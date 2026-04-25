import sys
import os

# Ensure the correct path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from app.core.database import SessionLocal
from app.services.propiedad_horizontal import pago_service

def test():
    db = SessionLocal()
    try:
        # Assuming empresa_id is 134 based on the user's log: empresa_id: 134
        empresa_id = 134
        unidad_id = 18
        print(f"Testing get_estado_cuenta_unidad for empresa {empresa_id}, unidad {unidad_id}")
        res = pago_service.get_estado_cuenta_unidad(db, unidad_id, empresa_id)
        print("Success!")
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test()
