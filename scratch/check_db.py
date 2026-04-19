
from app.core.database import SessionLocal
from app.models.producto import MovimientoInventario
from sqlalchemy import desc

db = SessionLocal()
try:
    # Buscar el último movimiento del producto 1634 (Arracacha)
    mov = db.query(MovimientoInventario).filter(MovimientoInventario.producto_id == 1634).order_by(desc(MovimientoInventario.id)).first()
    if mov:
        print(f"ID Mov: {mov.id}")
        print(f"Tipo: {mov.tipo_movimiento}")
        print(f"Doc ID: {mov.documento_id}")
        print(f"Costo Unitario en DB: {mov.costo_unitario}")
        print(f"Costo Total en DB: {mov.costo_total}")
        
        from app.models.documento import Documento
        doc = db.query(Documento).get(mov.documento_id)
        if doc:
            print(f"Doc Ref ID: {doc.documento_referencia_id}")
    else:
        print("No se encontró movimiento para el producto 1634")
finally:
    db.close()
