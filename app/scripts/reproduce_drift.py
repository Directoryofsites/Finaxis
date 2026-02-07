import sys
import os
from datetime import datetime
from sqlalchemy import func, extract

# Add project root to path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.consumo_registros import ControlPlanMensual, EstadoPlan
# Fix for relationship initialization
import app.models.nomina  # noqa
from app.services.consumo_service import _get_or_create_plan_mensual

def reproduce_drift():
    db = SessionLocal()
    try:
        print("\n[TEST] Reproducing 'Drift' (Failure to Heal Upwards)")
        
        # 1. Pick a target company (Using the one from the issue: 204 / 9878778)
        # We know it has 0 active records now.
        empresa_id = 204
        now = datetime.now()
        
        plan = _get_or_create_plan_mensual(db, empresa_id, now)
        if not plan:
            print("[ERROR] No plan found.")
            return

        original_avail = plan.cantidad_disponible
        original_limit = plan.limite_asignado
        print(f"  [INIT] Limit: {original_limit} | Available: {original_avail}")

        # 2. SIMULATE DRIFT (Force available to 0)
        # This simulates a "Phantom Consumption" state where DB thinks we are full, but we have 0 docs.
        print("  [STEP] Forcing 'Phantom Consumption' (Setting Available = 0)...")
        plan.cantidad_disponible = 0
        db.commit()
        
        # 3. CALL HEALING
        # _get_or_create_plan_mensual triggers the auto-heal logic
        print("  [STEP] Triggering Auto-Heal via _get_or_create_plan_mensual...")
        plan_after = _get_or_create_plan_mensual(db, empresa_id, now)
        
        # 4. VERIFY RESULT
        print(f"  [RESULT] Limit: {plan_after.limite_asignado} | Available: {plan_after.cantidad_disponible}")
        
        if plan_after.cantidad_disponible == 0:
            print("  [FAIL] Logic successfully REPRODUCED the bug. Data did NOT heal upwards.")
        elif plan_after.cantidad_disponible == original_limit:
            print("  [PASS] Logic healed the data! (This would mean the bug is already fixed?)")
        else:
             print(f"  [?] Partial or unexpected result: {plan_after.cantidad_disponible}")

        # 5. RESTORE STATE (If we broke it for the test)
        # We should restore it to original_avail
        if plan_after.cantidad_disponible != original_avail:
            print(f"  [CLEANUP] Restoring to {original_avail}...")
            plan_after.cantidad_disponible = original_avail
            db.commit()

    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reproduce_drift()
