import sys
import os
from sqlalchemy import func, desc

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.producto import MovimientoInventario
from app.models.producto import Producto

def find_heavy_company():
    db = SessionLocal()
    try:
        # Group movements by company (via Producto)
        print("--- Finding Heaviest Company ---")
        
        results = db.query(
            Producto.empresa_id,
            func.count(MovimientoInventario.id).label('total_movs')
        ).join(MovimientoInventario, MovimientoInventario.producto_id == Producto.id)\
         .group_by(Producto.empresa_id)\
         .order_by(desc('total_movs'))\
         .limit(5)\
         .all()
         
        for row in results:
            print(f"Empresa ID: {row.empresa_id} | Total Movimientos: {row.total_movs}")

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    find_heavy_company()
