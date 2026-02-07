import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.services.consumo_service import _get_or_create_plan_mensual
from app.models.consumo_registros import ControlPlanMensual
import app.models.nomina

def trigger_healing(company_id):
    db = SessionLocal()
    try:
        now = datetime.now()
        print(f"--- TRIGGERING HEALING FOR COMPANY {company_id} ---")
        
        # 1. Check before
        plan_before = db.query(ControlPlanMensual).filter(
            ControlPlanMensual.empresa_id == company_id,
            ControlPlanMensual.anio == now.year,
            ControlPlanMensual.mes == now.month
        ).first()
        
        if plan_before:
             print(f"BEFORE: Limit={plan_before.limite_asignado}, Available={plan_before.cantidad_disponible}")
        else:
             print("BEFORE: No plan found (Normal if new)")

        # 2. Trigger Logic
        # This function contains the healing logic
        plan = _get_or_create_plan_mensual(db, company_id, now)
        db.commit() # Save changes
        
        # 3. Check after
        print(f"AFTER: Limit={plan.limite_asignado}, Available={plan.cantidad_disponible}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    trigger_healing(177) # Gonzalito
