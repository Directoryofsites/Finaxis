from app.core.database import SessionLocal
# Import ALL models to ensure registry is populated
import app.models.nomina 
import app.models.propiedad_horizontal.unidad 
from app.models.consumo_registros import ControlPlanMensual, HistorialConsumo
from app.models.documento import Documento
from app.models.movimiento_contable import MovimientoContable
from sqlalchemy import func, extract
from datetime import datetime

def repair_mejia():
    db = SessionLocal()
    empresa_id = 179
    anio = 2026
    mes = 1
    
    try:
        print(f"--- REPAIRING EMPRESA {empresa_id} for {mes}/{anio} ---")
        
        # 1. Get Plan
        plan = db.query(ControlPlanMensual).filter_by(empresa_id=empresa_id, anio=anio, mes=mes).first()
        if not plan:
            print("Plan not found!")
            return

        print(f"Current State: Limit={plan.limite_asignado}, Available={plan.cantidad_disponible}")

        # 2. Calculate Real Consumption (Count Documents/Movements)
        # Note: This counts ONLY documents owned directly by 179.
        # BUT this is a "Shared Wallet". The plan availability should reflect consumption of 179 AND all its children (180, 183, etc.)?
        # WAIT! If "Bolsa Maestra" means children consume from parent, then `cantidad_disponible` on Parent MUST decrease when children consume.
        # If children have been consuming, maybe they truly drained the parent to 0?
        
        # Let's count consumption of specific children to see if they sum up to ~248.
        
        # Count 179
        c_179 = db.query(func.count(MovimientoContable.id)).join(Documento).filter(
            Documento.empresa_id == empresa_id,
            extract('year', Documento.fecha) == anio,
            extract('month', Documento.fecha) == mes,
            Documento.anulado == False
        ).scalar()
        print(f"Real Usage 179: {c_179}")
        
        # Count 180 (Acme)
        c_180 = db.query(func.count(MovimientoContable.id)).join(Documento).filter(
            Documento.empresa_id == 180,
            extract('year', Documento.fecha) == anio,
            extract('month', Documento.fecha) == mes,
            Documento.anulado == False
        ).scalar()
        print(f"Real Usage 180: {c_180}")

        # Count 183 (Pajarera)
        c_183 = db.query(func.count(MovimientoContable.id)).join(Documento).filter(
            Documento.empresa_id == 183,
            extract('year', Documento.fecha) == anio,
            extract('month', Documento.fecha) == mes,
            Documento.anulado == False
        ).scalar()
        print(f"Real Usage 183: {c_183}")
        
        total_usage_family = c_179 + c_180 + c_183
        print(f"Total Family Usage: {total_usage_family}")
        
        # If the Parent Plan is shared, Available should be Limit - TotalFamilyUsage (approx)
        theoretical_available = plan.limite_asignado - total_usage_family
        print(f"Theoretical Available (Limit - Family): {theoretical_available}")
        
        if plan.cantidad_disponible == 0 and theoretical_available > 0:
            print(">>> DETECTED DISCREPANCY. FIXING TO THEORETICAL AVAILABLE...")
            plan.cantidad_disponible = theoretical_available
            db.commit()
            print(f"FIXED: New Available = {plan.cantidad_disponible}")
        else:
            print("No obvious fix needed based on this simple logic, or usage is truly high.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    repair_mejia()
