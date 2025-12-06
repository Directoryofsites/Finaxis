from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from app.models.remision import Remision, RemisionDetalle
from app.models.producto import StockBodega, Producto
from app.models import Tercero, Bodega
from app.schemas import remision as schemas
from datetime import datetime, date

def create_remision(db: Session, remision_in: schemas.RemisionCreate, user_id: int, empresa_id: int):
    # 1. Validar Bodega
    bodega = db.query(Bodega).filter(Bodega.id == remision_in.bodega_id, Bodega.empresa_id == empresa_id).first()
    if not bodega:
        raise HTTPException(status_code=404, detail="La bodega no existe.")

    # 2. Consecutivo
    ultimo_numero = db.query(func.max(Remision.numero)).filter(Remision.empresa_id == empresa_id).scalar() or 0
    nuevo_numero = ultimo_numero + 1

    # 3. Crear Remisión en Estado BORRADOR
    # (No afecta stock todavía)
    db_remision = Remision(
        empresa_id=empresa_id,
        numero=nuevo_numero,
        fecha=remision_in.fecha,
        fecha_vencimiento=remision_in.fecha_vencimiento,
        tercero_id=remision_in.tercero_id,
        bodega_id=remision_in.bodega_id,
        observaciones=remision_in.observaciones,
        usuario_id=user_id,
        estado='BORRADOR'
    )
    db.add(db_remision)
    db.flush()

    # 4. Detalles
    for det in remision_in.detalles:
        db_detalle = RemisionDetalle(
            remision_id=db_remision.id,
            producto_id=det.producto_id,
            cantidad_solicitada=det.cantidad_solicitada,
            cantidad_pendiente=det.cantidad_solicitada, # Inicialmente todo está pendiente
            cantidad_facturada=0,
            precio_unitario=det.precio_unitario
        )
        db.add(db_detalle)
    
    db.commit()
    db.refresh(db_remision)
    return db_remision

def aprobar_remision(db: Session, remision_id: int, empresa_id: int):
    """
    Cambia estado a APROBADA y COMPROMETE el stock.
    Valida disponibilidad.
    """
    remision = db.query(Remision).filter(Remision.id == remision_id, Remision.empresa_id == empresa_id).first()
    if not remision:
        raise HTTPException(status_code=404, detail="Remisión no encontrada.")
        
    if remision.estado != 'BORRADOR':
        raise HTTPException(status_code=400, detail="Solo se pueden aprobar remisiones en Borrador.")

    # Validar Disponibilidad y Comprometer Stock
    for det in remision.detalles:
        stock_record = db.query(StockBodega).filter(
            StockBodega.producto_id == det.producto_id,
            StockBodega.bodega_id == remision.bodega_id
        ).with_for_update().first() # Importante: Bloqueo de fila
        
        if not stock_record:
            # Si no existe registro de stock, asumimos 0
            stock_record = StockBodega(
                producto_id=det.producto_id,
                bodega_id=remision.bodega_id,
                stock_actual=0,
                stock_comprometido=0
            )
            db.add(stock_record)
        
        stock_disponible = stock_record.stock_actual - stock_record.stock_comprometido
        if stock_disponible < det.cantidad_solicitada:
             # Aquí decidimos si ser estrictos o permitir negativo.
             # Para "Profesionalidad", deberíamos alertar, pero permitiremos aprobar con warning si el usuario lo decide (TODO).
             # Por ahora, estricto: No deja aprobar si no hay stock LIBRE.
             producto = db.query(Producto).get(det.producto_id)
             raise HTTPException(
                 status_code=409, 
                 detail=f"Stock insuficiente para reservar {producto.nombre}. Disponible Real: {stock_disponible}"
             )
             
        # Comprometer
        stock_record.stock_comprometido += det.cantidad_solicitada
    
    remision.estado = 'APROBADA'
    db.commit()
    db.refresh(remision)
    return remision

