from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from typing import List, Dict, Any
from decimal import Decimal

from app.models.propiedad_horizontal import PHUnidad, PHConfiguracion, PHConcepto
from app.models.documento import Documento, MovimientoContable
from app.models.tipo_documento import TipoDocumento
from app.models.plan_cuenta import PlanCuenta
from app.services import documento as documento_service
from app.schemas import documento as doc_schemas
from fastapi import HTTPException
from weasyprint import HTML
from jinja2 import Environment, select_autoescape
from app.models.empresa import Empresa
from app.services._templates_empaquetados import TEMPLATES_EMPAQUETADOS

def generar_facturacion_masiva(db: Session, empresa_id: int, fecha_factura: date, usuario_id: int, conceptos_ids: List[int] = None, configuracion_conceptos: List[Any] = None):
    # 1. Obtener Configuración
    print(f"--- SUPER DEBUG: Iniciando Facturacion Masiva. Empresa: {empresa_id}, Fecha: {fecha_factura}, Conceptos IDs Seleccionados: {conceptos_ids} ---")
    config = db.query(PHConfiguracion).filter(PHConfiguracion.empresa_id == empresa_id).first()
    
    # Procesar mapa de excepciones {concepto_id: {unidad_id, unidad_id...}}
    mapa_excepciones = {}
    if configuracion_conceptos:
        for conf in configuracion_conceptos:
            # conf puede ser objeto Pydantic o dict
            c_id = getattr(conf, 'concepto_id', conf.get('concepto_id') if isinstance(conf, dict) else None)
            u_ids = getattr(conf, 'unidades_ids', conf.get('unidades_ids') if isinstance(conf, dict) else [])
            if c_id and u_ids:
                mapa_excepciones[c_id] = set(u_ids)
                
    # 2. Obtener Conceptos Activos
    query = db.query(PHConcepto).filter(PHConcepto.empresa_id == empresa_id, PHConcepto.activo == True)
    
    # Filtrar por IDs seleccionados si se proporcionan
    if conceptos_ids:
        query = query.filter(PHConcepto.id.in_(conceptos_ids))
        
    conceptos = query.all()
    if not conceptos:
        raise HTTPException(status_code=400, detail="No hay conceptos de cobro activos (o seleccionados) para facturar.")

    # 4. Obtener Unidades Activas con Propietario
    unidades = db.query(PHUnidad).filter(PHUnidad.empresa_id == empresa_id, PHUnidad.activo == True).all()
    
    print(f"--- DEBUG: Conceptos encontrados: {len(conceptos)}")
    print(f"--- DEBUG: Unidades encontradas: {len(unidades)}")
    
    resultados = {
        "generadas": 0,
        "errores": 0,
        "detalles": []
    }

    if not config or not config.tipo_documento_factura_id:
             raise HTTPException(status_code=400, detail="No se ha configurado el Tipo de Documento de Facturación en /ph/configuracion.")
             
    global_doc_id = config.tipo_documento_factura_id
    tipo_doc_obj = db.query(TipoDocumento).filter(TipoDocumento.id == global_doc_id).first()
    
    if not tipo_doc_obj:
         raise HTTPException(status_code=400, detail="El Tipo de Documento configurado no existe.")
         
    # --- LÓGICA DE GENERACIÓN DELTA (EVITAR DUPLICADOS) ---
    from sqlalchemy import func as sa_func
    periodo_str = fecha_factura.strftime('%Y-%m')
    
    unidades_ya_facturadas = db.query(Documento.unidad_ph_id)\
        .filter(
            Documento.empresa_id == empresa_id,
            Documento.tipo_documento_id == global_doc_id,
            sa_func.to_char(Documento.fecha, 'YYYY-MM') == periodo_str,
            Documento.estado.in_(['ACTIVO', 'PROCESADO'])
        ).all()
        
    ids_ya_facturados = {u.unidad_ph_id for u in unidades_ya_facturadas if u.unidad_ph_id}
    
    # NUEVO: Si estamos usando excepciones, permitimos "refacturar" si es un concepto diferente (Manejo a futuro)
    # Por ahora, mantenemos la regla de "Una factura por mes".
    # Pero el usuario podría querer facturar Multas aparte.
    # SI hay mapa de excepciones, relajamos la restricción de "ya facturado"? 
    # NO, por ahora agregaremos los items a la factura si no existe, o crearemos nota separada?
    # MEJOR: En este MVP, si ya tiene factura, NO generamos otra. El usuario deberá borrarla y regenerar 
    # o hacer factura manual. Este es el trade-off de la "Facturación Masiva".
    
    unidades_a_procesar = [u for u in unidades if u.id not in ids_ya_facturados]
    
    if len(unidades_a_procesar) == 0:
         return {
            "generadas": 0,
            "errores": 0,
            "detalles": [f"Todas las unidades ({len(unidades)}) ya tienen facturación para {periodo_str}."]
        }
        
    unidades = unidades_a_procesar

    # 6. Iterar Unidades y Generar Facturas
    for unidad in unidades:
        try:
            if not unidad.propietario_principal_id:
                resultados["errores"] += 1
                resultados["detalles"].append(f"Unidad {unidad.codigo}: Sin propietario asignado.")
                continue

            movimientos = []
            total_factura = 0

            pagos_tardios_procesados = False # Control para no duplicar si hay multiples conceptos de interes

            # Procesar todos los conceptos activos para esta unidad
            for concepto in conceptos:
                # --- NUEVO FILTRO DE EXCEPCIONES ---
                # Si el concepto está en el mapa de excepciones, verificar si esta unidad está en la lista permitida
                if concepto.id in mapa_excepciones:
                    if unidad.id not in mapa_excepciones[concepto.id]:
                        continue # Este concepto ES una excepción y esta unidad NO está en la lista.
                # -----------------------------------

                valor_linea = 0
                es_mora = False
                saldo_mora = 0

                # --- LÓGICA DE MÓDULOS DE CONTRIBUCIÓN ---
                if concepto.modulos and concepto.id not in mapa_excepciones:
                    # El concepto tiene restricción por módulo (y no fue forzado por excepción manual)
                    unidad_modulos_ids = [m.id for m in unidad.modulos_contribucion]
                    concepto_modulos_ids = [m.id for m in concepto.modulos]
                    if not set(unidad_modulos_ids) & set(concepto_modulos_ids):
                        continue
                # ----------------------------------------

                # --- CÁLCULO DE VALOR (SMART LOGIC) ---
                if concepto.es_interes:
                    print(f"--- DEBUG: Entrando a logica interes para concepto {concepto.nombre} (Unidad {unidad.codigo}) ---")
                    
                    # --- LÓGICA DE INTERÉS DIFERIDO DISCRIMINADO (Pagos Tardios del Mes Anterior) ---
                    # MOVIDO AL INICIO PARA QUE APAREZCA PRIMERO EN EL DETALLE
                    if not pagos_tardios_procesados and float(config.interes_mora_mensual) > 0:
                        try:
                            # 1. Calcular fechas del mes anterior
                            # Ejemplo: fecha_factura 2026-02-01 -> Mes Anterior: Enero 2026 (01 al 31)
                            # Restamos 1 dia al 1ro del mes actual para obtener ultimo del anterior
                            ultimo_dia_mes_ant = fecha_factura.replace(day=1) - timedelta(days=1)
                            primer_dia_mes_ant = ultimo_dia_mes_ant.replace(day=1)
                            
                            # 2. Buscar Recibos en ese rango
                            if config.tipo_documento_recibo_id and config.dia_limite_pago:
                                recibos_tardios = db.query(Documento).filter(
                                    Documento.empresa_id == empresa_id,
                                    Documento.unidad_ph_id == unidad.id,
                                    Documento.tipo_documento_id == config.tipo_documento_recibo_id,
                                    Documento.fecha >= primer_dia_mes_ant,
                                    Documento.fecha <= ultimo_dia_mes_ant,
                                    Documento.estado == 'ACTIVO'
                                ).order_by(Documento.fecha.asc()).all() # Ordenar por fecha para agrupar

                                for recibo in recibos_tardios:
                                    if recibo.fecha.day > config.dia_limite_pago:
                                        # 3. Calcular Base (Total abonado a credito)
                                        valor_base_pago = sum([m.credito for m in recibo.movimientos if m.credito > 0])
                                        
                                        if valor_base_pago > 0:
                                            tasa_decimal = Decimal(str(config.interes_mora_mensual)) / Decimal(100)
                                            interes_pago = valor_base_pago * tasa_decimal
                                            interes_pago = round(interes_pago, 2)
                                            
                                            if interes_pago > 0:
                                                # Cuentas
                                                cta_ing = concepto.cuenta_ingreso_id
                                                cta_cxc = concepto.cuenta_cxc_id or config.cuenta_cartera_id or tipo_doc_obj.cuenta_debito_cxc_id
                                                
                                                if cta_ing and cta_cxc:
                                                    # Credito Ingreso
                                                    movimientos.append(doc_schemas.MovimientoContableCreate(
                                                        cuenta_id=cta_ing,
                                                        concepto=f"Interés Mora (Pago tardío {recibo.fecha}: {config.interes_mora_mensual}% sobre ${valor_base_pago:,.0f})",
                                                        debito=0,
                                                        credito=interes_pago,
                                                        centro_costo_id=None
                                                    ))
                                                    # Debito Cartera
                                                    movimientos.append(doc_schemas.MovimientoContableCreate(
                                                        cuenta_id=cta_cxc,
                                                        concepto=f"CxC Interés Mora (Pago tardío {recibo.fecha}: {config.interes_mora_mensual}% sobre ${valor_base_pago:,.0f}) - {unidad.codigo}",
                                                        debito=interes_pago,
                                                        credito=0
                                                    ))
                                                    total_factura += float(interes_pago)
                                                    
                            pagos_tardios_procesados = True
                            
                        except Exception as e_tardios:
                            print(f"Error procesando pagos tardios unidad {unidad.codigo}: {str(e_tardios)}")

                    # Lógica de Interés de Mora (Saldo Actual)
                    # Lógica de Interés de Mora
                    es_mora = True
                    if config.interes_mora_mensual > 0:
                        try:
                            # Importuración diferida para evitar ciclos
                            from app.services.cartera import get_facturas_pendientes_por_tercero
                            from datetime import datetime
                            
                            pendientes = get_facturas_pendientes_por_tercero(
                                db, 
                                unidad.propietario_principal_id, 
                                empresa_id, 
                                unidad_ph_id=unidad.id
                            )
                            
                            print(f"DEBUG: Pendientes encontradas: {len(pendientes)}")
                            
                            # --- CORRECCION DE VARIABLES ---
                            saldo_mora = 0
                            primer_dia_mes_factura = fecha_factura.replace(day=1)
                            print(f"DEBUG: Fecha ref factura: {primer_dia_mes_factura}")

                            # --- ANTI-ANATOCISMO: Identificar cuentas de interes ---
                            cuentas_interes_ids = [c.cuenta_ingreso_id for c in conceptos if c.es_interes and c.cuenta_ingreso_id]
                            print(f"DEBUG: Cuentas de Interes a excluir de la base: {cuentas_interes_ids}")
                            from app.models.documento import MovimientoContable
                            from sqlalchemy import func

                            for fact in pendientes:
                                fecha_ref_str = fact.get('fecha_vencimiento') or fact['fecha']
                                try:
                                    fecha_ref = datetime.fromisoformat(fecha_ref_str).date()
                                except:
                                    fecha_ref = fact.get('fecha_vencimiento') or fact['fecha']
                                
                                # Solo interesa si est vencida
                                if fecha_ref < primer_dia_mes_factura:
                                    saldo_factura = fact['saldo_pendiente']
                                    
                                    # Calcular componente de interes en esta factura (Anatocismo)
                                    interes_acumulado_en_factura = 0
                                    if cuentas_interes_ids:
                                        val_dec = db.query(func.sum(MovimientoContable.credito)).filter(
                                            MovimientoContable.documento_id == fact['id'],
                                            MovimientoContable.cuenta_id.in_(cuentas_interes_ids)
                                        ).scalar() or 0
                                        interes_acumulado_en_factura = float(val_dec)
                                    
                                    base_depurada = max(0, saldo_factura - interes_acumulado_en_factura)
                                    
                                    print(f"DEBUG: Factura {fact['numero']} | Saldo Total: {saldo_factura} | Interes Incluido: {interes_acumulado_en_factura} | Base Depurada: {base_depurada}")
                                    
                                    saldo_mora += base_depurada
                            
                            print(f"DEBUG: Saldo Mora Calculado: {saldo_mora}")

                            if saldo_mora > 0:
                                interes_valor = saldo_mora * (config.interes_mora_mensual / 100.0)
                                valor_linea = round(interes_valor, 2)
                                print(f"DEBUG: Interes final: {valor_linea}")
                        except Exception as e_mora:
                            print(f"Error calculando mora unidad {unidad.codigo}: {str(e_mora)}")
                            valor_linea = 0
                    else:
                        print("DEBUG: Tasa interes es 0 o nula")
                
                else:
                    # Lógica Estándar (Fijo o Coeficiente)
                    if concepto.usa_coeficiente and unidad.coeficiente:
                        valor_linea = float(concepto.valor_defecto) * float(unidad.coeficiente)
                    else:
                        valor_linea = float(concepto.valor_defecto)
                
                # Redondear
                valor_linea = round(valor_linea, 2)
                
                if valor_linea > 0:
                    # 1. Credito (Ingreso)
                    cuenta_ingreso_id = concepto.cuenta_ingreso_id
                    if not cuenta_ingreso_id:
                        print(f"Concepto {concepto.nombre} sin cuenta ingreso.")
                        continue
                    
                    nombre_concepto_mov = f"{concepto.nombre} - {fecha_factura.strftime('%B %Y')}"
                    detalle_mora_str = ""
                    if es_mora:
                        base_fmt = f"{saldo_mora:,.0f}".replace(",", ".")
                        detalle_mora_str = f"({config.interes_mora_mensual}% - {base_fmt})"
                        nombre_concepto_mov = f"{concepto.nombre} {detalle_mora_str}"

                    movimientos.append(doc_schemas.MovimientoContableCreate(
                        cuenta_id=cuenta_ingreso_id,
                        concepto=nombre_concepto_mov,
                        debito=0,
                        credito=valor_linea,
                        centro_costo_id=None 
                    ))
                    
                    # 2. Debito (Cartera)
                    cuenta_cartera_id = concepto.cuenta_cxc_id
                    if not cuenta_cartera_id:
                         cuenta_cartera_id = config.cuenta_cartera_id if config else None
                         if not cuenta_cartera_id:
                             cuenta_cartera_id = tipo_doc_obj.cuenta_debito_cxc_id
                    
                    if not cuenta_cartera_id:
                        # Si es mora y no tiene cxc, intentamos usar la global
                        raise Exception(f"Concepto {concepto.nombre} no tiene Cuenta Cartera definida.")

                    movimientos.append(doc_schemas.MovimientoContableCreate(
                        cuenta_id=cuenta_cartera_id,
                        concepto=f"CxC {concepto.nombre} {detalle_mora_str} - {unidad.codigo}".replace("  ", " "),
                        debito=valor_linea,
                        credito=0
                    ))
                    
                    total_factura += valor_linea



            # --- ORDENAMIENTO DE DETALLES (SOLICITUD USUARIO) ---
            # 1. Fecha (Ascendente)
            # 2. Tipo (Pago Tardío -> Interés Mora Saldo -> Otros)
            if movimientos:
                def get_sort_key(mov):
                    desc = mov.concepto
                    # Prioridad Default
                    prio = 3 
                    fecha_sort = fecha_factura
                    
                    if "Pago tardío" in desc:
                        prio = 1
                        try:
                            # Extract YYYY-MM-DD
                            import re
                            match = re.search(r'\d{4}-\d{2}-\d{2}', desc)
                            if match:
                                from datetime import datetime
                                fecha_sort = datetime.strptime(match.group(), '%Y-%m-%d').date()
                        except:
                            pass
                    elif "Interés Mora" in desc or "Interes Mora" in desc:
                        prio = 2
                    
                    return (fecha_sort, prio, desc)
                
                movimientos.sort(key=get_sort_key)

            if total_factura > 0:
                # Crear Documento
                obs = f"Factura Expensas - PH Unidad {unidad.codigo}"
                if config and config.mensaje_factura:
                     obs += f" | {config.mensaje_factura}"

                doc_create = doc_schemas.DocumentoCreate(
                    empresa_id=empresa_id,
                    tipo_documento_id=global_doc_id, # Usamos el global
                    numero=0, 
                    fecha=fecha_factura,
                    fecha_vencimiento=fecha_factura, 
                    beneficiario_id=unidad.propietario_principal_id,
                    observaciones=obs,
                    movimientos=movimientos,
                    unidad_ph_id=unidad.id
                )
                
                new_doc = documento_service.create_documento(db, doc_create, user_id=usuario_id)
                resultados["generadas"] += 1
                resultados["detalles"].append(f"Unidad {unidad.codigo}: Doc {new_doc.numero} por ${total_factura:,.0f}")

        except Exception as e:
            resultados["errores"] += 1
            resultados["detalles"].append(f"Unidad {unidad.codigo}: Error - {str(e)}")
            continue

        except Exception as e:
            resultados["errores"] += 1
            resultados["detalles"].append(f"Unidad {unidad.codigo}: Error - {str(e)}")
            continue

    return resultados

