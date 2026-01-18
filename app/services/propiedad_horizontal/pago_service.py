from sqlalchemy.orm import Session, joinedload, selectinload
from typing import Optional
from fastapi import HTTPException
from app.models.propiedad_horizontal import PHUnidad, PHConfiguracion
from app.models.documento import Documento
from app.models.movimiento_contable import MovimientoContable
from app.models.tipo_documento import TipoDocumento
from app.services import cartera as cartera_service
from app.services import documento as documento_service
from app.schemas import documento as doc_schemas
from app.core.constants import FuncionEspecial
from datetime import date

def get_estado_cuenta_unidad(db: Session, unidad_id: int, empresa_id: int):
    # 1. Obtener Unidad y Propietario
    unidad = db.query(PHUnidad).filter(PHUnidad.id == unidad_id, PHUnidad.empresa_id == empresa_id).first()
    if not unidad:
        raise HTTPException(status_code=404, detail="Unidad no encontrada")
    
    if not unidad.propietario_principal_id:
        return {"unidad": unidad.codigo, "propietario": "Sin Propietario", "saldo_total": 0, "facturas_pendientes": []}

    # 2. Consultar Cartera del Propietario
    # OJO: Esto trae TODA la deuda del tercero. Si tuviera multiples unidades, se mezcla.
    # Idealmente filtraríamos por un campo en el documento, pero por ahora asumimos 1 propietario -> N unidades (o deuda global).
    
    # IMPORTANTE: El recálculo ahora se hace dentro de get_cartera_ph_pendientes para evitar race conditions
    
    # CORRECCIÓN: Usamos la funcion especializada que filtra por UNIDAD
    # Antes usabamos la generica de cartera y mezclaba apartamentos del mismo dueño.
    facturas_pendientes = get_cartera_ph_pendientes(
        db, 
        empresa_id=empresa_id, 
        unidad_id=unidad_id, # FILTRO CLAVE
        propietario_id=unidad.propietario_principal_id
    )
    
    # CORRECCIÓN DEFINITIVA DE SALDO:
    # En lugar de sumar las facturas pendientes (que depende de que los cruces/aplicaciones estén perfectos),
    # Calculamos el saldo CONTABLE real basado en movimientos, que es la verdad absoluta.
    # Esto asegura que el "Saldo Total" coincida siempre con el final de la tabla de historial.
    datos_historial = get_historial_cuenta_unidad(db, unidad_id, empresa_id)
    saldo_total = datos_historial['saldo_actual']

    return {
        "unidad": unidad.codigo,
        "propietario_id": unidad.propietario_principal_id,
        "propietario_nombre": unidad.propietario_principal.razon_social if unidad.propietario_principal else "Desconocido",
        "saldo_total": saldo_total,
        "facturas_pendientes": facturas_pendientes
    }

def get_historial_cuenta_unidad(db: Session, unidad_id: Optional[int], empresa_id: int, fecha_inicio: date = None, fecha_fin: date = None, propietario_id: Optional[int] = None):
    # 1. Obtener Datos Básicos
    unidad = None
    tercero_id = propietario_id

    if unidad_id:
        unidad = db.query(PHUnidad).filter(PHUnidad.id == unidad_id, PHUnidad.empresa_id == empresa_id).first()
        if not unidad:
            raise HTTPException(status_code=404, detail="Unidad no encontrada")
        tercero_id = unidad.propietario_principal_id
    
    if not tercero_id:
         return {"unidad": unidad, "transacciones": [], "saldo_actual": 0}

    # 2. Consultar Movimientos
    # Buscamos Documentos donde el beneficiario sea el propietario
    # Y que sean de tipos de documento de CXC (Factura o Recibo)
    
    query = db.query(Documento).options(
        joinedload(Documento.tipo_documento),
        joinedload(Documento.unidad_ph), # Cargar Unidad relacionada
        selectinload(Documento.movimientos).joinedload(MovimientoContable.cuenta)
    ).filter(
        Documento.empresa_id == empresa_id,
        Documento.beneficiario_id == tercero_id,
        Documento.estado.in_(['ACTIVO', 'PROCESADO'])
    )

    if unidad_id:
        query = query.filter(Documento.unidad_ph_id == unidad_id)

    # Filtros de Fecha
    if fecha_inicio:
        query = query.filter(Documento.fecha >= fecha_inicio)
    if fecha_fin:
        query = query.filter(Documento.fecha <= fecha_fin)

    docs = query.order_by(Documento.fecha.asc(), Documento.id.asc()).all()

    # 3. Construir Historial
    transacciones = []
    saldo = 0
    
    # Identificar cuentas de cartera validas (incluyendo la configurada en PH)
    cuentas_cxc_ids = cartera_service.get_cuentas_especiales_ids(db, empresa_id, 'cxc')

    for doc in docs:
        # Calcular impacto en cartera de este documento
        # Usamos los movimientos del documento.
        
        impacto_cxc = 0
        for mov in doc.movimientos:
            # Si la cuenta está en el grupo de Cartera (13, 16 config, etc)
            if mov.cuenta_id in cuentas_cxc_ids:
                impacto_cxc += (mov.debito - mov.credito)
        
        if impacto_cxc != 0:
            saldo += impacto_cxc
            
            # Construir detalle con Unidad
            unidad_texto = f"Unidad {doc.unidad_ph.codigo}" if doc.unidad_ph else "Unidad General"
            concepto = f"{unidad_texto} - {doc.observaciones}" if doc.observaciones else unidad_texto

            transacciones.append({
                "fecha": doc.fecha,
                "documento": f"{doc.tipo_documento.codigo} - {doc.numero}",
                "tipo": doc.tipo_documento.nombre,
                # Usar Unit Code como detalle principal
                "concepto": concepto,
                "debito": impacto_cxc if impacto_cxc > 0 else 0, # Cargos
                "credito": abs(impacto_cxc) if impacto_cxc < 0 else 0, # Pagos
                "saldo": saldo,
                # Compatibilidad (opcional)
                "cargo": impacto_cxc if impacto_cxc > 0 else 0,
                "abono": abs(impacto_cxc) if impacto_cxc < 0 else 0
            })

    return {
        "unidad": unidad,
        "propietario": unidad.propietario_principal if unidad else None,
        "propietario_id": tercero_id, # Retornamos ID del tercero
        "transacciones": transacciones,
        "saldo_actual": saldo
    }

