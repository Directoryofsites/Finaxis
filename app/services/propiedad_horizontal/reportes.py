from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import text
from typing import List, Optional
from datetime import date
from app.models.documento import Documento
from app.models.movimiento_contable import MovimientoContable
from app.models.propiedad_horizontal.unidad import PHUnidad
from app.models.propiedad_horizontal.concepto import PHConcepto
from app.models.tercero import Tercero
from app.models.tipo_documento import TipoDocumento

def get_movimientos_ph_report(
    db: Session,
    empresa_id: int,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    unidad_id: Optional[int] = None,
    propietario_id: Optional[int] = None,
    tipo_documento_id: Optional[int] = None,
    concepto_id: Optional[int] = None,
    numero_doc: Optional[str] = None,
    tipo_movimiento: Optional[str] = None # 'FACTURAS', 'RECIBOS', 'TODOS'
):
    """
    Genera un reporte detallado de movimientos para PH.
    Permite filtrar por múltiples criterios.
    """
    from app.models.propiedad_horizontal.configuracion import PHConfiguracion
    
    # Base Query: Movimientos Contables enlazados a Documentos
    # Seleccionamos campos relevantes
    query = db.query(
        Documento.fecha,
        TipoDocumento.codigo.label("tipo_doc"),
        Documento.numero,
        PHUnidad.codigo.label("unidad"),
        Tercero.razon_social.label("propietario"),
        MovimientoContable.concepto.label("detalle"),
        MovimientoContable.debito,
        MovimientoContable.credito,
        Documento.observaciones
    ).join(Documento, MovimientoContable.documento_id == Documento.id)\
     .join(TipoDocumento, Documento.tipo_documento_id == TipoDocumento.id)\
     .outerjoin(PHUnidad, Documento.unidad_ph_id == PHUnidad.id)\
     .outerjoin(Tercero, Documento.beneficiario_id == Tercero.id)

    # --- FILTRO MAESTRO: SOLO CUENTAS POR COBRAR (CARTERA) ---
    # Para el "Extracto de Cuenta", solo nos interesan los movimientos de las cuentas 13xx (Cartera)
    # Obtenemos las cuentas configuradas en PHConfiguracion y/o las cuentas de CXC de los Tipos Doc.
    
    config = db.query(PHConfiguracion).filter(PHConfiguracion.empresa_id == empresa_id).first()
    ids_cartera = set()
    
    if config:
        if config.cuenta_cartera_id: ids_cartera.add(config.cuenta_cartera_id)
        # if config.cuenta_intereses_id: ids_cartera.add(config.cuenta_intereses_id) # ELIMINADO: Campo no existe
        
        # Tambien buscamos cuentas cxc de los tipos de documento usados en PH
        if config.tipo_documento_factura_id:
             td = db.query(TipoDocumento).filter(TipoDocumento.id == config.tipo_documento_factura_id).first()
             if td and td.cuenta_debito_cxc_id: ids_cartera.add(td.cuenta_debito_cxc_id)
             
    # Si no hay cuentas configuradas, intentamos fallback genérico a cuentas que empiecen por '13'
    # pero es mas seguro usar las configuradas para no traer ruido.
    
    # Para asegurar que traemos TODO lo de cartera, vamos a filtrar donde la cuenta sea de tipo "Deudores" (13)
    # OJO: Esto requiere joinear con PlanCuenta.
    
    from app.models.plan_cuenta import PlanCuenta
    query = query.join(PlanCuenta, MovimientoContable.cuenta_id == PlanCuenta.id)
    query = query.filter(PlanCuenta.codigo.like("13%")) # Convención estándar Colombia
    
    # ---------------------------------------------------------

    # Filtros Obligatorios
    query = query.filter(Documento.empresa_id == empresa_id)
    query = query.filter(Documento.estado.in_(['ACTIVO', 'PROCESADO']))
    # --- CORRECCIÓN: Filtrar solo documentos de PH (vinculados a una unidad) ---
    query = query.filter(Documento.unidad_ph_id != None)

    # Filtros Opcionales
    if fecha_desde:
        query = query.filter(Documento.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Documento.fecha <= fecha_hasta)
    
    if unidad_id:
        query = query.filter(Documento.unidad_ph_id == unidad_id)
    
    if propietario_id:
        query = query.filter(Documento.beneficiario_id == propietario_id)
    
    if tipo_documento_id:
        query = query.filter(Documento.tipo_documento_id == tipo_documento_id)
    
    if numero_doc:
        from sqlalchemy import cast, String
        query = query.filter(cast(Documento.numero, String).ilike(f"%{numero_doc}%"))

    # Filtro por Tipo de Movimiento (Facturas vs Recibos)
    if tipo_movimiento and tipo_movimiento in ['FACTURAS', 'RECIBOS']:
        
        if config:
            if tipo_movimiento == 'FACTURAS':
                if config.tipo_documento_factura_id:
                    query = query.filter(Documento.tipo_documento_id == config.tipo_documento_factura_id)
            elif tipo_movimiento == 'RECIBOS':
                # Nota: Recibos no siempre tienen ID unico en config, podria ser cualquier comprobante
                # Mejor filtrar por naturaleza: Facturas (Debito > 0), Recibos (Credito > 0) dentro de Cartera
                if tipo_movimiento == 'FACTURAS':
                     query = query.filter(MovimientoContable.debito > 0)
                elif tipo_movimiento == 'RECIBOS':
                     query = query.filter(MovimientoContable.credito > 0)


    # Filtro Especial por Concepto de PH -> AHORA FILTRA POR DETALLE DE TEXTO O CONCEPTOS
    if concepto_id:
        # Si el usuario filtra por concepto, buscamos en el texto del movimiento
        # ya que ahora estamos filtrando solo cuentas de cartera.
        ph_concepto = db.query(PHConcepto).filter(PHConcepto.id == concepto_id).first()
        if ph_concepto:
             query = query.filter(MovimientoContable.concepto.ilike(f"%{ph_concepto.nombre}%"))

    # Ordenamiento: Ascendente para poder calcular saldos correctamente (opcional)
    # Pero el usuario pidió ver historial, usualmente Descendente. 
    # Para saldos acumulados en frontend, es mejor Ascendente y luego reversear, o hacerlo desc desde saldo final.
    # Mantendremos DESC como estaba.
    query = query.order_by(Documento.fecha.desc(), Documento.id.desc())

    results = query.all()

    # Formatear salida
    reporte = []
    for row in results:
        reporte.append({
            "fecha": row.fecha,
            "tipo_doc": row.tipo_doc,
            "numero": row.numero,
            "unidad": row.unidad or "N/A",
            "propietario": row.propietario or "N/A",
            "detalle": row.detalle,  # Concepto del movimiento
            "observaciones": row.observaciones, # Observaciones del documento general
            "debito": float(row.debito or 0),
            "credito": float(row.credito or 0)
        })
    
    return reporte

