import sys
import os

# Add project root to path
sys.path.append("c:\\ContaPY2")

from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.consumo_registros import ControlPlanMensual, HistorialConsumo, TipoFuenteConsumo, TipoOperacionConsumo

def sync_plans():
    db = SessionLocal()
    try:
        print("--- Starting Plan Synchronization ---")
        
        # 1. Get all Plans
        planes = db.query(ControlPlanMensual).all()
        print(f"Found {len(planes)} plans to check.")
        
        for plan in planes:
            # 2. Calculate consumption from History for this specific plan
            # We look for records where source is THIS plan
            
            # Consumo (Resta)
            consumo_total = db.query(func.sum(HistorialConsumo.cantidad)).filter(
                HistorialConsumo.fuente_id == plan.id,
                HistorialConsumo.fuente_tipo.in_([TipoFuenteConsumo.PLAN, 'PLAN_PASADO']),
                HistorialConsumo.tipo_operacion == TipoOperacionConsumo.CONSUMO
            ).scalar() or 0
            
            # Reversiones (Suma)
            reversion_total = db.query(func.sum(HistorialConsumo.cantidad)).filter(
                HistorialConsumo.fuente_id == plan.id,
                HistorialConsumo.fuente_tipo.in_([TipoFuenteConsumo.PLAN, 'PLAN_PASADO']),
                HistorialConsumo.tipo_operacion == TipoOperacionConsumo.REVERSION
            ).scalar() or 0
            
            net_consumption = consumo_total - reversion_total
            expected_available = plan.limite_asignado - net_consumption
            
            if plan.cantidad_disponible != expected_available:
                print(f"MISMATCH Plan {plan.id} ({plan.mes}/{plan.anio}) Empresa {plan.empresa_id}:")
                print(f"  DB Available: {plan.cantidad_disponible}")
                print(f"  Calc Consumption: {net_consumption} (Cons: {consumo_total}, Rev: {reversion_total})")
                print(f"  Expected Available: {expected_available} (Limit {plan.limite_asignado} - Net {net_consumption})")
                
                # FIX IT
                plan.cantidad_disponible = expected_available
                db.add(plan)
                print(f"  -> SET TO {expected_available}")
        
        print("Committing changes...")
        db.commit()
        print("--- Sync Completed successfully ---")
        
    except Exception as e:
        # db.rollback() # Let's see the error if any, rollback might hide it if printed poorly
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    sync_plans()
