
import sys
import os
sys.path.append('c:\\ContaPY2')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.consumo_registros import ControlPlanMensual
from app.api.api_v1.endpoints.consumo import _calcular_saldo_historico

# Setup DB
DATABASE_URL = settings.DATABASE_URL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def restore_demo():
    print("--- RESTORING DEMO DATA FOR PELAEZ ---")
    empresa_id = 211
    
    # Nov 2025 -> 70 Available
    plan_nov = db.query(ControlPlanMensual).filter_by(
        empresa_id=empresa_id, anio=2025, mes=11
    ).first()
    if plan_nov:
        plan_nov.cantidad_disponible = 70
        print("Updated Nov 2025 to 70.")
    
    # Dec 2025 -> 40 Available
    plan_dec = db.query(ControlPlanMensual).filter_by(
        empresa_id=empresa_id, anio=2025, mes=12
    ).first()
    if plan_dec:
        plan_dec.cantidad_disponible = 40
        print("Updated Dec 2025 to 40.")
        
    db.commit()
    
    # VERIFY AGAIN
    print("\n--- VERIFYING ROLLING QUOTA (JAN 2026) ---")
    hist_jan = _calcular_saldo_historico(db, empresa_id, 2026, 1)
    print(f"Saldo Historico Jan: {hist_jan} (Expected 70+40=110)")

if __name__ == "__main__":
    restore_demo()
