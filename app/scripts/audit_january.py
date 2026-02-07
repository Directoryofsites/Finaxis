import sys
import os
from sqlalchemy import func

# Add project root to path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.consumo_registros import HistorialConsumo, ControlPlanMensual, TipoFuenteConsumo
from app.models.documento import Documento
import app.models.nomina

def audit_january_plan(company_id):
    db = SessionLocal()
    try:
        print(f"--- AUDIT FOR COMPANY {company_id} (JAN 2026) ---")
        
        # 1. Get Plan Status
        plan = db.query(ControlPlanMensual).filter(
            ControlPlanMensual.empresa_id == company_id,
            ControlPlanMensual.anio == 2026,
            ControlPlanMensual.mes == 1
        ).first()
        
        if plan:
            print(f"Current Plan State: Limit={plan.limite_asignado}, Available={plan.cantidad_disponible}, Status={plan.estado}")
        else:
            print("Plan NOT FOUND for Jan 2026")

        # 2. Reconstruct Consumption Timeline
        print("\n[CONSUMPTION TIMELINE JAN 2026]")
        history = db.query(HistorialConsumo).filter(
            HistorialConsumo.empresa_id == company_id,
            func.extract('year', HistorialConsumo.fecha) == 2026,
            func.extract('month', HistorialConsumo.fecha) == 1,
            HistorialConsumo.fuente_tipo == TipoFuenteConsumo.PLAN
        ).order_by(HistorialConsumo.id).all()
        
        cumulative_usage = 0
        for h in history:
            cumulative_usage += h.cantidad
            doc_info = "Unknown Doc"
            if h.documento_id:
                doc = db.query(Documento).get(h.documento_id)
                if doc:
                    doc_info = f"{doc.tipo_documento.codigo} #{doc.consecutivo}"
            
            print(f"  - ID {h.id} | Date: {h.fecha} | Amount: {h.cantidad} | Doc: {doc_info} | Balance After: {h.saldo_fuente_despues}")

        print(f"\nTotal Consumed from Plan: {cumulative_usage}")
        if plan:
            expected_avail = plan.limite_asignado - cumulative_usage
            print(f"Expected Available (Limit - TotalConsumed): {expected_avail}")

    finally:
        db.close()

if __name__ == "__main__":
    # Check both Child (205) and Parent (177) since 205 consumes from 177
    audit_january_plan(177) 
