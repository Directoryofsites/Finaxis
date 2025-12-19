
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.services.propiedad_horizontal import unidad_service
from sqlalchemy.orm import Session

def test_services():
    db = SessionLocal()
    empresa_id = 1 # Assuming ID 1 for test, or fetch first available
    try:
        print("Testing get_unidades...")
        unidades = unidad_service.get_unidades(db, empresa_id)
        print(f"Unidades result: {len(unidades)} found.")

        print("Testing get_propietarios_resumen...")
        props = unidad_service.get_propietarios_resumen(db, empresa_id)
        print(f"Propietarios result: {len(props)} found.")
        
        print("SUCCESS: All services executed without error.")
    except Exception as e:
        print(f"FAILURE: Assertion error or Exception: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_services()
