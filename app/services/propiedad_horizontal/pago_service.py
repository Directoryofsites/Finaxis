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

    return new_doc

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