def get_historial_facturacion(db: Session, empresa_id: int):
    """
    Agrupa las facturas de PH por mes para mostrar historial.
    """
    from sqlalchemy import func, desc
    
    config = db.query(PHConfiguracion).filter(PHConfiguracion.empresa_id == empresa_id).first()
    if not config:
        return []

    tipo_factura_id = config.tipo_documento_factura_id
    if not tipo_factura_id:
        return []

    # Estrategia 2: Query de periodos distintos
    periodos = db.query(Documento.fecha).filter(
        Documento.empresa_id == empresa_id, 
        Documento.tipo_documento_id == tipo_factura_id,
        Documento.estado.in_(['ACTIVO', 'PROCESADO'])
    ).distinct().all()
    
    # Normalizar a meses unicos
    meses_set = set()
    for p in periodos:
        meses_set.add(p.fecha.strftime('%Y-%m'))
        
    historial = []
    
    # Calcular totales por mes
    for mes in sorted(list(meses_set), reverse=True):
        # Buscar docs de este mes
        docs = db.query(Documento).filter(
            Documento.empresa_id == empresa_id,
            Documento.tipo_documento_id == tipo_factura_id,
            func.to_char(Documento.fecha, 'YYYY-MM') == mes,
            Documento.estado.in_(['ACTIVO', 'PROCESADO'])
        ).all()
        
        # Calcular total DEBITO (Total facturado) - Buscando Movimientos Ingreso o CXC
        total_periodo = 0
        from app.services.cartera import get_cuentas_especiales_ids
        ids_cxc = get_cuentas_especiales_ids(db, empresa_id, 'cxc')
        
        for d in docs:
            # Sumar debito de cuentas cxc
            for mov in d.movimientos:
                if mov.cuenta_id in ids_cxc:
                    total_periodo += mov.debito

        historial.append({
            "periodo": mes,
            "cantidad": len(docs),
            "total": total_periodo
        })
        
    return historial