def anular_remision(db: Session, remision_id: int, empresa_id: int):
    """Liberar Stock Comprometido"""
    remision = db.query(Remision).filter(Remision.id == remision_id, Remision.empresa_id == empresa_id).first()
    if not remision: return
    
    if remision.estado in ['ANULADA', 'FACTURADA_TOTAL']:
        raise HTTPException(status_code=400, detail="No se puede anular en el estado actual.")

    # Solo si estaba aprobada o parcial liberamos lo pendiente
    if remision.estado in ['APROBADA', 'FACTURADA_PARCIAL']:
        for det in remision.detalles:
            if det.cantidad_pendiente > 0:
                stock_record = db.query(StockBodega).filter(
                    StockBodega.producto_id == det.producto_id,
                    StockBodega.bodega_id == remision.bodega_id
                ).first()
                if stock_record:
                    stock_record.stock_comprometido -= det.cantidad_pendiente
                    # Safety check
                    if stock_record.stock_comprometido < 0: stock_record.stock_comprometido = 0
                    
    remision.estado = 'ANULADA'
    db.commit()
    return remision

def get_remisiones(
    db: Session, 
    empresa_id: int, 
    skip: int = 0, 
    limit: int = 100,
    numero: int = None,
    tercero_id: int = None,
    estado: str = None,
    fecha_inicio: date = None,
    fecha_fin: date = None
):
    query = db.query(Remision).filter(Remision.empresa_id == empresa_id)
    
    if numero:
        query = query.filter(Remision.numero == numero)
    if tercero_id:
        query = query.filter(Remision.tercero_id == tercero_id)
    if estado and estado != 'TODOS':
        query = query.filter(Remision.estado == estado)
    if fecha_inicio:
        query = query.filter(Remision.fecha >= fecha_inicio)
    if fecha_fin:
        query = query.filter(Remision.fecha <= fecha_fin)

    query = query.order_by(Remision.numero.desc())
    
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    # Enrich simple
    for r in items:
        r.tercero_nombre = r.tercero.razon_social if r.tercero else "N/A"
        r.bodega_nombre = r.bodega.nombre if r.bodega else "N/A"
        for d in r.detalles:
            d.producto_nombre = d.producto.nombre if d.producto else "Desconocido"
            d.producto_codigo = d.producto.codigo if d.producto else "N/A"
    return {"total": total, "remisiones": items}

def get_remision_by_id(db: Session, remision_id: int, empresa_id: int):
    remision = db.query(Remision).filter(Remision.id == remision_id, Remision.empresa_id == empresa_id).first()
    if remision:
        remision.tercero_nombre = remision.tercero.razon_social if remision.tercero else "N/A"
        remision.bodega_nombre = remision.bodega.nombre if remision.bodega else "N/A"
        for d in remision.detalles:
            d.producto_nombre = d.producto.nombre if d.producto else "Desconocido"
            d.producto_codigo = d.producto.codigo if d.producto else "N/A"
    return remision

def procesar_facturacion_remision(db: Session, remision_id: int, items_facturados: list):
    """
    Actualiza la remisión tras generar una factura.
    - Reduce cantidad pendiente.
    - Aumenta cantidad facturada.
    - Libera stock comprometido (ya que la factura descarga el físico).
    - Actualiza estado.
    """
    remision = db.query(Remision).get(remision_id)
    if not remision: return

    todos_cerrados = True
    
    # Mapa de items facturados para acceso rápido: {producto_id: cantidad}
    facturado_map = {}
    for item in items_facturados:
        facturado_map[item.producto_id] = facturado_map.get(item.producto_id, 0) + item.cantidad

    for det in remision.detalles:
        cant_facturar = facturado_map.get(det.producto_id, 0)
        
        if cant_facturar > 0:
            # 1. Ajustar cantidades
            det.cantidad_facturada += cant_facturar
            det.cantidad_pendiente -= cant_facturar
            if det.cantidad_pendiente < 0: det.cantidad_pendiente = 0 # Safety
            
            # 2. Liberar Stock Comprometido
            # NOTA: La factura ya redujo Stock Físico (stock_actual).
            # Aquí solo debemos quitar la reserva (stock_comprometido).
            stock_record = db.query(StockBodega).filter(
                StockBodega.producto_id == det.producto_id,
                StockBodega.bodega_id == remision.bodega_id
            ).first()
            
            if stock_record:
                stock_record.stock_comprometido -= cant_facturar
                if stock_record.stock_comprometido < 0: stock_record.stock_comprometido = 0
                
            # Consumimos del mapa para evitar doble conteo si hubiera items repetidos (raro)
            facturado_map[det.producto_id] = 0

        if det.cantidad_pendiente > 0:
            todos_cerrados = False

    # 3. Actualizar Estado
    if todos_cerrados:
        remision.estado = 'FACTURADA_TOTAL'
    else:
        remision.estado = 'FACTURADA_PARCIAL'
    
    # No hacemos commit aquí, esperamos al commit de la transacción principal de facturación


