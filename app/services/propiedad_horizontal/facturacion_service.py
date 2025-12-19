from sqlalchemy.orm import Session
from datetime import date
from typing import List, Dict, Any

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

def generar_facturacion_masiva(db: Session, empresa_id: int, fecha_factura: date, usuario_id: int, conceptos_ids: List[int] = None):
    # 1. Obtener Configuración
    config = db.query(PHConfiguracion).filter(PHConfiguracion.empresa_id == empresa_id).first()
    # Nota: Ya no es estrictamente obligatorio el global si los conceptos tienen el suyo
    
    # 2. Obtener Conceptos Activos
    query = db.query(PHConcepto).filter(PHConcepto.empresa_id == empresa_id, PHConcepto.activo == True)
    
    # Filtrar por IDs seleccionados si se proporcionan
    if conceptos_ids:
        query = query.filter(PHConcepto.id.in_(conceptos_ids))
        
    conceptos = query.all()
    if not conceptos:
        raise HTTPException(status_code=400, detail="No hay conceptos de cobro activos (o seleccionados) para facturar.")

    # 3. (Paso Omitido) Ya tenemos los IDs de cuenta directamente en el objeto Concepto.

    # 4. Obtener Unidades Activas con Propietario
    unidades = db.query(PHUnidad).filter(PHUnidad.empresa_id == empresa_id, PHUnidad.activo == True).all()
    
    resultados = {
        "generadas": 0,
        "errores": 0,
        "detalles": []
    }

    # 5. Agrupar Conceptos por Tipo de Documento
    # Esto permite que si un concepto usa Doc A y otro Doc B, se generen 2 facturas.
    # Si no tiene tipo_doc especifico, usar el Global.
    # NOTA: En el nuevo modelo PHConcepto ya NO existe tipo_documento_id en el concepto mismo (se removió en limpieza).
    # Asumimos que todos usan el Tipo Documento Global configurado en PHConfiguracion.
    # Si se quisiera re-introducir esa flexibilidad, habría que agregarlo al modelo.
    # Por ahora, usamos FACTURA DE VENTA GLOBAL.
    
    if not config or not config.tipo_documento_factura_id:
        # Fallback si no hay config, aunque debería. 
        # Podríamos buscar el primer TipoDocumento de venta... pero mejor exigir config.
        if not config or not config.tipo_documento_factura_id:
             raise HTTPException(status_code=400, detail="No se ha configurado el Tipo de Documento de Facturación en /ph/configuracion.")
             
    global_doc_id = config.tipo_documento_factura_id
    tipo_doc_obj = db.query(TipoDocumento).filter(TipoDocumento.id == global_doc_id).first()
    
    if not tipo_doc_obj:
         raise HTTPException(status_code=400, detail="El Tipo de Documento configurado no existe.")
         
    # --- LÓGICA DE GENERACIÓN DELTA (EVITAR DUPLICADOS) ---
    # 1. Obtener las unidades que YA tienen facturación válida para este periodo
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
    
    # 2. Filtrar la lista de unidades a procesar
    unidades_a_procesar = [u for u in unidades if u.id not in ids_ya_facturados]
    
    if len(unidades_a_procesar) == 0:
         return {
            "generadas": 0,
            "errores": 0,
            "detalles": [f"Todas las unidades ({len(unidades)}) ya tienen facturación para {periodo_str}."]
        }
        
    # Reemplazamos 'unidades' loop con la lista filtrada
    unidades = unidades_a_procesar

    # 6. Iterar Unidades y Generar Facturas (Una por unidad, agrupando todos los conceptos)

    # 6. Iterar Unidades y Generar Facturas (Una por unidad, agrupando todos los conceptos)
    for unidad in unidades:
        try:
            if not unidad.propietario_principal_id:
                resultados["errores"] += 1
                resultados["detalles"].append(f"Unidad {unidad.codigo}: Sin propietario asignado.")
                continue

            movimientos = []
            movimientos = []
            total_factura = 0

            # --- CÁLCULO DE INTERESES DE MORA ---
            if config.interes_mora_habilitado and config.interes_mora_mensual > 0:
                try:
                    from app.services.cartera import get_facturas_pendientes_por_tercero
                    from datetime import datetime
                    
                    # Obtener facturas pendientes del propietario, FILTRADAS POR LA UNIDAD ACTUAL
                    # Esto evita que se sumen deudas de otros apartamentos del mismo dueño
                    pendientes = get_facturas_pendientes_por_tercero(
                        db, 
                        unidad.propietario_principal_id, 
                        empresa_id, 
                        unidad_ph_id=unidad.id
                    )
                    
                    saldo_mora = 0
                    primer_dia_mes_factura = fecha_factura.replace(day=1)

                    for fact in pendientes:
                        # Convertir fecha vencimiento (string ISO) a date
                        # Si no tiene fecha vencimiento, usamos la fecha documento como fallback
                        fecha_ref_str = fact.get('fecha_vencimiento') or fact['fecha']
                        fecha_ref = datetime.fromisoformat(fecha_ref_str).date()
                        
                        # Si la fecha de VENCIMIENTO es anterior al primer día del mes actual, 
                        # significa que ya venció el mes pasado y debe pagar mora.
                        if fecha_ref < primer_dia_mes_factura:
                            saldo_mora += fact['saldo_pendiente']
                    
                    if saldo_mora > 0:
                        interes_valor = saldo_mora * (config.interes_mora_mensual / 100.0)
                        interes_valor = round(interes_valor, 2)
                        
                        if interes_valor > 0:
                            # 1. Credito Ingreso por Intereses
                            cta_int_ingreso = config.cuenta_ingreso_intereses_id
                            if not cta_int_ingreso:
                                # Fallback a warning o skip silencioso
                                print(f"Unidad {unidad.codigo} tiene mora pero no hay Cuenta Interés configurada.")
                            else:
                                movimientos.append(doc_schemas.MovimientoContableCreate(
                                    cuenta_id=cta_int_ingreso,
                                    concepto=f"Int. Mora {config.interes_mora_mensual}% sobre ${saldo_mora:,.0f}",
                                    debito=0,
                                    credito=interes_valor,
                                    centro_costo_id=None
                                ))

                                # 2. Debito Cartera (Usamos la global de PH si existe, o del tipo doc)
                                # Lógica similar a los conceptos normales
                                cta_int_cxc = config.cuenta_cartera_id
                                if not cta_int_cxc:
                                    cta_int_cxc = tipo_doc_obj.cuenta_debito_cxc_id
                                
                                if cta_int_cxc:
                                    movimientos.append(doc_schemas.MovimientoContableCreate(
                                        cuenta_id=cta_int_cxc,
                                        concepto=f"CxC Interés Mora - {unidad.codigo}",
                                        debito=interes_valor,
                                        credito=0
                                    ))
                                    total_factura += interes_valor
                except Exception as e_mora:
                    print(f"Error calculando mora unidad {unidad.codigo}: {str(e_mora)}")
            # ------------------------------------
            
            # Procesar todos los conceptos activos para esta unidad
            for concepto in conceptos:
                # --- LÓGICA DE MÓDULOS DE CONTRIBUCIÓN ---
                if concepto.modulos:
                    # El concepto tiene restricción por módulo.
                    # Verificar si la unidad pertenece a alguno de esos módulos.
                    unidad_modulos_ids = [m.id for m in unidad.modulos_contribucion]
                    concepto_modulos_ids = [m.id for m in concepto.modulos]
                    
                    # Intersección: Si no hay elementos comunes, la unidad NO paga este concepto.
                    if not set(unidad_modulos_ids) & set(concepto_modulos_ids):
                        continue
                # ----------------------------------------
                # Calcular Valor
                valor_linea = 0
                if concepto.usa_coeficiente and unidad.coeficiente: # Chequeo booleano correcto
                    valor_linea = float(concepto.valor_defecto) * float(unidad.coeficiente)
                else:
                    # Fijo
                    valor_linea = float(concepto.valor_defecto)

                # Redondear (opcional, pero buena practica en facturación)
                valor_linea = round(valor_linea, 2)
                
                if valor_linea > 0:
                    # 1. Credito (Ingreso)
                    cuenta_ingreso_id = concepto.cuenta_ingreso_id
                    if not cuenta_ingreso_id:
                        # Concepto mal configurado -> Skip o Warning
                        print(f"Concepto {concepto.nombre} sin cuenta ingreso.")
                        continue

                    movimientos.append(doc_schemas.MovimientoContableCreate(
                        cuenta_id=cuenta_ingreso_id,
                        concepto=f"{concepto.nombre} - {fecha_factura.strftime('%B %Y')}",
                        debito=0,
                        credito=valor_linea,
                        centro_costo_id=None 
                    ))
                    
                    # 2. Debito (Cartera) - ESPECIFICO DEL CONCEPTO
                    cuenta_cartera_id = concepto.cuenta_cxc_id
                    if not cuenta_cartera_id:
                         # Fallback a Config Global -> Fallback a Tipo Doc
                         cuenta_cartera_id = config.cuenta_cartera_id if config else None
                         if not cuenta_cartera_id:
                             cuenta_cartera_id = tipo_doc_obj.cuenta_debito_cxc_id
                    
                    if not cuenta_cartera_id:
                        raise Exception(f"Concepto {concepto.nombre} no tiene Cuenta Cartera definida y no hay default.")

                    movimientos.append(doc_schemas.MovimientoContableCreate(
                        cuenta_id=cuenta_cartera_id,
                        concepto=f"CxC {concepto.nombre} - {unidad.codigo}",
                        debito=valor_linea,
                        credito=0
                    ))
                    
                    total_factura += valor_linea

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
            if terc:
                # Usar solo campos que existen seguro en Tercero
                nombre_tercero = terc.razon_social or "Sin Nombre"

            # Obtener codigo de unidad directamente de la relacion
            unidad_info = uni.codigo if uni else (doc.observaciones or "")

            # Calcular total (suma de debitos)
            doc_total = sum([m.debito for m in doc.movimientos])
            
            # Intento de saldo, si no existe propiedad, fallback a total
            try:
                doc_saldo = doc.saldo_pendiente
            except:
                doc_saldo = doc_total # Asumimos pendiente si no hay logica de saldo

            lista_final.append({
                "id": doc.id,
                "consecutivo": doc.numero,
                "fecha": doc.fecha,
                "tercero_nombre": nombre_tercero,
                "unidad": unidad_info, 
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
    context = {
        "empresa": empresa,
        "periodo": periodo,
        "items": datos,
        "total_general": total_general
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
