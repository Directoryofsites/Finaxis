from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from app.models.cotizacion import Cotizacion, CotizacionDetalle
from app.models import Tercero, Bodega, Producto
from app.schemas import cotizacion as schemas
from datetime import date

def create_cotizacion(db: Session, cotizacion_in: schemas.CotizacionCreate, user_id: int, empresa_id: int):
    # 1. Consecutivo
    ultimo_numero = db.query(func.max(Cotizacion.numero)).filter(Cotizacion.empresa_id == empresa_id).scalar() or 0
    nuevo_numero = ultimo_numero + 1

    # 2. Calcular Total Estimado
    total = sum(det.cantidad * det.precio_unitario for det in cotizacion_in.detalles)

    # 3. Crear Cotización
    db_cotizacion = Cotizacion(
        empresa_id=empresa_id,
        numero=nuevo_numero,
        fecha=cotizacion_in.fecha,
        fecha_vencimiento=cotizacion_in.fecha_vencimiento,
        tercero_id=cotizacion_in.tercero_id,
        bodega_id=cotizacion_in.bodega_id, # Opcional
        observaciones=cotizacion_in.observaciones,
        usuario_id=user_id,
        estado='BORRADOR',
        total_estimado=total
    )
    db.add(db_cotizacion)
    db.flush()

    # 4. Detalles
    for det in cotizacion_in.detalles:
        db_detalle = CotizacionDetalle(
            cotizacion_id=db_cotizacion.id,
            producto_id=det.producto_id,
            cantidad=det.cantidad,
            precio_unitario=det.precio_unitario,
            cantidad_facturada=0
        )
        db.add(db_detalle)
    
    db.commit()
    db.refresh(db_cotizacion)
    return db_cotizacion

def get_cotizaciones(
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
    query = db.query(Cotizacion).filter(Cotizacion.empresa_id == empresa_id)
    
    if numero:
        query = query.filter(Cotizacion.numero == numero)
    if tercero_id:
        query = query.filter(Cotizacion.tercero_id == tercero_id)
    if estado and estado != 'TODOS':
        query = query.filter(Cotizacion.estado == estado)
    if fecha_inicio:
        query = query.filter(Cotizacion.fecha >= fecha_inicio)
    if fecha_fin:
        query = query.filter(Cotizacion.fecha <= fecha_fin)

    query = query.order_by(Cotizacion.numero.desc())
    
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    
    # Enrich
    for c in items:
        c.tercero_nombre = c.tercero.razon_social if c.tercero else "N/A"
        c.bodega_nombre = c.bodega.nombre if c.bodega else "N/A"
        
    return {"total": total, "cotizaciones": items}

def get_cotizacion_by_id(db: Session, cotizacion_id: int, empresa_id: int):
    cotizacion = db.query(Cotizacion).filter(Cotizacion.id == cotizacion_id, Cotizacion.empresa_id == empresa_id).first()
    if cotizacion:
        cotizacion.tercero_nombre = cotizacion.tercero.razon_social if cotizacion.tercero else "N/A"
        cotizacion.bodega_nombre = cotizacion.bodega.nombre if cotizacion.bodega else "N/A"
        for d in cotizacion.detalles:
            d.producto_nombre = d.producto.nombre if d.producto else "Desconocido"
            d.producto_codigo = d.producto.codigo if d.producto else "N/A"
    return cotizacion

def update_cotizacion(db: Session, cotizacion_id: int, cotizacion_in: schemas.CotizacionCreate, empresa_id: int):
    # Similar a Remision, solo si es BORRADOR
    cotizacion = db.query(Cotizacion).filter(Cotizacion.id == cotizacion_id, Cotizacion.empresa_id == empresa_id).first()
    if not cotizacion:
        raise HTTPException(status_code=404, detail="Cotización no encontrada.")

    if cotizacion.estado != 'BORRADOR':
        raise HTTPException(status_code=400, detail="Solo se pueden editar cotizaciones en estado BORRADOR.")

    # 1. Update Cabecera
    cotizacion.fecha = cotizacion_in.fecha
    cotizacion.fecha_vencimiento = cotizacion_in.fecha_vencimiento
    cotizacion.tercero_id = cotizacion_in.tercero_id
    cotizacion.bodega_id = cotizacion_in.bodega_id
    cotizacion.observaciones = cotizacion_in.observaciones
    
    # Recalcular Total
    total = sum(det.cantidad * det.precio_unitario for det in cotizacion_in.detalles)
    cotizacion.total_estimado = total

    # 2. Reemplazar Detalles
    db.query(CotizacionDetalle).filter(CotizacionDetalle.cotizacion_id == cotizacion_id).delete()
    
    for det in cotizacion_in.detalles:
        db_detalle = CotizacionDetalle(
            cotizacion_id=cotizacion.id,
            producto_id=det.producto_id,
            cantidad=det.cantidad,
            precio_unitario=det.precio_unitario,
            cantidad_facturada=0
        )
        db.add(db_detalle)

    db.commit()
    db.refresh(cotizacion)
    return cotizacion

def cambiar_estado(db: Session, cotizacion_id: int, nuevo_estado: str, empresa_id: int):
    cotizacion = db.query(Cotizacion).filter(Cotizacion.id == cotizacion_id, Cotizacion.empresa_id == empresa_id).first()
    if not cotizacion:
        raise HTTPException(status_code=404, detail="Cotización no encontrada.")
        
    # Validaciones simples de flujo
    if cotizacion.estado == 'ANULADA':
         raise HTTPException(status_code=400, detail="No se puede cambiar estado de una cotización ANULADA.")
         
    if nuevo_estado == 'APROBADA' and cotizacion.estado != 'BORRADOR':
         raise HTTPException(status_code=400, detail="Solo se puede aprobar desde Borrador.")

    cotizacion.estado = nuevo_estado
    db.commit()
    db.refresh(cotizacion)
    return cotizacion

def procesar_facturacion_cotizacion(db: Session, cotizacion_id: int, items_factura: list):
    """
    Actualiza el estado de la cotización a FACTURADA.
    """
    cot = db.query(Cotizacion).filter(Cotizacion.id == cotizacion_id).first()
    if cot:
        cot.estado = 'FACTURADA'
        db.add(cot)
        # Nota: No hacemos commit aquí porque somos parte de la transacción mayor de Facturación