def registrar_pago_unidad(db: Session, unidad_id: int, empresa_id: int, usuario_id: int, monto: float, fecha_pago: date, forma_pago_id: int = None):
    # 1. Validaciones
    if monto <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser mayor a 0.")
    
    print(f"DEBUG: Buscando configuración PH para empresa_id={empresa_id}")
    config = db.query(PHConfiguracion).filter(PHConfiguracion.empresa_id == empresa_id).first()
    
    if config:
        print(f"DEBUG: Config encontrada. ID={config.id}, ReciboDocID={config.tipo_documento_recibo_id}")
    else:
        print("DEBUG: Configuración PH es None (No existe fila en la tabla para esta empresa).")

    if not config or not config.tipo_documento_recibo_id:
        raise HTTPException(status_code=400, detail="No se ha configurado el Tipo de Documento para Recibos de Caja en PH.")

    tipo_doc = db.query(TipoDocumento).filter(TipoDocumento.id == config.tipo_documento_recibo_id).first()
    if not tipo_doc:
         raise HTTPException(status_code=404, detail="Tipo de Documento de Recibo no encontrado.")

    estado_cuenta = get_estado_cuenta_unidad(db, unidad_id, empresa_id)
    if not estado_cuenta['propietario_id']:
        raise HTTPException(status_code=400, detail="La unidad no tiene propietario asignado para registrar el pago.")

    # 2. Crear Movimientos Contables
    movimientos = []
    
    # A. Débito (Entrada de Dinero - Caja/Banco)
    # NUEVA LÓGICA (Usuario solicitó por Concepto):
    # Buscamos qué conceptos debe la unidad para saber a qué cuenta de caja debe ir el dinero.
    cuenta_caja_final = None
    
    # 1. Analizar deuda pendiente para identificar concepto mayoritario
    # Obtenemos las facturas pendientes
    pendientes = get_cartera_ph_pendientes(db, empresa_id, unidad_id=unidad_id)
    
    if pendientes:
        # Si hay deuda, intentamos inferir la caja basada en el concepto de la deuda
        try:
            # Traemos los conceptos activos que tengan cuenta de caja configurada
            from app.models.propiedad_horizontal.concepto import PHConcepto
            conceptos_con_caja = db.query(PHConcepto).filter(
                PHConcepto.empresa_id == empresa_id,
                PHConcepto.cuenta_caja_id.isnot(None)
            ).all()
            
            # Crear mapa: CuentaCXC -> CuentaCaja
            # Asumimos que la factura afectó la cuenta_cxc del concepto.
            mapa_cxc_caja = {c.cuenta_cxc_id: c.cuenta_caja_id for c in conceptos_con_caja if c.cuenta_cxc_id}
            
            if mapa_cxc_caja:
                # Buscamos en los movimientos de las facturas pendientes qué cuenta CXC se movió
                doc_ids = [p['id'] for p in pendientes]
                
                # Query para ver cuentas afectadas en esos documentos (limitado a las cuentas cxc mapeadas)
                # Buscamos el primer match para simplificar (o el más reciente)
                stmt = db.query(MovimientoContable.cuenta_id).filter(
                    MovimientoContable.documento_id.in_(doc_ids),
                    MovimientoContable.cuenta_id.in_(mapa_cxc_caja.keys())
                ).limit(1)
                
                cuenta_cxc_encontrada = db.execute(stmt).scalar()
                
                if cuenta_cxc_encontrada and cuenta_cxc_encontrada in mapa_cxc_caja:
                    cuenta_caja_final = mapa_cxc_caja[cuenta_cxc_encontrada]
                    print(f"DEBUG: Caja resuelta por Concepto (CXC {cuenta_cxc_encontrada} -> Caja {cuenta_caja_final})")

        except Exception as e:
            print(f"WARN: Error intentando resolver caja por concepto: {e}")

    # Fallbacks standard si no se resolvio por concepto (o no habia dedua)
    if not cuenta_caja_final:
        # Usar cuenta debito CXC estandar del Tipo Doc Recibo (A veces la caja se configura ahi)
        cuenta_caja_final = tipo_doc.cuenta_debito_cxc_id 
        
        # Fallback 2: Usar campo especial 'cuenta_caja_id' de Tipo Doc
        if not cuenta_caja_final:
             caja_id_custom = getattr(tipo_doc, 'cuenta_caja_id', None)
             if caja_id_custom:
                 cuenta_caja_final = caja_id_custom
    
    # Fallback 3: Global Config (Para compatibilidad si aun existe en algun lado, aunque lo quitamos de UI)
    if not cuenta_caja_final and config.cuenta_caja_id:
        cuenta_caja_final = config.cuenta_caja_id

    if not cuenta_caja_final:
         raise HTTPException(status_code=400, detail="No se encontró cuenta de Caja/Bancos. Configure 'Cuenta Caja' en el Concepto de Facturación o en el Tipo de Documento.")

    # B. Crédito a Cartera (Disminuye deuda)
    # PRIORIDAD: Intentar resolver por concepto (Igual que la caja)
    cuenta_cartera_final = None

    if pendientes:
        try:
             # Usamos el mismo mapa_cxc_caja o lógica similar si ya lo calculamos antes.
             # Si encontramos la cuenta CXC en el documento pagado, esa ES la cuenta cartera final.
             if 'cuenta_cxc_encontrada' in locals() and cuenta_cxc_encontrada:
                 cuenta_cartera_final = cuenta_cxc_encontrada
                 print(f"DEBUG: Cartera resuelta por Concepto (CXC detectada: {cuenta_cartera_final})")
        except Exception as e:
            print(f"WARN: Error resolviendo cartera por concepto: {e}")

    # Fallback 1: Config Global (si existe)
    if not cuenta_cartera_final and config.cuenta_cartera_id:
        cuenta_cartera_final = config.cuenta_cartera_id
    
    # Fallback 2: Tipo Doc Recibo (Credito CXC)
    if not cuenta_cartera_final:
        cuenta_cartera_final = tipo_doc.cuenta_credito_cxc_id
    
    if not cuenta_cartera_final:
        raise HTTPException(status_code=400, detail="No se encontró cuenta de Cartera. Configure 'Cuenta Cartera' en Parámetros PH.")
    
    # Agregar Movimiento Crédito (Abono a Cartera)
    movimientos.append(doc_schemas.MovimientoContableCreate(
        cuenta_id=cuenta_cartera_final,
        concepto=f"Abono/Pago Unidad {estado_cuenta['unidad']}",
        debito=0,
        credito=monto
    ))

    # C. Agregar Movimiento Débito (Entra a Caja)
    # OJO: Anteriormente estaba implícito o faltaba en el snippet, aqui lo agrego explicito.
    movimientos.append(doc_schemas.MovimientoContableCreate(
        cuenta_id=cuenta_caja_final,
        concepto=f"Ingreso Pago Unidad {estado_cuenta['unidad']}",
        debito=monto,
        credito=0
    ))

    # C. Débito a Caja (Entra dinero)
    # Necesitamos una cuenta de caja. 
    # VOY A ASUMIR que por ahora usamos la cuenta DEBITO del mismo tipo de documento si está configurada, sino ERROR.

    # 3. Crear Documento
    doc_create = doc_schemas.DocumentoCreate(
        empresa_id=empresa_id,
        tipo_documento_id=tipo_doc.id,
        numero=0,
        fecha=fecha_pago,
        beneficiario_id=estado_cuenta['propietario_id'],
        unidad_ph_id=unidad_id, # FIX: Vincular documento a unidad PH
        observaciones=f"Pago PH Unidad {estado_cuenta['unidad']}",
        movimientos=movimientos
    )

    new_doc = documento_service.create_documento(db, doc_create, user_id=usuario_id)

    # --- 4. OPCIÓN 2: GENERACIÓN AUTOMÁTICA DE MORA (Late Payment Sanction) ---
    # Si la fecha de pago supera el límite, generamos una Nota Débito automática.
    if False and config.interes_mora_habilitado and config.dia_limite_pago: # DISABLED: Deferred Model (Cobro en Facturacion)
        if fecha_pago.day > config.dia_limite_pago:
            # Calcular Sanción
            # Usamos el % configurado sobre el valor pagado como simplificación "Sanción por Extemporaneidad"
            # Si hubiera un campo "valor_sancion_fija", lo usaríamos aquí.
            tasa = config.interes_mora_mensual or 0
            valor_sancion = monto * (tasa / 100.0)
            
            if valor_sancion > 0:
                print(f"DEBUG: Pago Extemporáneo detectado (Día {fecha_pago.day} > {config.dia_limite_pago}). Generando ND por {valor_sancion}")
                
                # Buscar Tipo Doc para la Mora (ND)
                # PRIORITY: Configurado explícitamente
                tipo_nd = None
                if config.tipo_documento_mora_id:
                    tipo_nd = db.query(TipoDocumento).filter(TipoDocumento.id == config.tipo_documento_mora_id).first()
                
                # Fallback: Buscar por código 'ND'
                if not tipo_nd:
                    tipo_nd = db.query(TipoDocumento).filter(TipoDocumento.codigo == 'ND', TipoDocumento.empresa_id == empresa_id).first()
                
                # Fallback Global
                if not tipo_nd:
                     tipo_nd = db.query(TipoDocumento).filter(TipoDocumento.codigo == 'ND').first()
                
                if tipo_nd:
                    # Cuentas para la Mora
                    cta_cartera = cuenta_cartera_final # Aumenta la deuda (Misma cuenta del pago)
                    cta_ingreso = config.cuenta_ingreso_intereses_id
                    
                    if not cta_ingreso:
                        # Fallback: Usar cuenta credito del Tipo ND si existe
                        cta_ingreso = tipo_nd.cuenta_credito_id
                    
                    if cta_cartera and cta_ingreso:
                        movs_nd = [
                            # Debito a Cartera (Aumenta la deuda del cliente)
                            doc_schemas.MovimientoContableCreate(
                                cuenta_id=cta_cartera,
                                concepto=f"Sanción Mora ({tasa}% sobre ${monto:,.0f})",
                                debito=valor_sancion,
                                credito=0
                            ),
                            # Credito a Ingreso (Ganancia para la empresa)
                            doc_schemas.MovimientoContableCreate(
                                cuenta_id=cta_ingreso,
                                concepto=f"Ingreso Mora ({tasa}% sobre ${monto:,.0f}) - {estado_cuenta['unidad']}",
                                debito=0,
                                credito=valor_sancion
                            )
                        ]
                        
                        doc_nd_create = doc_schemas.DocumentoCreate(
                            empresa_id=empresa_id,
                            tipo_documento_id=tipo_nd.id,
                            numero=0,
                            fecha=fecha_pago,
                            beneficiario_id=estado_cuenta['propietario_id'],
                            unidad_ph_id=unidad_id,
                            observaciones=f"Sanción Mora ({tasa}% sobre ${monto:,.0f})",
                            movimientos=movs_nd
                        )
                        documento_service.create_documento(db, doc_nd_create, user_id=usuario_id)
                    else:
                        print("WARN: No se pudo generar Mora Automática. Faltan cuentas contables (Cartera o Ingreso Intereses).")
                else:
                     print("WARN: No se pudo generar Mora Automática. Tipo Documento 'ND' no existe.")

    # --- 5. DETECCIÓN DE NECESIDAD DE RECÁLCULO (Retroactivo) ---
    sugerir_recalculo = False
    try:
        # Verificar si existen FACTURAS ACTIVAS posteriores a la fecha de este pago
        # que podrían requerir recalculo de intereses.
        facturas_futuras = db.query(Documento).join(TipoDocumento).filter(
            Documento.empresa_id == empresa_id,
            Documento.unidad_ph_id == unidad_id,
            Documento.fecha > fecha_pago,
            Documento.estado.in_(['ACTIVO', 'PROCESADO']),
            TipoDocumento.codigo == 'FPH' # O el código que usen para facturas PH
        ).count()
        
        if facturas_futuras > 0:
            print(f"DEBUG: Pago retroactivo. Existen {facturas_futuras} facturas posteriores.")
            sugerir_recalculo = True
            
    except Exception as e:
        print(f"WARN: Error verificando facturas futuras: {e}")

    # Retornamos estructura enriquecida (routes.py debe manejar esto)
    return {
        "documento": new_doc,
        "sugerir_recalculo": sugerir_recalculo,
        "facturas_futuras_count": facturas_futuras if 'facturas_futuras' in locals() else 0
    }

