import sys
import os
from datetime import datetime
from sqlalchemy import func, extract
from sqlalchemy.orm import joinedload

# Add project root to path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.consumo_registros import ControlPlanMensual, HistorialConsumo
from app.models.documento import Documento
from app.models.movimiento_contable import MovimientoContable
# Fix for relationship initialization error
import app.models.nomina  # noqa

def inspect_company(nit_target):
    db = SessionLocal()
    try:
        print(f"\n[INFO] Inspecting Company NIT: {nit_target}")
        
        # 1. Find Company
        empresa = db.query(Empresa).filter(Empresa.nit == nit_target).first()
        if not empresa:
            print(f"[ERROR] Company with NIT {nit_target} not found.")
            return

        print(f"[INFO] Found Company: {empresa.razon_social} (ID: {empresa.id})")
        print(f"       Padre ID: {empresa.padre_id}")
        
        # 2. Check Plan for Current Month (Assuming Dec 2025 or current?)
        # User screen showed Dec 2025 in screenshot, let's check Dec 2025 and Jan 2026/Feb 2026
        # Actually user said "Ahorita voy a intentar...". Date in screenshot is Dec 2025 (future?) NO wait.
        # User date in metadata is 2026-02-02.
        # Screenshot 1 says "diciembre 2025". Screenshot 2 says "noviembre 2025".
        # Wait, current date is Feb 2nd 2026.
        # Let's inspect the current active month (Feb 2026) and maybe Jan 2026.
        
        now = datetime.now()
        queries = [
            (2025, 12),
            (2026, 1),
            (2026, 2)
        ]

        for anio, mes in queries:
            print(f"\n--- Period: {mes}/{anio} ---")
            
            # A. Plan Control
            plan = db.query(ControlPlanMensual).filter(
                ControlPlanMensual.empresa_id == empresa.id,
                ControlPlanMensual.anio == anio,
                ControlPlanMensual.mes == mes
            ).first()
            
            limit = 0
            available = 0
            state = "N/A"
            
            if plan:
                limit = plan.limite_asignado
                available = plan.cantidad_disponible
                state = plan.estado
                print(f"  [PLAN] Limit: {limit} | Available: {available} | Used (Calculated): {limit - available} | State: {state}")
            else:
                print("  [PLAN] No plan found for this month.")

            # B. Actual Consumption (Count Movimientos in Valid Documents)
            # Logic: Sum of movements in documents that are NOT annulled.
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
            
            # C. Count Deleted/Annulled references (Ghost Hunting)
            # Documents that ARE annulled but might have movements (Logic says they shouldn't count, but let's see count)
            query_annulled = db.query(func.count(MovimientoContable.id))\
                .join(Documento, MovimientoContable.documento_id == Documento.id)\
                .filter(
                    Documento.empresa_id == empresa.id,
                    extract('year', Documento.fecha) == anio,
                    extract('month', Documento.fecha) == mes,
                    Documento.anulado == True
                )
            annulled_records = query_annulled.scalar() or 0
            
            print(f"  [INFO] Records in Annulled Documents: {annulled_records}")

            # D. Discrepancy
            if plan:
                reported_used = limit - available
                diff = reported_used - real_consumption
                if diff != 0:
                    print(f"  [WARN] DISCREPANCY FOUND! System thinks used {reported_used}, but actual is {real_consumption}. Diff: {diff}")
                    if diff > 0 and diff == annulled_records:
                         print("  [HYPOTHESIS] The difference matches exactly the annulled records. Reversion failed?")
                else:
                    print(f"  [OK] No discrepancy.")

    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        nit = sys.argv[1]
    else:
        nit = "9878778"
    inspect_company(nit)
