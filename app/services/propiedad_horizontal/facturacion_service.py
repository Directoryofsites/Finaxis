from sqlalchemy.orm import Session, joinedload
from datetime import date, datetime, timedelta
from typing import List, Dict, Any
from decimal import Decimal
from app.utils.sorting import natural_sort_key

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
    from app.services.propiedad_horizontal import configuracion_service
    config = configuracion_service.get_configuracion(db, empresa_id)
    
    # Procesar mapa de excepciones {concepto_id: {unidad_id, unidad_id...}}
    mapa_excepciones = {}
    if configuracion_conceptos:
        for conf in configuracion_conceptos:
            # conf puede ser objeto Pydantic o dict
            c_id = getattr(conf, 'concepto_id', conf.get('concepto_id') if isinstance(conf, dict) else None)
            u_ids = getattr(conf, 'unidades_ids', conf.get('unidades_ids') if isinstance(conf, dict) else [])
            if c_id and u_ids:
                mapa_excepciones[c_id] = set(u_ids)
                
    # 2. Obtener Conceptos Activos (con sus módulos cargados)
    query = db.query(PHConcepto)\
        .options(joinedload(PHConcepto.modulos))\
        .filter(PHConcepto.empresa_id == empresa_id, PHConcepto.activo == True)
    
    # Filtrar por IDs seleccionados si se proporcionan
    if conceptos_ids:
        query = query.filter(PHConcepto.id.in_(conceptos_ids))
        
    conceptos = query.all()
    if not conceptos:
        raise HTTPException(status_code=400, detail="No hay conceptos de cobro activos (o seleccionados) para facturar.")

    # 4. Obtener Unidades Activas con Propietario y sus Módulos de Contribución cargados
    unidades = db.query(PHUnidad)\
        .options(joinedload(PHUnidad.modulos_contribucion))\
        .filter(PHUnidad.empresa_id == empresa_id, PHUnidad.activo == True).all()
    
    # Pre-cargar torres de los módulos para evitar lazy loading en el bucle
    # Acceder a .torres en cada módulo dentro de la sesión activa
    for concepto in conceptos:
        for modulo in concepto.modulos:
            _ = modulo.torres  # Forzar la carga mientras la sesión está abierta
    
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
    
    # NUEVO: Buscar Tipo de Documento para Cruces
    tipo_nc = None
    if config and config.tipo_documento_cruce_id:
        tipo_nc = db.query(TipoDocumento).filter(TipoDocumento.id == config.tipo_documento_cruce_id).first()
    if not tipo_nc:
        tipo_nc = db.query(TipoDocumento).filter(
            TipoDocumento.empresa_id == empresa_id,
            TipoDocumento.funcion_especial == 'PH_CRUCE_ANTICIPO'
        ).first()
    if not tipo_nc:
        tipo_nc = db.query(TipoDocumento).filter(
            TipoDocumento.empresa_id == empresa_id,
            TipoDocumento.codigo == 'NC'
        ).first()
    
    # Identificar unidades con excepciones (whitelisted)
    unidades_con_excepciones = set()
    for u_set in mapa_excepciones.values():
        unidades_con_excepciones.update(u_set)
        
    unidades_a_procesar = []
    for u in unidades:
        # Aceptar si NO está facturada O SÍ está facturada pero tiene excepción (Delta)
        if u.id not in ids_ya_facturados or u.id in unidades_con_excepciones:
            unidades_a_procesar.append(u)
    
    unidades = unidades_a_procesar

    # --- PRECARGA MASIVA DE DATOS (ANTI N+1) ---
    print(f"--- BATCH OPTIMIZATION: Iniciando precarga masiva para {len(unidades)} unidades ---")
    from app.services.cartera import get_cuentas_especiales_ids
    ids_cxc = get_cuentas_especiales_ids(db, empresa_id, 'cxc')
    cuentas_interes_ids = [c.cuenta_ingreso_id for c in conceptos if c.es_interes and c.cuenta_ingreso_id]
    primer_dia_mes_factura = fecha_factura.replace(day=1)

    # 1. Precarga de Cartera y Anatocismo (Saldos Mora)
    # Nota: Usamos una version simplificada de cartera.py para velocidad masiva
    from app.models.aplicacion_pago import AplicacionPago
    from sqlalchemy import func

    # Subquery de aplicaciones por factura
    q_aplica = db.query(
        AplicacionPago.documento_factura_id,
        func.sum(AplicacionPago.valor_aplicado).label("total_aplicado")
    ).join(Documento, AplicacionPago.documento_pago_id == Documento.id).filter(
        Documento.empresa_id == empresa_id,
        Documento.anulado == False
    ).group_by(AplicacionPago.documento_factura_id).subquery()

    # Subquery de debitos (Solo cuentas CXC)
    q_debitos = db.query(
        MovimientoContable.documento_id,
        func.sum(MovimientoContable.debito).label("valor_total")
    ).filter(
        MovimientoContable.cuenta_id.in_(ids_cxc)
    ).group_by(MovimientoContable.documento_id).subquery()

    # Consulta masiva de pendientes con saldo
    pendientes_lote = db.query(
        Documento.id,
        Documento.unidad_ph_id,
        q_debitos.c.valor_total,
        func.coalesce(q_aplica.c.total_aplicado, 0).label("aplicado")
    ).join(q_debitos, Documento.id == q_debitos.c.documento_id)\
     .outerjoin(q_aplica, Documento.id == q_aplica.c.documento_factura_id)\
     .filter(
        Documento.empresa_id == empresa_id,
        Documento.anulado == False,
        Documento.fecha < primer_dia_mes_factura,
        (q_debitos.c.valor_total - func.coalesce(q_aplica.c.total_aplicado, 0)) > 0.01
    ).all()

    # 2. Precarga de Intereses Registrados (Para evitar Anatocismo en lote)
    ids_docs_pendientes = [p.id for p in pendientes_lote]
    mapa_anatocismo = {}
    if ids_docs_pendientes and cuentas_interes_ids:
        anatocismo_query = db.query(
            MovimientoContable.documento_id,
            func.sum(MovimientoContable.credito).label("total_interes")
        ).filter(
            MovimientoContable.documento_id.in_(ids_docs_pendientes),
            MovimientoContable.cuenta_id.in_(cuentas_interes_ids)
        ).group_by(MovimientoContable.documento_id).all()
        mapa_anatocismo = {q.documento_id: float(q.total_interes) for q in anatocismo_query}

    # Organizar saldos depurados por unidad en un mapa de memoria
    mapa_saldos_unidades = {}
    for p in pendientes_lote:
        saldo_factura = float(p.valor_total - p.aplicado)
        interes_incluido = mapa_anatocismo.get(p.id, 0)
        base_depurada = max(0, saldo_factura - interes_incluido)
        
        if p.unidad_ph_id not in mapa_saldos_unidades:
            mapa_saldos_unidades[p.unidad_ph_id] = 0
        mapa_saldos_unidades[p.unidad_ph_id] += base_depurada

    # 3. Precarga de Pagos Tardios (Recibos del mes anterior)
    ultimo_dia_mes_ant = primer_dia_mes_factura - timedelta(days=1)
    primer_dia_mes_ant = ultimo_dia_mes_ant.replace(day=1)
    
    rc_tipo = db.query(TipoDocumento).filter(TipoDocumento.empresa_id == empresa_id, TipoDocumento.codigo == 'RC').first()
    mapa_recibos_tardios = {}
    if rc_tipo:
        recibos_mes_ant = db.query(Documento).filter(
            Documento.empresa_id == empresa_id,
            Documento.tipo_documento_id == rc_tipo.id,
            Documento.fecha >= primer_dia_mes_ant,
            Documento.fecha <= ultimo_dia_mes_ant,
            Documento.anulado == False
        ).all()
        for r in recibos_mes_ant:
            if r.unidad_ph_id not in mapa_recibos_tardios:
                mapa_recibos_tardios[r.unidad_ph_id] = []
            mapa_recibos_tardios[r.unidad_ph_id].append(r)
    
    # 4. Precarga de Anticipos (Saldos a favor en Pasivo) - Corregido: agrupa por beneficiario_id
    mapa_anticipos = {}
    if config.cuenta_anticipos_id:
        print(f"--- BATCH OPTIMIZATION: Cargando saldos de anticipos (Cuenta: {config.cuenta_anticipos_id}) ---")
        anticipos_query = db.query(
            Documento.beneficiario_id,
            func.sum(MovimientoContable.credito - MovimientoContable.debito).label("saldo_anticipo")
        ).join(Documento, MovimientoContable.documento_id == Documento.id)\
         .filter(
            Documento.empresa_id == empresa_id,
            Documento.anulado == False,
            MovimientoContable.cuenta_id == config.cuenta_anticipos_id
        ).group_by(Documento.beneficiario_id).all()
        
        mapa_anticipos = {q.beneficiario_id: float(q.saldo_anticipo) for q in anticipos_query if q.saldo_anticipo and q.saldo_anticipo > 0.01}
        print(f"--- BATCH OPTIMIZATION: {len(mapa_anticipos)} propietarios con anticipos encontrados: {list(mapa_anticipos.keys())} ---")

    print(f"--- BATCH OPTIMIZATION: Precarga completada. Iniciando bucle de generacion ---")
    # -------------------------------------------
    # 6. Iterar Unidades y Generar Facturas
    for unidad in unidades:
        try:
            if not unidad.propietario_principal_id:
                resultados["errores"] += 1
                resultados["detalles"].append(f"Unidad {unidad.codigo}: Sin propietario asignado.")
                continue
            
            # Chequeo de seguridad: Si ya está facturada, solo permitir conceptos excepcionales
            ya_facturada = unidad.id in ids_ya_facturados

            movimientos = []
            total_factura = 0

            pagos_tardios_procesados = False # Control para no duplicar si hay multiples conceptos de interes

            # Procesar todos los conceptos activos para esta unidad
            for concepto in conceptos:
                # --- NUEVO FILTRO DE EXCEPCIONES ---
                # Si el concepto está en el mapa de excepciones, verificar si esta unidad está en la lista permitida
                es_excepcion_unidad = False
                if concepto.id in mapa_excepciones:
                    if unidad.id in mapa_excepciones[concepto.id]:
                        es_excepcion_unidad = True
                    else:
                        continue # Este concepto ES una excepción y esta unidad NO está en la lista.
                
                # BLINDAJE DELTA: Si la unidad ya tiene factura, SOLO procesar si es excepción explicita
                if ya_facturada and not es_excepcion_unidad:
                    continue
                # -----------------------------------

                valor_linea = 0
                es_mora = False
                saldo_mora = 0

                # --- LÓGICA DE MÓDULOS DE CONTRIBUCIÓN (HÍBRIDA: TORRE + INDIVIDUAL) ---
                if concepto.modulos:
                    # 1. Recopilar criterios de inclusión de todos los módulos vinculados al concepto
                    torres_autorizadas_ids = set()
                    concept_modulos_ids = set()
                    
                    for mod in concepto.modulos:
                        concept_modulos_ids.add(mod.id)
                        if mod.torres:
                            for t in mod.torres:
                                torres_autorizadas_ids.add(t.id)
                    
                    # 2. Verificar pertenencia de la unidad
                    # A. Por Estructura (Torre)
                    pertenece_por_torre = False
                    if torres_autorizadas_ids and unidad.torre_id in torres_autorizadas_ids:
                        pertenece_por_torre = True
                    
                    # B. Por Asignación Directa (Check individual en ficha de unidad)
                    pertenece_por_asignacion_directa = False
                    unidad_modulos_ids = {m.id for m in unidad.modulos_contribucion}
                    if unidad_modulos_ids & concept_modulos_ids:
                        pertenece_por_asignacion_directa = True
                    
                    # 3. Decisión Híbrida: Si no cumple NINGUNA de las dos, se ignora la unidad para este concepto
                    if not (pertenece_por_torre or pertenece_por_asignacion_directa):
                        continue
                # ----------------------------------------------------------------------
                # -------------------------------------------------------

                # --- CÁLCULO DE VALOR (SMART LOGIC) ---
                if concepto.es_interes:
                    print(f"--- DEBUG: Entrando a logica interes para concepto {concepto.nombre} (Unidad {unidad.codigo}) ---")
                    
                    # --- LÓGICA DE INTERÉS DIFERIDO DISCRIMINADO (Pagos Tardios del Mes Anterior) ---
                    # MOVIDO AL INICIO PARA QUE APAREZCA PRIMERO EN EL DETALLE
                    if not pagos_tardios_procesados and float(config.interes_mora_mensual) > 0 and not ya_facturada:
                        try:
                            # 2. Obtener Recibos del mapa precargado
                            recibos_tardios = mapa_recibos_tardios.get(unidad.id, [])

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
                    es_mora = True
                    if config.interes_mora_mensual > 0:
                        try:
                            # USAR MAPA DE SALDOS PRECARGADO (Cero consultas adicionales)
                            saldo_mora = mapa_saldos_unidades.get(unidad.id, 0)

                            if saldo_mora > 0:
                                interes_valor = saldo_mora * (float(config.interes_mora_mensual) / 100.0)
                                valor_linea = round(interes_valor, 2)
                                print(f"DEBUG: Unidad {unidad.codigo} tiene saldo mora {saldo_mora}. Interes: {valor_linea}")
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
                
                # Redondear a la unidad más cercana (Sin decimales) según solicitud usuario
                valor_linea = round(valor_linea, 0)
                
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
                    tipo_documento_id=global_doc_id,
                    numero=0,
                    fecha=fecha_factura,
                    fecha_vencimiento=fecha_factura,
                    beneficiario_id=unidad.propietario_principal_id,
                    observaciones=obs,
                    movimientos=movimientos,
                    unidad_ph_id=unidad.id
                )

                new_doc = documento_service.create_documento(db, doc_create, user_id=usuario_id, skip_recalculo=True, commit=False)
                db.flush()  # Forzar asignación de ID sin confirmar transacción
                resultados["generadas"] += 1
                resultados["detalles"].append(f"Unidad {unidad.codigo}: Doc {new_doc.numero} por ${total_factura:,.0f}")

                # --- LÓGICA DE AUTO-CRUCE DE ANTICIPOS ---
                # Si el propietario tiene saldo a favor en pasivo, aplicamos el cruce inmediatamente
                id_propietario = unidad.propietario_principal_id
                if config.cuenta_anticipos_id and id_propietario in mapa_anticipos and tipo_nc:
                    saldo_disponible = mapa_anticipos[id_propietario]
                    if saldo_disponible > 0.01:
                        monto_cruce = min(total_factura, saldo_disponible)
                        
                        # Crear movimientos del cruce
                        movs_cruce = [
                            # 1. Debito al Pasivo (Reducción de Anticipo)
                            doc_schemas.MovimientoContableCreate(
                                cuenta_id=config.cuenta_anticipos_id,
                                concepto=f"Cruce Anticipo - Pago Factura {new_doc.numero} - {unidad.codigo}",
                                debito=monto_cruce,
                                credito=0
                            ),
                            # 2. Credito a la Cartera (Pago de la Factura)
                            doc_schemas.MovimientoContableCreate(
                                cuenta_id=config.cuenta_cartera_id or tipo_doc_obj.cuenta_debito_cxc_id,
                                concepto=f"Cruce Anticipo - Aplicación Factura {new_doc.numero} - {unidad.codigo}",
                                debito=0,
                                credito=monto_cruce
                            )
                        ]
                        
                        doc_cruce = doc_schemas.DocumentoCreate(
                            empresa_id=empresa_id,
                            tipo_documento_id=tipo_nc.id,
                            numero=0,
                            fecha=fecha_factura,
                            fecha_vencimiento=fecha_factura,
                            beneficiario_id=id_propietario,
                            observaciones=f"Auto-cruce masivo de anticipo contra Factura {new_doc.numero}",
                            movimientos=movs_cruce,
                            unidad_ph_id=unidad.id
                        )
                        
                        cruce_obj = documento_service.create_documento(db, doc_cruce, user_id=usuario_id, skip_recalculo=True, commit=False)
                        db.flush()
                        
                        # --- APLICACION DIRECTA DE PAGO (ALTO RENDIMIENTO) ---
                        # Vincula la NC de cruce a la factura directamente en la tabla de aplicaciones.
                        # Sin recálculo completo → el saldo baja de inmediato en la pantalla de recaudos.
                        nueva_aplicacion = AplicacionPago(
                            documento_factura_id=new_doc.id,
                            documento_pago_id=cruce_obj.id,
                            valor_aplicado=monto_cruce,
                            empresa_id=empresa_id
                        )
                        db.add(nueva_aplicacion)
                        
                        # Actualizar el mapa RAM para siguientes unidades del mismo dueño
                        mapa_anticipos[id_propietario] -= monto_cruce
                        resultados["detalles"].append(f"   ↳ Cruce automático aplicado: ${monto_cruce:,.0f} (NC {cruce_obj.numero})")
                # -----------------------------------------

                # Commit por lotes de 50 para liberar memoria sin saturar la BD
                if resultados["generadas"] % 50 == 0:
                    db.commit()
                    print(f"--- BATCH COMMIT: {resultados['generadas']} facturas confirmadas ---")

        except Exception as e:
            resultados["errores"] += 1
            resultados["detalles"].append(f"Unidad {unidad.codigo}: Error - {str(e)}")
            # El rollback parcial de SQLAlchemy mantiene el estado limpio para la siguiente iteración
            db.rollback()
            continue

    # Commit final para confirmar las últimas facturas del lote
    try:
        db.commit()
        print(f"--- COMMIT FINAL: Proceso completado. {resultados['generadas']} generadas, {resultados['errores']} errores ---")
    except Exception as e_final:
        db.rollback()
        print(f"--- ERROR EN COMMIT FINAL: {str(e_final)} ---")

    return resultados