# --- NUEVOS SERVICIOS PARA VISTA CONSOLIDADA (Analysis Implementation) ---

def get_estado_cuenta_propietario(db: Session, propietario_id: int, empresa_id: int):
    """
    Retorna el estado de cuenta consolidado para un propietario y todas sus unidades.
    """
    # 1. Obtener Propietario
    from app.models.tercero import Tercero
    propietario = db.query(Tercero).filter(Tercero.id == propietario_id, Tercero.empresa_id == empresa_id).first()
    if not propietario:
         raise HTTPException(status_code=404, detail="Propietario no encontrado")

    # 2. Obtener Unidades asociadas
    unidades = db.query(PHUnidad).filter(
        PHUnidad.empresa_id == empresa_id,
        PHUnidad.propietario_principal_id == propietario_id
    ).all()

    desglose_unidades = []
    saldo_total_consolidado = 0
    facturas_pendientes_todas = []

    # 3. Iterar y Consolidar
    # Forzamos recálculo una sola vez por seguridad
    cartera_service.recalcular_aplicaciones_tercero(db, propietario_id, empresa_id)

    for u in unidades:
        # Llamamos al individual (pero optimizado, ya recalculó arriba)
        # Nota: get_estado_cuenta_unidad hace recalculo, es redundante pero seguro.
        # Si performance es problema, refactorizamos.
        estado_u = get_estado_cuenta_unidad(db, u.id, empresa_id)
        
        desglose_unidades.append({
            "unidad_id": u.id,
            "codigo": u.codigo,
            "saldo": estado_u['saldo_total']
        })
        saldo_total_consolidado += estado_u['saldo_total']
        
        # Filtramos facturas pendientes QUE PERTENEZCAN a esta unidad
        # get_estado_cuenta_unidad trae TODO lo del tercero. Debemos filtrar por unidad si es posible.
        # PERO: get_estado_cuenta_unidad actualmente usa 'get_facturas_pendientes_por_tercero', 
        # que NO distingue unidad.
        # SOLUCION: En el paso 4 haremos el filtrado correcto al armar la lista final.

    # 4. Obtener Cartera REAL (Pendientes) con Distincion de Unidad
    # Usamos nuestra nueva funcion especializada
    docs_pendientes = get_cartera_ph_pendientes(db, empresa_id, propietario_id=propietario_id)
    
    return {
        "propietario": {
            "id": propietario.id,
            "nombre": propietario.razon_social,
            "documento": propietario.nit
        },
        "saldo_total_consolidado": saldo_total_consolidado,
        "desglose_por_unidad": desglose_unidades,
        "facturas_pendientes": docs_pendientes # Lista plana de todo lo que debe
    }