def get_cartera_edades(db: Session, empresa_id: int, fecha_corte: date = None):
    """
    Calcula la cartera clasificada por edades (vencimiento) para todas las unidades.
    Rangos: Corriente (0-30), 31-60, 61-90, >90.
    Soporta Fecha de Corte (Historico) y Prelación de Pagos.
    """
    from datetime import date
    from app.services.propiedad_horizontal import pago_service
    from app.models.propiedad_horizontal.unidad import PHUnidad
    from app.models.documento import Documento, MovimientoContable
    from sqlalchemy.orm import joinedload, selectinload
    
    # 1. Obtener Unidades
    unidades_db = db.query(PHUnidad).options(joinedload(PHUnidad.propietario_principal))\
        .filter(PHUnidad.empresa_id == empresa_id).all()
        
    mapa_unidades = {u.id: u for u in unidades_db}
    
    # 2. Obtener TODOS los documentos relevantes (para poder simular)
    # Optimización: Un solo query grande ordenado por Unidad
    docs = db.query(Documento).options(
        selectinload(Documento.movimientos).joinedload(MovimientoContable.cuenta),
        joinedload(Documento.tipo_documento),
        joinedload(Documento.unidad_ph)
    ).filter(
        Documento.empresa_id == empresa_id,
        Documento.unidad_ph_id != None,
        Documento.estado.in_(['ACTIVO', 'PROCESADO'])
    ).order_by(Documento.unidad_ph_id, Documento.fecha.asc(), Documento.id.asc()).all()
    
    # Agrupar docs por unidad
    from collections import defaultdict
    docs_por_unidad = defaultdict(list)
    for d in docs:
        docs_por_unidad[d.unidad_ph_id].append(d)
        
    pendientes = []
    
    # 3. Simular por Unidad
    for unidad_id, unidad_docs in docs_por_unidad.items():
        # Ejecutar simulación con corte
        pending_current, _, pending_snapshot, saf_current, saf_snapshot = pago_service._simular_cronologia_pagos(
            db, unidad_docs, empresa_id, fecha_corte_snapshot=fecha_corte
        )
        
        # Determinar qué set de datos usar
        use_snapshot = fecha_corte is not None
        
        active_debts = pending_snapshot if use_snapshot and pending_snapshot is not None else pending_current
        active_saf = saf_snapshot if use_snapshot and pending_snapshot is not None else saf_current
        
        # Si fecha_corte es futuro o hoy, snapshot podría ser None si no hay docs futuros, 
        # en cuyo caso pending_current es lo correcto.
        if use_snapshot and pending_snapshot is None:
             # Fallback
             active_debts = pending_current
             active_saf = saf_current
        
        # Procesar Deudas
        u_info = mapa_unidades.get(unidad_id)
        u_codigo = u_info.codigo if u_info else "N/A"
        
        for d in active_debts:
            pendientes.append({
                'id': d.get('doc_id'),
                'fecha': d['fecha'].isoformat() if isinstance(d['fecha'], date) else d['fecha'],
                'saldo_pendiente': d['saldo'],
                'unidad_codigo': u_codigo,
                'tipo': d['tipo']
            })
            
        # Procesar Saldo a Favor (Como saldo negativo corriente)
        if active_saf > 0.001:
            pendientes.append({
                'id': 0,
                'fecha': fecha_corte.isoformat() if fecha_corte else date.today().isoformat(),
                'saldo_pendiente': -active_saf,
                'unidad_codigo': u_codigo,
                'tipo': 'ANTICIPO'
            })

    
    
    # Reutilizar unidades_db para mapa por codigo (Legacy loop support)
    mapa_codigo = {}
    for u in unidades_db:
        nombre_prop = u.propietario_principal.razon_social if u.propietario_principal else "Sin Propietario"
        mapa_codigo[u.codigo] = {
            "id": u.id,
            "propietario_nombre": nombre_prop
        }
        
    # 3. Agrupacion
    grupos = {} # codigo_unidad -> Objeto CarteraItem
    
    hoy = fecha_corte if fecha_corte else date.today()
    
    total_corriente = 0
    total_0_30 = 0
    total_31_60 = 0
    total_61_90 = 0
    total_mas_90 = 0
    total_general = 0

    for item in pendientes:
        # item es un dict: { 'id', 'fecha': ISOStr, 'saldo_pendiente', 'unidad_codigo', 'tipo' }
        
        saldo = item['saldo_pendiente']
        unidad_codigo = item['unidad_codigo']
        
        # Parse timestamp safely
        try:
             fecha_doc = date.fromisoformat(item['fecha'])
        except:
             # Fallback if already date obj or other format
             fecha_doc = item['fecha']
             if isinstance(fecha_doc, str):
                  fecha_doc = date.fromisoformat(fecha_doc[:10])

        
        # Inicializar grupo si no existe
        if unidad_codigo not in grupos:
            info_u = mapa_codigo.get(unidad_codigo, {"id": 0, "propietario_nombre": "Desconocido"})
            grupos[unidad_codigo] = {
                "unidad_id": info_u['id'],
                "unidad_codigo": unidad_codigo,
                "propietario_nombre": info_u['propietario_nombre'],
                "saldo_corriente": 0,
                "edad_0_30": 0,
                "edad_31_60": 0,
                "edad_61_90": 0,
                "edad_mas_90": 0,
                "saldo_total": 0
            }
            
        bucket = grupos[unidad_codigo]
        
        if saldo < 0:
            # Saldo a favor -> Resta a corriente
            bucket["saldo_corriente"] += saldo
            total_corriente += saldo
        else:
            # Deuda -> Calcular edad
            dias = (hoy - fecha_doc).days
            
            if dias <= 30:
                bucket["edad_0_30"] += saldo
                total_0_30 += saldo
            elif dias <= 60:
                bucket["edad_31_60"] += saldo
                total_31_60 += saldo
            elif dias <= 90:
                bucket["edad_61_90"] += saldo
                total_61_90 += saldo
            else:
                bucket["edad_mas_90"] += saldo
                total_mas_90 += saldo
                
        bucket["saldo_total"] += saldo
        total_general += saldo

    # 4. Formatear Respuesta
    items_lista = list(grupos.values())
    # Ordenar por Codigo Unidad
    items_lista.sort(key=lambda x: x['unidad_codigo'])
    
    return {
        "items": items_lista,
        "total_corriente": total_corriente,
        "total_0_30": total_0_30,
        "total_31_60": total_31_60,
        "total_61_90": total_61_90,
        "total_mas_90": total_mas_90,
        "total_general": total_general
    }

