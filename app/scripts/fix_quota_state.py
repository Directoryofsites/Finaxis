import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.consumo_registros import ControlPlanMensual

def fix_company_quota(company_id, correct_available):
    db = SessionLocal()
    try:
        now = datetime.now()
        plan = db.query(ControlPlanMensual).filter(
            ControlPlanMensual.empresa_id == company_id,
            ControlPlanMensual.anio == now.year,
            ControlPlanMensual.mes == now.month
        ).first()

        if plan:
            print(f"Current Available: {plan.cantidad_disponible}")
            print(f"Updating to: {correct_available}")
            plan.cantidad_disponible = correct_available
            db.commit()
            print("Update Successful.")
        else:
            print("No plan found.")

    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # ID 179 identified from previous step
    # Correct Available = -8 (220 Limit - 228 Consumption)
    fix_company_quota(179, -8)