def get_cartera_ph_pendientes(db: Session, empresa_id: int, unidad_id: int = None, propietario_id: int = None):
    """
    Versión especializada de cartera pendiente para PH.
    Permite filtrar por Unidad Específica.
    """
    # BLINDAJE: Asegurar Recalculo Fresco
    # Si tenemos contexto del tercero, forzamos recálculo para que el usuario vea la realidad instantánea
    target_propietario_id = propietario_id
    if not target_propietario_id and unidad_id:
        # Inferir propietario desde la unidad
        u_temp = db.query(PHUnidad.propietario_principal_id).filter(PHUnidad.id == unidad_id).first()
        if u_temp:
            target_propietario_id = u_temp[0]
    
    if target_propietario_id:
         cartera_service.recalcular_aplicaciones_tercero(db, target_propietario_id, empresa_id)

    # Reutilizamos la lógica base de Cartera pero con filtro extra
    from sqlalchemy import func
    
    cuentas_cxc_ids = cartera_service.get_cuentas_especiales_ids(db, empresa_id, 'cxc')
    if not cuentas_cxc_ids:
        return []

    # Subqueries (igual que cartera.py)
    subquery_valor_total = db.query(
        MovimientoContable.documento_id.label("documento_id"),
        func.sum(MovimientoContable.debito).label("valor_total")
    ).join(Documento, MovimientoContable.documento_id == Documento.id).filter(
        Documento.empresa_id == empresa_id,
        Documento.anulado == False,
        MovimientoContable.cuenta_id.in_(cuentas_cxc_ids)
    ).group_by(MovimientoContable.documento_id).subquery()
    
    from app.models.aplicacion_pago import AplicacionPago
    subquery_valor_aplicado = db.query(
        AplicacionPago.documento_factura_id.label("documento_id"),
        func.sum(AplicacionPago.valor_aplicado).label("total_aplicado")
    ).join(Documento, AplicacionPago.documento_pago_id == Documento.id).filter(
        Documento.anulado == False
    ).group_by(AplicacionPago.documento_factura_id).subquery()

    # Query Principal
    # --- QUERY A: FACTURAS (DEBITOS) ---
    query_facturas = db.query(
        Documento.id, Documento.numero, Documento.fecha, Documento.unidad_ph_id,
        PHUnidad.codigo.label("unidad_codigo"),
        subquery_valor_total.c.valor_total,
        func.coalesce(subquery_valor_aplicado.c.total_aplicado, 0).label("total_aplicado"),
        TipoDocumento.codigo.label("tipo_doc_codigo")
    ).join(
        subquery_valor_total, subquery_valor_total.c.documento_id == Documento.id
    ).join(
        TipoDocumento, Documento.tipo_documento_id == TipoDocumento.id
    ).outerjoin(
        subquery_valor_aplicado, subquery_valor_aplicado.c.documento_id == Documento.id
    ).outerjoin(
        PHUnidad, Documento.unidad_ph_id == PHUnidad.id
    ).filter(
        Documento.empresa_id == empresa_id,
        Documento.anulado == False,
        subquery_valor_total.c.valor_total > func.coalesce(subquery_valor_aplicado.c.total_aplicado, 0)
    )

    if unidad_id: query_facturas = query_facturas.filter(Documento.unidad_ph_id == unidad_id)
    if propietario_id: query_facturas = query_facturas.filter(Documento.beneficiario_id == propietario_id)
    
    facturas_activas = query_facturas.all()

    # --- QUERY B: PAGOS / ANTICIPOS (CREDITOS NO APLICADOS) ---
    # Buscamos documentos donde haya Credito a CXC > Aplicado
    
    subquery_valor_credito = db.query(
        MovimientoContable.documento_id.label("documento_id"),
        func.sum(MovimientoContable.credito).label("valor_credito")
    ).join(Documento, MovimientoContable.documento_id == Documento.id).filter(
        Documento.empresa_id == empresa_id,
        Documento.anulado == False,
        MovimientoContable.cuenta_id.in_(cuentas_cxc_ids)
    ).group_by(MovimientoContable.documento_id).subquery()

    # La tabla de aplicacion tiene: documento_pago_id (el recibo) y documento_factura_id (la factura)
    # Queremos saber cuanto de este recibo se ha usado.
    subquery_uso_pago = db.query(
        AplicacionPago.documento_pago_id.label("documento_id"),
        func.sum(AplicacionPago.valor_aplicado).label("total_usado")
    ).join(Documento, AplicacionPago.documento_pago_id == Documento.id).filter(
        Documento.anulado == False
    ).group_by(AplicacionPago.documento_pago_id).subquery()

    query_pagos = db.query(
        Documento.id, Documento.numero, Documento.fecha, Documento.unidad_ph_id,
        PHUnidad.codigo.label("unidad_codigo"),
        subquery_valor_credito.c.valor_credito,
        func.coalesce(subquery_uso_pago.c.total_usado, 0).label("total_usado"),
        TipoDocumento.codigo.label("tipo_doc_codigo")
    ).join(
        subquery_valor_credito, subquery_valor_credito.c.documento_id == Documento.id
    ).join(
        TipoDocumento, Documento.tipo_documento_id == TipoDocumento.id
    ).outerjoin(
        subquery_uso_pago, subquery_uso_pago.c.documento_id == Documento.id
    ).outerjoin(
        PHUnidad, Documento.unidad_ph_id == PHUnidad.id
    ).filter(
        Documento.empresa_id == empresa_id,
        Documento.anulado == False,
        subquery_valor_credito.c.valor_credito > func.coalesce(subquery_uso_pago.c.total_usado, 0) + 0.01 # Margen flotante
    )

    if unidad_id: query_pagos = query_pagos.filter(Documento.unidad_ph_id == unidad_id)
    if propietario_id: query_pagos = query_pagos.filter(Documento.beneficiario_id == propietario_id)

    pagos_activos = query_pagos.all()

    # --- FORMATO FINAL ---
    formateado = []
    
    # 1. Facturas (Positivas)
    for row in facturas_activas:
        saldo = float(row.valor_total) - float(row.total_aplicado)
        formateado.append({
            "id": row.id,
            "numero": f"{row.tipo_doc_codigo} - {row.numero}",
            "fecha": row.fecha.isoformat(),
            "unidad_codigo": row.unidad_codigo or "N/A",
            "valor_total": float(row.valor_total),
            "saldo_pendiente": saldo,
            "tipo": "FACTURA"
        })

    # 2. Pagos (Negativos)
    for row in pagos_activos:
        # Saldo a favor = Credito - Usado
        saldo_favor = float(row.valor_credito) - float(row.total_usado)
        if saldo_favor > 0.1: # Ignorar decimales minimos
            formateado.append({
                "id": row.id,
                "numero": f"{row.tipo_doc_codigo} - {row.numero}",
                "fecha": row.fecha.isoformat(),
                "unidad_codigo": row.unidad_codigo or "N/A",
                "valor_total": float(row.valor_credito),
                "saldo_pendiente": -saldo_favor, # NEGATIVO PARA RESTAR EN UI
                "tipo": "PAGO"
            })
        
    # Ordenar por fecha
    formateado.sort(key=lambda x: x['fecha'])
        
    return formateado

