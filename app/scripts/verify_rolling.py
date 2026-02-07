
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

def verify_rolling():
    print("--- VERIFYING ROLLING QUOTA CALCULATION (POST CLEANUP) ---")
    
    # 1. Check Pelaez (ID 211)
    empresa_id = 211
    
    # NOV 2025
    print("\n--- NOV 2025 ---")
    hist_nov = _calcular_saldo_historico(db, empresa_id, 2025, 11)
    print(f"Saldo Historico Nov: {hist_nov} (Expected 0)")
    
    # DEC 2025
    print("\n--- DEC 2025 ---")
    hist_dec = _calcular_saldo_historico(db, empresa_id, 2025, 12)
    print(f"Saldo Historico Dec: {hist_dec} (Expected ~70)")
    
    # JAN 2026
    print("\n--- JAN 2026 ---")
    hist_jan = _calcular_saldo_historico(db, empresa_id, 2026, 1)
    print(f"Saldo Historico Jan: {hist_jan} (Expected ~110)")

if __name__ == "__main__":
    verify_rolling()