def eliminar_facturacion_masiva(db: Session, empresa_id: int, periodo: str, usuario_id: int):
    """
    Elimina todas las facturas de un periodo (YYYY-MM).
    """
    config = db.query(PHConfiguracion).filter(PHConfiguracion.empresa_id == empresa_id).first()
    if not config or not config.tipo_documento_factura_id:
        raise Exception("Configuracion PH invalida.")
        
    from sqlalchemy import func
    # Buscar documentos
    docs = db.query(Documento).filter(
        Documento.empresa_id == empresa_id,
        Documento.tipo_documento_id == config.tipo_documento_factura_id,
        func.to_char(Documento.fecha, 'YYYY-MM') == periodo,
        Documento.estado.in_(['ACTIVO', 'PROCESADO']) # Solo activos
    ).all()
    
    if not docs:
        return {"mensaje": "No se encontraron facturas para este periodo.", "eliminadas": 0}
        
    count = 0
    from app.services.documento import eliminar_documento
    
    for doc in docs:
        eliminar_documento(db, doc.id, empresa_id, usuario_id, "Eliminacion Masiva Facturacion PH")
        count += 1
        
    db.commit()
    return {"mensaje": "Facturacion eliminada correctamente.", "eliminadas": count}

def check_facturacion_periodo(db: Session, empresa_id: int, fecha: date):
    """
    Verifica si ya existen facturas de PH para el mes indicado.
    Retorna la cantidad encontrada.
    """
    from sqlalchemy import func
    
    config = db.query(PHConfiguracion).filter(PHConfiguracion.empresa_id == empresa_id).first()
    if not config or not config.tipo_documento_factura_id:
        return 0 # Si no hay config, asumimos 0 (el generador fallará despues igual)
        
    tipo_doc_id = config.tipo_documento_factura_id
    periodo_str = fecha.strftime('%Y-%m')
    
    count = db.query(Documento).filter(
        Documento.empresa_id == empresa_id,
        Documento.tipo_documento_id == tipo_doc_id,
        func.to_char(Documento.fecha, 'YYYY-MM') == periodo_str,
        Documento.estado.in_(['ACTIVO', 'PROCESADO'])
    ).count()
    
    return count

