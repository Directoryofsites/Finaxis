from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from app.models.remision import Remision, RemisionDetalle
from app.models.producto import StockBodega, Producto
from app.models import Tercero, Bodega
from app.schemas import remision as schemas
from datetime import datetime

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

def get_remisiones(db: Session, empresa_id: int, skip: int=0, limit: int=100):
    query = db.query(Remision).filter(Remision.empresa_id == empresa_id).order_by(Remision.numero.desc())
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    # Enrich simple
    for r in items:
        r.tercero_nombre = r.tercero.razon_social if r.tercero else "N/A"
        r.bodega_nombre = r.bodega.nombre if r.bodega else "N/A"
    return {"total": total, "remisiones": items}
