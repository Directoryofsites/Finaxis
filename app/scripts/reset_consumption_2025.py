import sys
import os
from sqlalchemy import func, extract

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.core.database import SessionLocal
from app.models.consumo_registros import HistorialConsumo, BolsaExcedente, ControlPlanMensual, EstadoPlan
from app.models.empresa import Empresa
import app.models.nomina # Fix mapper

def reset_consumption_2025():
    db = SessionLocal()
    try:
        # 1. Find Mejia
        mejia = db.query(Empresa).filter(Empresa.razon_social.ilike("%Mejia%")).first()
        if not mejia:
            print("Mejia not found")
            return

        print(f"RESETTING CONSUMPTION FOR: {mejia.razon_social} (ID: {mejia.id}) - YEAR 2025")

        # 2. Delete ALL HistorialConsumo for 2025 (Jan & Feb)
        # This removes the "Financial Memory" of any document or bag.
        deleted_hist = db.query(HistorialConsumo).filter(
            HistorialConsumo.empresa_id == mejia.id,
            extract('year', HistorialConsumo.fecha) == 2025
        ).delete(synchronize_session=False)
        print(f" - Deleted {deleted_hist} HistorialConsumo records.")

        # 3. Delete ALL BolsaExcedente for 2025
        deleted_bags = db.query(BolsaExcedente).filter(
            BolsaExcedente.empresa_id == mejia.id,
            BolsaExcedente.anio_origen == 2025
        ).delete(synchronize_session=False)
        print(f" - Deleted {deleted_bags} BolsaExcedente records.")

        # 4. Reset ControlPlanMensual for 2025
        # We want Jan and Feb to be "Fresh": 250 Available, Open state.
        planes = db.query(ControlPlanMensual).filter(
            ControlPlanMensual.empresa_id == mejia.id,
            ControlPlanMensual.anio == 2025
        ).all()

        for p in planes:
            print(f" - Resetting Plan {p.mes}/{p.anio}. Was: {p.cantidad_disponible} Disp, State: {p.estado}")
            p.cantidad_disponible = 250 # Reset to full limit
            p.estado = EstadoPlan.ABIERTO.value
            p.fecha_cierre = None
            # Note: We assume limit is 250. If dynamic, we should read it from Company, but 250 is standard.
            # Ideally we check mejia.limite_registros_mensual
            p.cantidad_disponible = mejia.limite_registros_mensual or 250
            
        db.commit()
        print("RESET COMPLETE. Please refresh your dashboard.")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_consumption_2025()