def get_detalle_facturacion(db: Session, empresa_id: int, periodo: str):
    """
    Retorna el detalle de las facturas generadas para un periodo (YYYY-MM).
    """
    try:
        from sqlalchemy import func
        from app.models.tercero import Tercero
        from app.models.propiedad_horizontal.unidad import PHUnidad
        
        config = db.query(PHConfiguracion).filter(PHConfiguracion.empresa_id == empresa_id).first()
        if not config or not config.tipo_documento_factura_id:
            return []
            
        # Join explicito seleccionando Documento, Tercero y Unidad
        resultados_query = db.query(Documento, Tercero, PHUnidad)\
            .outerjoin(Tercero, Documento.beneficiario_id == Tercero.id)\
            .outerjoin(PHUnidad, Documento.unidad_ph_id == PHUnidad.id)\
            .filter(
                Documento.empresa_id == empresa_id,
                Documento.tipo_documento_id == config.tipo_documento_factura_id,
                func.to_char(Documento.fecha, 'YYYY-MM') == periodo,
                Documento.estado.in_(['ACTIVO', 'PROCESADO'])
            ).order_by(Documento.numero.desc()).all()
        
        lista_final = []
        for doc, terc, uni in resultados_query:
            nombre_tercero = "Desconocido"
            nit_tercero = ""
            if terc:
                # Usar solo campos que existen seguro en Tercero
                nombre_tercero = terc.razon_social or "Sin Nombre"
                nit_tercero = terc.nit

            # Obtener codigo de unidad directamente de la relacion
            unidad_info = uni.codigo if uni else (doc.observaciones or "")

            # Calcular total (suma de debitos)
            doc_total = sum([m.debito for m in doc.movimientos])
            
            # Intento de saldo, si no existe propiedad, fallback a total
            try:
                doc_saldo = doc.saldo_pendiente
            except:
                doc_saldo = doc_total # Asumimos pendiente si no hay logica de saldo

            # Obtener sub-items (conceptos cobrados = movimientos credito)
            sub_items = []
            for m in doc.movimientos:
                if m.credito > 0:
                    sub_items.append({
                        "nombre": m.concepto,
                        "valor": m.credito
                    })

            lista_final.append({
                "id": doc.id,
                "consecutivo": doc.numero,
                "fecha": doc.fecha,
                "tercero_nombre": nombre_tercero,
                "tercero_nit": nit_tercero,
                "detalle": unidad_info, # Renamed to 'detalle' to match template usage
                "sub_items": sub_items, # Nueva lista de conceptos
                "total": doc_total,
                "saldo": doc_saldo,
                "estado": doc.estado
            })
            
        return lista_final
    except Exception as e:
        print(f"ERROR CRITICO en get_detalle_facturacion: {str(e)}")
        # import traceback
        # traceback.print_exc()
        raise e

