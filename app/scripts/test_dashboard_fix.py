import sys
import os
from datetime import date

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.core.database import SessionLocal
from app.services import dashboard as dashboard_service
from app.models.empresa import Empresa
import app.models.nomina # Fix mapper error

def test_dashboard_consumption():
    db = SessionLocal()
    try:
        # Pajarera ID
        pajarera_id = 183
        mejia_id = 179 # Grandparent

        print("\n--- TESTING DASHBOARD SERVICE FIX ---")
        
        # 1. Check Pajarera (Child/Grandchild)
        print(f"Checking Pajarera (ID: {pajarera_id})...")
        # Note: Using January 2026 as per recent context
        res_pajarera = dashboard_service.get_consumo_actual(db, pajarera_id, mes=1, anio=2026)
        print(f"Pajarera Result: {res_pajarera}")
        
        # 2. Check Mejia (Grandparent/Accountant)
        print(f"Checking Mejia (ID: {mejia_id})...")
        res_mejia = dashboard_service.get_consumo_actual(db, mejia_id, mes=1, anio=2026)
        print(f"Mejia Result: {res_mejia}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_dashboard_consumption()