def generar_pdf_estado_cuenta(db: Session, empresa_id: int, unidad_id: int = None, propietario_id: int = None, view_mode: str = 'PENDING', fecha_inicio: date = None, fecha_fin: date = None):
    from weasyprint import HTML
    from jinja2 import Environment, select_autoescape
    from app.services._templates_empaquetados import TEMPLATES_EMPAQUETADOS
    from app.models.empresa import Empresa
    from app.models.propiedad_horizontal.configuracion import PHConfiguracion

    # 1. Obtener Datos Generales
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    
    # Resolver Entidad Principal (Unidad o Propietario)
    unidad_codigo = "N/A"
    propietario_data = {"nombre": "Desconocido", "documento": ""}
    
    if unidad_id:
        unidad = db.query(PHUnidad).filter(PHUnidad.id == unidad_id).first()
        if unidad: 
            unidad_codigo = unidad.codigo
            if unidad.propietario_principal:
                propietario_data = {
                    "nombre": unidad.propietario_principal.razon_social,
                    "documento": unidad.propietario_principal.nit
                }
    elif propietario_id:
        from app.models.tercero import Tercero
        prop = db.query(Tercero).filter(Tercero.id == propietario_id).first()
        if prop:
            propietario_data = {"nombre": prop.razon_social, "documento": prop.nit}
            # Buscar unidades del propietario
            units = db.query(PHUnidad).filter(PHUnidad.propietario_principal_id == propietario_id).all()
            if units:
                unidad_codigo = ", ".join([u.codigo for u in units])
            else:
                unidad_codigo = "VARIAS (Ver Detalle)"

    
    # 2. Selección de Modo y Datos y TERMINOLOGÍA
    # Detectar Tipo de Negocio para etiquetas dinámicas
    tipo_negocio = 'PH_RESIDENCIAL'
    tipo_negocio = 'PH_RESIDENCIAL'
    # Validar existencia de atributo en modelo Empresa (no existe actualmente)
    if hasattr(empresa, 'tipo_negocio') and empresa.tipo_negocio: 
         tipo_negocio = empresa.tipo_negocio
    
    # Buscar en PHConfiguracion si no está en Empresa
    ph_config = db.query(PHConfiguracion).filter(PHConfiguracion.empresa_id == empresa_id).first()
    if ph_config:
         tipo_negocio = ph_config.tipo_negocio
         
    # Definir Etiquetas
    labels = {
        "entidad_principal": "PROPIETARIO",
        "entidad_secundaria": "UNIDAD / INMUEBLE",
        "entidad_secundaria_short": "UNIDAD",
        "titulo_reporte_historico": "ESTADO DE CUENTA - HISTÓRICO DETALLADO",
        "titulo_reporte_cobro": "RELACIÓN DE COBRO (PENDIENTES)"
    }
    
    if tipo_negocio == 'EDUCATIVO':
        labels = {
            "entidad_principal": "ACUDIENTE / TITULAR",
            "entidad_secundaria": "ESTUDIANTE / GRADO",
            "entidad_secundaria_short": "ESTUDIANTE",
            "titulo_reporte_historico": "ESTADO DE CUENTA - GESTIÓN EDUCATIVA",
            "titulo_reporte_cobro": "RELACIÓN DE COBRO - PENSIONES"
        }

    template_name = ""
    context = {
        "empresa": empresa,
        "propietario": propietario_data,
        "unidad_codigo": unidad_codigo,
        "fecha_impresion": date.today().strftime('%Y-%m-%d'),
        "labels": labels # IS NEW
    }

    if view_mode == 'PENDING':
        # --- RELACION DE COBRO ---
        items = get_cartera_ph_pendientes(
            db, empresa_id, unidad_id=unidad_id, propietario_id=propietario_id
        )
        
        # Reformatear para template
        items_fmt = []
        total_pendiente = 0
        for i in items:
            items_fmt.append({
                "fecha_fmt": i['fecha'][:10],
                "numero": i['numero'],
                "tipo": i['tipo'],
                "unidad_codigo": i['unidad_codigo'],
                "valor_total": i['valor_total'],
                "saldo_pendiente": i['saldo_pendiente']
            })
            total_pendiente += i['saldo_pendiente']
            
        context["items"] = items_fmt
        context["total_pendiente"] = total_pendiente
        template_name = 'reports/estado_cuenta_ph_pendientes_report.html'

    elif view_mode == 'HISTORY':
        # --- HISTORIAL DETALLADO ---
        data_hist = get_historial_cuenta_ph_detailed(
            db, empresa_id, unidad_id=unidad_id, propietario_id=propietario_id,
            fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
        )
        
        context.update(data_hist)
        # data_hist trae: transacciones, saldo_anterior, saldo_final, fecha_inicio, fecha_fin
        
        template_name = 'reports/estado_cuenta_ph_historico_report.html'
    
    else:
        raise HTTPException(status_code=400, detail="Modo de vista inválido")

    # 3. Renderizar PDF
    if template_name not in TEMPLATES_EMPAQUETADOS:
        raise HTTPException(status_code=500, detail=f"Plantilla {template_name} no encontrada.")

    try:
        env = Environment(loader=None, autoescape=select_autoescape(['html', 'xml']))
        template = env.from_string(TEMPLATES_EMPAQUETADOS[template_name])
        html_content = template.render(context)
        return HTML(string=html_content).write_pdf()
    except Exception as e:
        print(f"ERROR GENERANDO PDF PH: {str(e)}")
        # Fallback simple
        return HTML(string=f"<h1>Error generando reporte</h1><p>{str(e)}</p>").write_pdf()

