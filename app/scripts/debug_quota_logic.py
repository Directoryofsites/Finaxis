import sys
import os
from datetime import datetime
from sqlalchemy import func

# Add project root to path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.consumo_registros import ControlPlanMensual, HistorialConsumo
from app.models.documento import Documento
from app.models.movimiento_contable import MovimientoContable

def inspect_company(company_name_part):
    db = SessionLocal()
    try:
        # 1. Find Company
        empresa = db.query(Empresa).filter(Empresa.razon_social.ilike(f"%{company_name_part}%")).first()
        if not empresa:
            print(f"No company found matching '{company_name_part}'")
            return

        print(f"--- INSPECTION: {empresa.razon_social} (ID: {empresa.id}) ---")
        print(f"Parent ID: {empresa.padre_id}")
        
        # 2. Inspect Plan
        now = datetime.now()
        plan = db.query(ControlPlanMensual).filter(
            ControlPlanMensual.empresa_id == empresa.id,
            ControlPlanMensual.anio == now.year,
            ControlPlanMensual.mes == now.month
        ).first()

        if plan:
            print(f"Plan Mensual: Limit={plan.limite_asignado}, Avail={plan.cantidad_disponible}")
            print(f"Plan State: {plan.estado}")
        else:
            print("No Plan Mensual found for this month.")

        # 3. Calculate Child Consumption
        # Note: This is expensive but necessary for debug
        children = db.query(Empresa).filter(Empresa.padre_id == empresa.id).all()
        print(f"Children Count: {len(children)}")
        
        total_child_consumption = 0
        for child in children:
            # Get consumption via Historial for Child
            # Only for this month
             child_usage = db.query(func.sum(HistorialConsumo.cantidad)).filter(
                HistorialConsumo.empresa_id == child.id,
                func.extract('year', HistorialConsumo.fecha) == now.year,
                func.extract('month', HistorialConsumo.fecha) == now.month
            ).scalar() or 0
             print(f"  Child {child.razon_social} (ID {child.id}) Usage: {child_usage}")
             total_child_consumption += child_usage

        print(f"Total Child Consumption (via History): {total_child_consumption}")
        
        # 4. Calculate Own Consumption
        own_usage = db.query(func.sum(HistorialConsumo.cantidad)).filter(
            HistorialConsumo.empresa_id == empresa.id,
             func.extract('year', HistorialConsumo.fecha) == now.year,
            func.extract('month', HistorialConsumo.fecha) == now.month
        ).scalar() or 0
        print(f"Own Consumption (via History): {own_usage}")

        # 5. Sanity Check Calculation
        theoretical_avail = plan.limite_asignado - (own_usage + total_child_consumption) if plan else 0
        print(f"Theoretical Available (Limit - Total Usage): {theoretical_avail}")
        
        if plan:
            print(f"DISCREPANCY: {plan.cantidad_disponible - theoretical_avail}")

    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_company("Mejia")
