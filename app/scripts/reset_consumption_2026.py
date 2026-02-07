import sys
import os
from sqlalchemy import func, extract

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.core.database import SessionLocal
from app.models.consumo_registros import HistorialConsumo, BolsaExcedente, ControlPlanMensual, EstadoPlan
from app.models.empresa import Empresa
import app.models.nomina

def reset_consumption_2026():
    db = SessionLocal()
    try:
        # 1. Find Mejia
        mejia = db.query(Empresa).filter(Empresa.razon_social.ilike("%Mejia%")).first()
        if not mejia:
            print("Mejia not found")
            return

        print(f"DIAGNOSIS & RESET FOR: {mejia.razon_social} (ID: {mejia.id}) - YEAR 2026")

        # 2. Diagnose Feb 2026
        # Check Plan
        plan_feb = db.query(ControlPlanMensual).filter(
            ControlPlanMensual.empresa_id == mejia.id,
            ControlPlanMensual.anio == 2026,
            ControlPlanMensual.mes == 2
        ).first()

        if plan_feb:
            print(f" - Plan Feb 2026: {plan_feb.cantidad_disponible} Available (Should be 250?)")
        else:
            print(" - Plan Feb 2026: Not Found")

        # Check History
        hist_count = db.query(func.count(HistorialConsumo.id)).filter(
            HistorialConsumo.empresa_id == mejia.id,
            extract('year', HistorialConsumo.fecha) == 2026,
            extract('month', HistorialConsumo.fecha) == 2
        ).scalar()
        print(f" - History Count Feb 2026: {hist_count}")

        # 3. ACTION: RESET 2026
        print(" -> EXECUTING RESET FOR 2026...")
        
        # Delete History corresponding to 2026
        db.query(HistorialConsumo).filter(
            HistorialConsumo.empresa_id == mejia.id,
            extract('year', HistorialConsumo.fecha) == 2026
        ).delete(synchronize_session=False)

        # Delete Bags 2026
        db.query(BolsaExcedente).filter(
            BolsaExcedente.empresa_id == mejia.id,
            BolsaExcedente.anio_origen == 2026
        ).delete(synchronize_session=False)

        # Reset Plans 2026 (Jan to Dec just in case)
        planes = db.query(ControlPlanMensual).filter(
            ControlPlanMensual.empresa_id == mejia.id,
            ControlPlanMensual.anio == 2026
        ).all()

        for p in planes:
            p.cantidad_disponible = 250
            p.estado = EstadoPlan.ABIERTO.value
            p.fecha_cierre = None
            
        db.commit()
        print("RESET 2026 COMPLETE.")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_consumption_2026()
