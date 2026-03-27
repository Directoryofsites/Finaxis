from app.core.database import SessionLocal
from app.models.producto import Producto
from app.services.inventario import recalcular_saldos_producto

def run():
    db = SessionLocal()
    try:
        productos = db.query(Producto).all()
        for p in productos:
            recalcular_saldos_producto(db, p.id)
        db.commit()
        print('Recalculo exitoso.')
    except Exception as e:
        print(f'Error: {e}')
    finally:
        db.close()

if __name__ == '__main__':
    run()