def get_reporte_saldos(
    db: Session, 
    empresa_id: int, 
    fecha_corte: Optional[date] = None,
    unidad_id: Optional[int] = None,
    propietario_id: Optional[int] = None,
    torre_id: Optional[int] = None,
    concepto_busqueda: Optional[str] = None
):
    """
    Reporte de Saldos (Balance General) detallado.
    Calcula la deuda actual o histórica de cada unidad y permite filtrar.
    """
    from app.services.propiedad_horizontal import pago_service
    from datetime import date
    
    # 1. Obtener Unidades (Filtrado Previo)
    query_unidades = db.query(PHUnidad).options(
        joinedload(PHUnidad.propietario_principal),
        joinedload(PHUnidad.torre)
    ).filter(PHUnidad.empresa_id == empresa_id)
    
    if unidad_id:
        query_unidades = query_unidades.filter(PHUnidad.id == unidad_id)
    if propietario_id:
        query_unidades = query_unidades.filter((PHUnidad.propietario_principal_id == propietario_id))
    if torre_id:
        query_unidades = query_unidades.filter(PHUnidad.torre_id == torre_id)
        
    unidades_db = query_unidades.all()
    
    # 2. Obtener Documentos (Optimización: Traer todo y filtrar en memoria o traer por lotes?)
    # Para consistencia con 'edades', traemos todo lo de la empresa.
    # Si la empresa es muy grande, esto podría optimizarse filtrando docs por unidad_ids seleccionados.
    unidades_ids = [u.id for u in unidades_db]
    if not unidades_ids:
        return {"items": [], "total_general": 0}

    docs = db.query(Documento).options(
        selectinload(Documento.movimientos).joinedload(MovimientoContable.cuenta),
        joinedload(Documento.tipo_documento),
        joinedload(Documento.unidad_ph)
    ).filter(
        Documento.empresa_id == empresa_id,
        Documento.unidad_ph_id.in_(unidades_ids),
        Documento.estado.in_(['ACTIVO', 'PROCESADO'])
    ).order_by(Documento.unidad_ph_id, Documento.fecha.asc(), Documento.id.asc()).all()

    # Agrupar docs por unidad
    from collections import defaultdict
    docs_por_unidad = defaultdict(list)
    for d in docs:
        docs_por_unidad[d.unidad_ph_id].append(d)

    reporte_items = []
    total_general = 0

    # 3. Simulación y Filtrado
    hoy = fecha_corte if fecha_corte else date.today()

    for u in unidades_db:
        udocs = docs_por_unidad.get(u.id, [])
        
        # Simular
        pending_current, _, pending_snapshot, saf_current, saf_snapshot = pago_service._simular_cronologia_pagos(
            db, udocs, empresa_id, fecha_corte_snapshot=fecha_corte
        )
        
        use_snapshot = fecha_corte is not None
        active_debts = pending_snapshot if use_snapshot and pending_snapshot is not None else pending_current
        active_saf = saf_snapshot if use_snapshot and pending_snapshot is not None else saf_current
        
        # Fallback snapshot
        if use_snapshot and pending_snapshot is None:
            active_debts = pending_current
            active_saf = saf_current
            
        # Filtrado por Concepto (Texto)
        deudas_filtradas = []
        saldo_unidad = 0
        
        for d in active_debts:
            cumple_concepto = True
            if concepto_busqueda and concepto_busqueda.strip():
                # Busqueda case-insensitive flexible
                if concepto_busqueda.lower() not in d['concepto'].lower():
                    cumple_concepto = False
            
            if cumple_concepto:
                deudas_filtradas.append(d)
                saldo_unidad += d['saldo']
        
        # Manejo de SAF (Solo si no estamos filtrando concepto especifico, O si el saf aplica?)
        # SAF es "Anticipo", no tiene concepto especifico usualmente.
        # Si el usuario busca "Administracion", ¿queremos ver el anticipo? 
        # Probablemente NO, porque el anticipo es generico.
        # PERO, contablemente, el saldo de la unidad es Neto.
        # Decision: Si hay filtro de concepto, IGNORAMOS SAF (mostramos solo deuda de ese concepto).
        # Si NO hay filtro de concepto, restamos SAF.
        
        saf_aplicable = 0
        if not concepto_busqueda:
            saf_aplicable = active_saf
            saldo_unidad -= saf_aplicable
            
        # Si tiene saldo o movimientos (incluso si saldo es 0, si queremos ver historial... pero es reporte de SALDOS)
        # Mostramos si saldo != 0
        if abs(saldo_unidad) > 0.01:
            total_general += saldo_unidad
            
            # Formatear items de detalle
            detalles_str = []
            for d in deudas_filtradas:
                detalles_str.append(f"{d['concepto']} (${d['saldo']:,.0f})")
            
            # Resumir detalle si es muy largo
            detalle_final = "; ".join(detalles_str[:3])
            if len(detalles_str) > 3:
                detalle_final += f" (+{len(detalles_str)-3} más)"
            
            if saf_aplicable > 0:
                detalle_final += f" [Anticipo: -${saf_aplicable:,.0f}]"

            nombre_prop = u.propietario_principal.razon_social if u.propietario_principal else "Sin Propietario"
            nombre_torre = u.torre.nombre if u.torre else "-"

            reporte_items.append({
                "unidad_id": u.id,
                "unidad_codigo": u.codigo,
                "propietario_nombre": nombre_prop,
                "torre_nombre": nombre_torre,
                "saldo": saldo_unidad,
                "detalle": detalle_final,
                "antiguedad_promedio": 0, # TODO: Calcular si se requiere, por ahora simple
                "conceptos_count": len(deudas_filtradas)
            })

    # Ordenar por Torre, luego Unidad
    reporte_items.sort(key=lambda x: (x['torre_nombre'], x['unidad_codigo']))

    return {
        "items": reporte_items,
        "total_general": total_general,
        "fecha_corte": hoy.isoformat()
    }
