
from app.core.database import SessionLocal
from app.models.producto import Producto, MovimientoInventario
from sqlalchemy import desc

db = SessionLocal()
try:
    p = db.query(Producto).filter(Producto.id == 1634).first()
    print(f"Producto: {p.nombre}")
    print(f"Costo Promedio Maestro: {p.costo_promedio}")
    print(f"Stock Maestro: {p.stock_almacenado}")
    
    print("\nUltimos 5 Movimientos:")
    movs = db.query(MovimientoInventario).filter(MovimientoInventario.producto_id == 1634).order_by(desc(MovimientoInventario.id)).limit(5).all()
    for m in movs:
        print(f"ID: {m.id}, Tipo: {m.tipo_movimiento}, Qty: {m.cantidad}, CostoU: {m.costo_unitario}, Total: {m.costo_total}")
finally:
    db.close()
