import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.core.database import SessionLocal
# Import ALL models to ensure relationships resolve
import app.models # this imports what is in __init__.py
import app.models.nomina # explicit import for nomina
from app.models.consumo_registros import ControlPlanMensual, RecargaAdicional, PaqueteRecarga, HistorialConsumo
from app.models.cupo_adicional import CupoAdicional
from app.models.empresa import Empresa

def debug_consumption():
    db = SessionLocal()
    try:
        # Find the accountant company
        empresa = db.query(Empresa).filter(Empresa.razon_social.ilike("%Mejia y Mejia%")).first()
        if not empresa:
            print("Company 'Mejia y Mejia' not found.")
            return

        print(f"Checking Company: {empresa.razon_social} (ID: {empresa.id})")
        
        # Check ControlPlanMensual for Jan 2026
        plan = db.query(ControlPlanMensual).filter_by(
            empresa_id=empresa.id,
            anio=2026,
            mes=1
        ).first()

        if plan:
            print(f"Plan Monthly (2026-01):")
            print(f"  Limit Assigned: {plan.limite_asignado}")
            print(f"  Available: {plan.cantidad_disponible}")
            used = plan.limite_asignado - plan.cantidad_disponible
            print(f"  Calculated Used (Limit - Avail): {used}")
            print(f"  State: {plan.estado}")
            print(f"  Manual Override: {plan.es_manual}")
        else:
            print("No ControlPlanMensual found for 2026-01.")

        # Check RecargaAdicional
        recargas = db.query(RecargaAdicional).filter_by(empresa_id=empresa.id, anio=2026, mes=1).all()
        print(f"\nRecargas (2026-01): {len(recargas)}")
        for r in recargas:
            print(f"  ID: {r.id}, Purchased: {r.cantidad_comprada}, Avail: {r.cantidad_disponible}, State: {r.estado}")

        # Check CupoAdicional
        cupos = db.query(CupoAdicional).filter_by(empresa_id=empresa.id, anio=2026, mes=1).all()
        print(f"\nCupos Adicionales (2026-01): {len(cupos)}")
        for c in cupos:
            print(f"  ID: {c.id}, Amount: {c.cantidad_adicional}")

        # Check HistorialConsumo
        historial = db.query(HistorialConsumo).filter(
            HistorialConsumo.empresa_id == empresa.id,
            HistorialConsumo.fecha >= '2026-01-01',
            HistorialConsumo.fecha < '2026-02-01'
        ).order_by(HistorialConsumo.fecha).all()

        print(f"\nConsumption History (2026-01): {len(historial)}")
        plan_consumed = 0
        plan_reverted = 0
        
        for h in historial:
            print(f"  ID: {h.id}, Date: {h.fecha}, Qty: {h.cantidad}, Type: {h.tipo_operacion}, Source: {h.fuente_tipo}, DocID: {h.documento_id}")
            if h.fuente_tipo == 'PLAN':
                if h.tipo_operacion == 'CONSUMO':
                    plan_consumed += h.cantidad
                elif h.tipo_operacion == 'REVERSION':
                    plan_reverted += h.cantidad
        
        print(f"\nSummary PLAN:")
        print(f"  Total Consumed: {plan_consumed}")
        print(f"  Total Reverted: {plan_reverted}")
        print(f"  Net Impact (Consumed - Reverted): {plan_consumed - plan_reverted}")
        print(f"  Expected Available (250 - Net): {250 - (plan_consumed - plan_reverted)}")


    finally:
        db.close()

if __name__ == "__main__":
    debug_consumption()