def get_historial_cuenta_ph_detailed(db: Session, empresa_id: int, unidad_id: int = None, propietario_id: int = None, fecha_inicio: date = None, fecha_fin: date = None):
    # 1. Calcular Saldo Anterior
    saldo_anterior = 0
    if fecha_inicio:
        from datetime import timedelta
        fecha_corte_saldo = fecha_inicio - timedelta(days=1)
        # Reusamos la logica existente que acumula todo hasta una fecha
        # OJO: get_historial_cuenta_unidad filtra movimientos por fecha, asi que debemos 
        # pedirle todo hasta fecha_corte.
        
        # Para eficiencia, simplemente sumamos movimientos previos al inicio
        # Clonamos logica basica de saldo:
        # (Esto es un poco pesado pero seguro)
        state_prev = get_historial_cuenta_unidad(
            db, unidad_id, empresa_id, 
            fecha_inicio=None, # Desde el principio de los tiempos
            fecha_fin=fecha_corte_saldo,
            propietario_id=propietario_id
        )
        saldo_anterior = state_prev['saldo_actual']
    
    # 2. Obtener Documentos del Periodo
    query = db.query(Documento).options(
        joinedload(Documento.tipo_documento),
        joinedload(Documento.unidad_ph),
        selectinload(Documento.movimientos).joinedload(MovimientoContable.cuenta)
    ).filter(
        Documento.empresa_id == empresa_id,
        Documento.estado.in_(['ACTIVO', 'PROCESADO'])
    )

    if unidad_id: query = query.filter(Documento.unidad_ph_id == unidad_id)
    if propietario_id: query = query.filter(Documento.beneficiario_id == propietario_id)
    
    if fecha_inicio: query = query.filter(Documento.fecha >= fecha_inicio)
    if fecha_fin: query = query.filter(Documento.fecha <= fecha_fin)
    
    docs = query.order_by(Documento.fecha.asc(), Documento.id.asc()).all()
    
    # 3. Procesar Transacciones Detalladas
    transacciones = []
    saldo_acumulado = saldo_anterior
    
    cuentas_cxc_ids = cartera_service.get_cuentas_especiales_ids(db, empresa_id, 'cxc')
    
    for doc in docs:
        # Calcular Total Documento (Impacto en Cartera)
        debito_cxc = 0
        credito_cxc = 0
        
        # Identificar Sub-Items (Conceptos que explican el documento)
        sub_items = []
        observacion_header = doc.observaciones or ""
        
        is_factura = False
        
        # Analisis de Movimientos
        for mov in doc.movimientos:
            if mov.cuenta_id in cuentas_cxc_ids:
                debito_cxc += mov.debito
                credito_cxc += mov.credito
            else:
                # Si NO es cuenta de cartera, es la contrapartida (Ingreso o Caja)
                # Esto es lo que queremos mostrar en el detalle
                
                # Para facturas (CXC Debito > 0), mostramos movimientos CRÉDITO (Ingresos)
                # Para recibos (CXC Credito > 0), mostramos movimientos DÉBITO (Caja) o simplificamos
                
                # Guardamos todos temporalmente
                sub_items.append({
                    "concepto": mov.concepto,
                    "valor_debito": mov.debito,
                    "valor_credito": mov.credito,
                    "cuenta": mov.cuenta.nombre if mov.cuenta else ""
                })

        impacto_neto = debito_cxc - credito_cxc
        
        # Filtrar Sub-items visuales
        visual_sub_items = []
        if impacto_neto > 0 and len(sub_items) > 0: # ES UNA FACTURA (Cargo)
            is_factura = True
            # Mostrar Ingresos (Creditos)
            for sub in sub_items:
                if sub['valor_credito'] > 0:
                    visual_sub_items.append({
                        "concepto": sub['concepto'],
                        "valor": sub['valor_credito']
                    })
        elif impacto_neto < 0: # ES UN PAGO (Abono)
            # Generalmente no desglosamos recibos, o mostramos "Pago Caja..."
            det_obs = doc.observaciones if doc.observaciones else ""
            observacion_header = f"Pago Recibido - {det_obs}" if det_obs else "Pago Recibido"
            # Opcional: Mostrar si hubo descuentos o multiples medios pago
        
        # Actualizar Saldo
        saldo_acumulado += impacto_neto
        
        transacciones.append({
            "fecha": doc.fecha.strftime('%Y-%m-%d'),
            "documento": f"{doc.tipo_documento.codigo}-{doc.numero}",
            "observacion_header": observacion_header,
            "unidad_codigo": doc.unidad_ph.codigo if doc.unidad_ph else "", # NEW
            "sub_items": visual_sub_items,
            "debito": impacto_neto if impacto_neto > 0 else 0,
            "credito": abs(impacto_neto) if impacto_neto < 0 else 0,
            "saldo_acumulado": saldo_acumulado
        })
        
    return {
        "transacciones": transacciones,
        "saldo_anterior": saldo_anterior,
        "saldo_final": saldo_acumulado,
        "fecha_inicio": fecha_inicio.strftime('%Y-%m-%d') if fecha_inicio else "Inicio",
        "fecha_fin": fecha_fin.strftime('%Y-%m-%d') if fecha_fin else date.today().strftime('%Y-%m-%d')
    }