def generar_pdf_detalle_facturacion(db: Session, empresa_id: int, periodo: str):
    """
    Genera el PDF del detalle de facturación para un periodo.
    """
    # 1. Obtener datos usando la función existente
    datos = get_detalle_facturacion(db, empresa_id, periodo)
    
    if not datos:
        # Retornar PDF con mensaje de vacio
        html_string = "<html><body><h1>Detalle de Facturación</h1><p>No se encontraron facturas para el periodo seleccionado.</p></body></html>"
        return HTML(string=html_string).write_pdf()
        
    # 2. Obtener Empresa
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    
    # 3. Calcular Total General
    total_general = sum(item['total'] for item in datos)
    
    # 4. Preparar Contexto
    
    # Definir labels para PH (Hardcoded por ahora ya que es módulo PH)
    labels = {
        "entidad_secundaria_short": "Unidad"
    }

    context = {
        "empresa": empresa,
        "periodo": periodo,
        "items": datos,
        "total_periodo": total_general, # FIX: Renamed key to match template
        "labels": labels
    }
    
    # 5. Renderizar Template
    template_name = 'reports/detalle_facturacion_report.html'
    if template_name not in TEMPLATES_EMPAQUETADOS:
        raise HTTPException(status_code=500, detail="Plantilla de reporte no encontrada.")
        
    env = Environment(loader=None, autoescape=select_autoescape(['html', 'xml']))
    template = env.from_string(TEMPLATES_EMPAQUETADOS[template_name])
    html_content = template.render(context)
    
    # 6. Generar PDF
    return HTML(string=html_content).write_pdf()

