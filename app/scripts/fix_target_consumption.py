import sys
import os
from datetime import datetime
from sqlalchemy import func, extract

# Add project root to path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.consumo_registros import ControlPlanMensual
from app.models.documento import Documento
from app.models.movimiento_contable import MovimientoContable
# Fix for relationship initialization error
import app.models.nomina  # noqa

def fix_company_consumption(nit_target):
    db = SessionLocal()
    try:
        print(f"\n[INFO] Fixing Consumption for Company NIT: {nit_target}")
        
        empresa = db.query(Empresa).filter(Empresa.nit == nit_target).first()
        if not empresa:
            print(f"[ERROR] Company with NIT {nit_target} not found.")
            return

        print(f"[INFO] Found Company: {empresa.razon_social} (ID: {empresa.id})")
        
        # Periods to fix
        queries = [
            (2025, 12),
            (2026, 1),
            (2026, 2)
        ]

        for anio, mes in queries:
            print(f"\n--- Processing Period: {mes}/{anio} ---")
            
            # 1. Get Actual Consumption
            query_consumo = db.query(func.count(MovimientoContable.id))\
                .join(Documento, MovimientoContable.documento_id == Documento.id)\
                .filter(
                    Documento.empresa_id == empresa.id,
                    extract('year', Documento.fecha) == anio,
                    extract('month', Documento.fecha) == mes,
                    Documento.anulado == False
                )
            
            real_consumption = query_consumo.scalar() or 0
            print(f"  [REAL] Actual Active Records: {real_consumption}")

            # 2. Get and Update Plan
            plan = db.query(ControlPlanMensual).filter(
                ControlPlanMensual.empresa_id == empresa.id,
                ControlPlanMensual.anio == anio,
                ControlPlanMensual.mes == mes
            ).with_for_update().first()
            
            if plan:
                limit = plan.limite_asignado
                current_available = plan.cantidad_disponible
                
                # Correct Available = Limit - Real Consumption
                correct_available = limit - real_consumption
                
                print(f"  [PLAN] Limit: {limit} | Current Available: {current_available}")
                print(f"  [FIX]  Setting Available to: {correct_available} (Limit {limit} - Real {real_consumption})")
                
                if current_available != correct_available:
                    plan.cantidad_disponible = correct_available
                    db.add(plan)
                    print("  [SUCCESS] Plan updated.")
                else:
                    print("  [SKIP] Plan already correct.")
            else:
                print("  [WARN] No plan found for this month.")

        db.commit()
        print("\n[DONE] Fix applied successfully.")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        nit = sys.argv[1]
    else:
        nit = "9878778"
    fix_company_consumption(nit)