def get_historial_facturacion(db: Session, empresa_id: int):
    """
    Agrupa las facturas de PH por mes para mostrar historial usando una consulta SQL agregada eficiente.
    """
    from sqlalchemy import func, desc
    
    from app.services.propiedad_horizontal import configuracion_service
    config = configuracion_service.get_configuracion(db, empresa_id)
    if not config or not config.tipo_documento_factura_id:
        return []

    tipo_factura_id = config.tipo_documento_factura_id
    
    # 1. Obtener IDs de Cuentas CXC para el cálculo de totales
    from app.services.cartera import get_cuentas_especiales_ids
    ids_cxc = get_cuentas_especiales_ids(db, empresa_id, 'cxc')
    
    if not ids_cxc:
        # Si no hay cuentas de cartera configuradas, usamos un fallback basado en el tipo de doc
        tipo_doc = db.query(TipoDocumento).filter(TipoDocumento.id == tipo_factura_id).first()
        if tipo_doc and tipo_doc.cuenta_debito_cxc_id:
            ids_cxc = [tipo_doc.cuenta_debito_cxc_id]
    
    # 2. Consulta Agregada: Agrupar por mes, contar documentos únicos y sumar débitos a CXC
    # Usamos func.to_char para compatibilidad con PostgreSQL (entorno Render)
    resumen_query = db.query(
        func.to_char(Documento.fecha, 'YYYY-MM').label('mes'),
        func.count(Documento.id.distinct()).label('cantidad'),
        func.sum(MovimientoContable.debito).label('total')
    ).join(MovimientoContable, MovimientoContable.documento_id == Documento.id)\
     .filter(
        Documento.empresa_id == empresa_id, 
        Documento.tipo_documento_id == tipo_factura_id,
        Documento.estado.in_(['ACTIVO', 'PROCESADO']),
        MovimientoContable.cuenta_id.in_(ids_cxc) if ids_cxc else True
    )\
    .group_by('mes')\
    .order_by(desc('mes'))
    
    stats = resumen_query.all()
    
    return [
        {
            "periodo": s.mes,
            "cantidad": s.cantidad,
            "total": float(s.total or 0)
        } for s in stats
    ]