def update_remision(db: Session, remision_id: int, remision_in: schemas.RemisionCreate, empresa_id: int):
    """
    Permite editar una remisión SIEMPRE QUE esté en estado BORRADOR.
    Estrategia: Actualizar cabecera y Reemplazar detalles.
    """
    remision = db.query(Remision).filter(Remision.id == remision_id, Remision.empresa_id == empresa_id).first()
    if not remision:
        raise HTTPException(status_code=404, detail="Remisión no encontrada.")

    if remision.estado != 'BORRADOR':
        raise HTTPException(status_code=400, detail="Solo se pueden editar remisiones en estado BORRADOR.")

    # 1. Actualizar Cabecera
    remision.fecha = remision_in.fecha
    remision.fecha_vencimiento = remision_in.fecha_vencimiento
    remision.tercero_id = remision_in.tercero_id
    remision.bodega_id = remision_in.bodega_id
    remision.observaciones = remision_in.observaciones
    
    # 2. Reemplazar Detalles (Borrar y Crear)
    # Como es borrador, no hay stock comprometido ni facturado, es seguro borrar.
    db.query(RemisionDetalle).filter(RemisionDetalle.remision_id == remision_id).delete()
    
    for det in remision_in.detalles:
        db_detalle = RemisionDetalle(
            remision_id=remision.id,
            producto_id=det.producto_id,
            cantidad_solicitada=det.cantidad_solicitada,
            cantidad_pendiente=det.cantidad_solicitada,
            cantidad_facturada=0,
            precio_unitario=det.precio_unitario
        )
        db.add(db_detalle)

    db.commit()
    db.refresh(remision)
    return remision

def get_detalles_reporte(db: Session, empresa_id: int, filtro_estado: str = None, tercero_id: int = None):
    """
    Retorna lista plana de items para reporte.
    Filtros combinables:
    - filtro_estado: 'PENDIENTES' (pend > 0, no anulada), o estado especifico (ej: 'APROBADA').
    - tercero_id: Filtra por cliente.
    """
    query = db.query(RemisionDetalle).join(Remision).filter(Remision.empresa_id == empresa_id)
    
    # 1. Filtro por Cliente
    if tercero_id:
        query = query.filter(Remision.tercero_id == tercero_id)
        
    # 2. Filtro por Estado
    if filtro_estado:
        if filtro_estado == 'PENDIENTES':
            query = query.filter(RemisionDetalle.cantidad_pendiente > 0, Remision.estado != 'ANULADA')
        elif filtro_estado != 'TODOS': # Si es un estado especifico (BORRADOR, APROBADA, etc)
            query = query.filter(Remision.estado == filtro_estado)
    
    results = query.all()
    
    reporte = []
    for det in results:
        # Lazy load warning...
        rem = det.remision
        reporte.append({
            "remision_numero": rem.numero,
            "fecha": rem.fecha,
            "tercero_nombre": rem.tercero.razon_social if rem.tercero else "N/A",
            "producto_codigo": det.producto.codigo if det.producto else "N/A",
            "producto_nombre": det.producto.nombre if det.producto else "Desconocido",
            "cantidad_solicitada": det.cantidad_solicitada,
            "cantidad_facturada": det.cantidad_facturada,
            "cantidad_pendiente": det.cantidad_pendiente,
            "estado_remision": rem.estado
        })
    return reporte



>>>>>>> origin/pc2-cambios-pendientes