def recalcular_intereses_posteriores(db: Session, empresa_id: int, unidad_id: int, fecha_corte: date, usuario_id: int):
    """
    Recalcula los intereses de mora de todas las facturas posteriores a una fecha dada.
    Útil cuando se edita un pago retroactivo y se quieren corregir las liquidaciones siguientes.
    """
    from datetime import datetime, date
    from sqlalchemy import func
    
    config = db.query(PHConfiguracion).filter(PHConfiguracion.empresa_id == empresa_id).first()
    if not config or not config.tipo_documento_factura_id:
        raise Exception("Configuración PH no encontrada")
        
    global_doc_id = config.tipo_documento_factura_id
    
    # 1. Buscar facturas posteriores a la fecha de corte
    facturas_futuras = db.query(Documento).filter(
        Documento.empresa_id == empresa_id,
        Documento.unidad_ph_id == unidad_id,
        Documento.tipo_documento_id == global_doc_id, # Solo facturas PH
        Documento.fecha > fecha_corte,
        Documento.estado.in_(['ACTIVO']) # No tocar anuladas ni procesadas si ya se cerraron (procesadas = asiento generado?) -> Asumimos ACTIVO
    ).order_by(Documento.fecha).all()
    
    log_cambios = []
    
    for factura in facturas_futuras:
        # Calcular fecha referencia (1er dia del mes de esa factura)
        # La logica original usa fecha_factura.replace(day=1) para saber que venció ANTES de ese mes.
        primer_dia_mes_factura = factura.fecha.replace(day=1)
        
        # 2. Calcular Saldo Mora "Virtual" a esa fecha
        from app.services.cartera import get_facturas_pendientes_por_tercero
        
        # IMPORTANTE: Usamos fecha_corte = factura.fecha para ver la foto EXACTA de ese momento
        pendientes = get_facturas_pendientes_por_tercero(
            db, 
            factura.beneficiario_id, 
            empresa_id, 
            unidad_ph_id=unidad_id,
            fecha_corte=factura.fecha # <<<< LA CLAVE DE LA INTELIGENCIA
        )
        
        # Calcular nueva base depurada
        saldo_mora_nuevo = 0
        from app.services.propiedad_horizontal.facturacion_service import generar_facturacion_masiva # Circular ref warning? No, same module function call is fine? No, defined below.
        # Repetimos logica de depuracion (anti-anatocismo)
        
        # Obtener conceptos de interes para excluir sus cuentas
        cuentas_interes_ids = db.query(PHConcepto.cuenta_ingreso_id).filter(
            PHConcepto.empresa_id == empresa_id,
            PHConcepto.es_interes == True,
            PHConcepto.activo == True
        ).all()
        cuentas_interes_ids = [c[0] for c in cuentas_interes_ids if c[0]]

        for fact_p in pendientes:
            # Check si vencio antes del mes de la factura TARGET
            try:
                fecha_ref = date.fromisoformat(fact_p['fecha'])
            except:
                fecha_ref = fact_p['fecha']
                
            if fecha_ref < primer_dia_mes_factura:
                # Es mora
                saldo_item = fact_p['saldo_pendiente']
                
                # Depurar interes previo
                interes_previo = 0
                if cuentas_interes_ids:
                    val_dec = db.query(func.sum(MovimientoContable.credito)).filter(
                        MovimientoContable.documento_id == fact_p['id'],
                        MovimientoContable.cuenta_id.in_(cuentas_interes_ids)
                    ).scalar() or 0
                    interes_previo = float(val_dec)
                    
                base_depurada = max(0, saldo_item - interes_previo)
                saldo_mora_nuevo += base_depurada

        # 3. ELIMINAR INTERESES EXISTENTES (Para regenerarlos limpiamente)
        # Identificar movimientos de interes actuales
        movs_interes_eliminar = []
        movs_cxc_eliminar = []
        
        for mov in factura.movimientos:
            if mov.credito > 0 and mov.cuenta_id in cuentas_interes_ids:
                movs_interes_eliminar.append(mov)
                
        # Buscar sus contrapartidas (CxC)
        # Estrategia: Buscar movimientos DEBITO creados en la misma transaccion/fecha o con concepto similar
        # Simplificación: Si el concepto contiene "Interés" o "Mora" y es débito, lo marcamos para revisión
        # Mejor: Usamos el ID de la transacción? No tenemos transaction_id explícito agrupador aqui facil.
        # Usamos heuristica de concepto.
        for mov in factura.movimientos:
            if mov.debito > 0 and ("Interés" in mov.concepto or "Interes" in mov.concepto or "Mora" in mov.concepto):
                 movs_cxc_eliminar.append(mov)

        # Ejecutar Eliminación (Marcándolos para borrar o borrándolos de la sesión)
        for m in movs_interes_eliminar:
            db.delete(m)
        for m in movs_cxc_eliminar:
            db.delete(m)
            
        # 4. CALCULAR NUEVOS INTERESES (Lógica Unificada)
        nuevos_movimientos = []
        total_nuevos_intereses = 0
        
        # A. INTERÉS POR PAGOS TARDÍOS (Del Mes Anterior)
        # Mes anterior relativo a la factura (factura.fecha es 1er dia del mes actual)
        # Ejem: Factura Abril (01/04). Mes Anterior = Marzo.
        ultimo_dia_mes_ant = factura.fecha.replace(day=1) - timedelta(days=1)
        primer_dia_mes_ant = ultimo_dia_mes_ant.replace(day=1)
            
        if config.tipo_documento_recibo_id and config.dia_limite_pago and config.interes_mora_mensual > 0:
             recibos_tardios = db.query(Documento).filter(
                Documento.empresa_id == empresa_id,
                Documento.unidad_ph_id == unidad_id,
                Documento.tipo_documento_id == config.tipo_documento_recibo_id,
                Documento.fecha >= primer_dia_mes_ant,
                Documento.fecha <= ultimo_dia_mes_ant,
                Documento.estado == 'ACTIVO'
            ).all()
             
             for recibo in recibos_tardios:
                if recibo.fecha.day > config.dia_limite_pago:
                    valor_base_pago = sum([m.credito for m in recibo.movimientos if m.credito > 0])
                    if valor_base_pago > 0:
                        interes_pago = round(float(valor_base_pago) * (float(config.interes_mora_mensual)/100.0), 2)
                        if interes_pago > 0:
                            # Añadir Movimientos
                            # Necesitamos cuentas. Usamos la primera cuenta de interés encontrada en config/conceptos o fallback
                            # Esto es una limitación: No sabemos EXACTO cual concepto usar si hay varios de interés.
                            # Usaremos el PRIMER concepto marcado como 'es_interes' de la empresa.
                            # O mejor, buscamos el concepto genérico de mora.
                            
                            # Fallback accounts
                            cta_ingreso = None
                            cta_cxc = None
                            
                            concepto_mora = db.query(PHConcepto).filter(PHConcepto.empresa_id==empresa_id, PHConcepto.es_interes==True).first()
                            if concepto_mora:
                                cta_ingreso = concepto_mora.cuenta_ingreso_id
                                cta_cxc = concepto_mora.cuenta_cxc_id
                            
                            if not cta_cxc: cta_cxc = config.cuenta_cartera_id
                            
                            if cta_ingreso and cta_cxc:
                                nuevos_movimientos.append({
                                    "cuenta_id": cta_ingreso,
                                    "concepto": f"Interés Mora (Pago tardío {recibo.fecha}: {config.interes_mora_mensual}% sobre ${valor_base_pago:,.0f})",
                                    "debito": 0,
                                    "credito": interes_pago
                                })
                                nuevos_movimientos.append({
                                    "cuenta_id": cta_cxc,
                                    "concepto": f"CxC Interés Mora (Pago tardío {recibo.fecha}: {config.interes_mora_mensual}% sobre ${valor_base_pago:,.0f})",
                                    "debito": interes_pago,
                                    "credito": 0,
                                    "es_cxc": True
                                })
                                total_nuevos_intereses += interes_pago

        # B. INTERÉS SOBRE SALDO (Saldo Mora Nuevo)
        if saldo_mora_nuevo > 0 and config.interes_mora_mensual > 0:
            nuevo_valor_interes = round(saldo_mora_nuevo * (config.interes_mora_mensual / 100.0), 2)
            if nuevo_valor_interes > 0:
                 # Cuentas
                 cta_ingreso = None
                 cta_cxc = None
                 concepto_mora = db.query(PHConcepto).filter(PHConcepto.empresa_id==empresa_id, PHConcepto.es_interes==True).first()
                 if concepto_mora:
                    cta_ingreso = concepto_mora.cuenta_ingreso_id
                    cta_cxc = concepto_mora.cuenta_cxc_id
                 if not cta_cxc: cta_cxc = config.cuenta_cartera_id
                 
                 base_fmt = f"{saldo_mora_nuevo:,.0f}".replace(",", ".")
                 # Nombre Concepto
                 nom_concepto = concepto_mora.nombre if concepto_mora else "Intereses Mora"
                 
                 if cta_ingreso and cta_cxc:
                    nuevos_movimientos.append({
                        "cuenta_id": cta_ingreso,
                        "concepto": f"{nom_concepto} ({config.interes_mora_mensual}% - {base_fmt})",
                        "debito": 0,
                        "credito": nuevo_valor_interes
                    })
                    nuevos_movimientos.append({
                         "cuenta_id": cta_cxc,
                         "concepto": f"CxC {nom_concepto} ({config.interes_mora_mensual}% - {base_fmt})",
                         "debito": nuevo_valor_interes,
                         "credito": 0,
                         "es_cxc": True
                    })
                    total_nuevos_intereses += nuevo_valor_interes

        # 5. INSERTAR NUEVOS MOVIMIENTOS
        if nuevos_movimientos:
            for mov_data in nuevos_movimientos:
                es_cxc = mov_data.pop("es_cxc", False)
                nuevo_mov = MovimientoContable(**mov_data, documento_id=factura.id)
                db.add(nuevo_mov)
                
            log_cambios.append(f"Factura {factura.numero}: Recalculado. Total Intereses: {total_nuevos_intereses}")
        else:
            log_cambios.append(f"Factura {factura.numero}: Recalculado. Sin intereses.")
        
    db.commit()
    return {"status": "ok", "actualizadas": len(log_cambios), "detalles": log_cambios}