def eliminar_facturacion_masiva(db: Session, empresa_id: int, periodo: str, usuario_id: int):
    """
    Elimina todas las facturas de un periodo (YYYY-MM).
    OPTIMIZADO: Recalcula la cartera de cada propietario UNA SOLA VEZ al final,
    en lugar de hacerlo por cada factura eliminada. Esto reduce el tiempo de
    ejecución de minutos a segundos.
    """
    from app.services.propiedad_horizontal import configuracion_service
    config = configuracion_service.get_configuracion(db, empresa_id)
    if not config or not config.tipo_documento_factura_id:
        raise Exception("Configuracion PH invalida.")

    from sqlalchemy import func
    # Buscar documentos del periodo
    docs = db.query(Documento).filter(
        Documento.empresa_id == empresa_id,
        Documento.tipo_documento_id == config.tipo_documento_factura_id,
        func.to_char(Documento.fecha, 'YYYY-MM') == periodo,
        Documento.estado.in_(['ACTIVO', 'PROCESADO'])
    ).all()

    if not docs:
        return {"mensaje": "No se encontraron facturas para este periodo.", "eliminadas": 0}

    count = 0
    errores = 0
    terceros_a_recalcular = set()  # Acumular terceros ANTES de eliminar, para recálculo único al final
    from app.services.documento import eliminar_documento
    from app.services import cartera as cartera_service

    # Recolectar todos los propietarios afectados antes de empezar
    for doc in docs:
        if doc.beneficiario_id:
            terceros_a_recalcular.add(doc.beneficiario_id)

    # BUCLE DE ELIMINACIÓN: Sin commit ni recálculo de cartera por iteración
    # commit=True es necesario por la arquitectura de eliminar_documento (maneja su propia transacción)
    # pero le decimos recalc=False para que NO recalcule inventario (las facturas PH no tienen inventario)
    for doc in docs:
        try:
            eliminar_documento(
                db,
                doc.id,
                empresa_id,
                usuario_id,
                "Eliminacion Masiva Facturacion PH",
                commit=True,
                recalc=False  # CLAVE: Evita X recálculos de inventario (no aplica aquí)
            )
            count += 1
            if count % 20 == 0:
                print(f"[ELIMINACION PH] Progreso: {count}/{len(docs)} facturas eliminadas...")
        except Exception as e_del:
            errores += 1
            print(f"[ELIMINACION PH] Error eliminando doc {doc.id}: {str(e_del)}")
            try:
                db.rollback()
            except:
                pass
            continue

    # RECÁLCULO ÚNICO DE CARTERA: Una sola vez por propietario, al final de todo
    # Esto reemplaza los N recálculos que antes ocurrían dentro de eliminar_documento
    print(f"[ELIMINACION PH] Iniciando recálculo de cartera para {len(terceros_a_recalcular)} propietarios únicos...")
    for t_id in terceros_a_recalcular:
        try:
            cartera_service.recalcular_aplicaciones_tercero(db, tercero_id=t_id, empresa_id=empresa_id, commit=True)
        except Exception as e_recalc:
            print(f"[ELIMINACION PH] Error recalculando cartera tercero {t_id}: {str(e_recalc)}")

    print(f"[ELIMINACION PH] Completado: {count} eliminadas, {errores} errores.")
    return {
        "mensaje": f"Facturacion del periodo {periodo} eliminada correctamente.",
        "eliminadas": count,
        "errores": errores
    }

def check_facturacion_periodo(db: Session, empresa_id: int, fecha: date):
    """
    Verifica si ya existen facturas de PH para el mes indicado.
    Retorna la cantidad encontrada.
    """
    from sqlalchemy import func
    
    from app.services.propiedad_horizontal import configuracion_service
    config = configuracion_service.get_configuracion(db, empresa_id)
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
        
        from app.services.propiedad_horizontal import configuracion_service
        config = configuracion_service.get_configuracion(db, empresa_id)
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
            
        # Ordenar el detalle de facturación lógicamente por el campo 'detalle' (que tiene el código de unidad)
        lista_final.sort(key=lambda x: natural_sort_key(x['detalle']))
        
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
    
    from app.services.propiedad_horizontal import configuracion_service
    config = configuracion_service.get_configuracion(db, empresa_id)
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
