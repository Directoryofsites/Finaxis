
import sys
import os
sys.path.append('c:\\ContaPY2')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.consumo_registros import ControlPlanMensual
from app.models.empresa import Empresa

# Setup DB
DATABASE_URL = settings.DATABASE_URL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def cleanup_ghosts():
    print("--- CLEANING GHOST PLANS FOR PELAEZ ---")
    empresa = db.query(Empresa).filter(Empresa.razon_social.ilike("%Pelaez%")).first()
    
    if not empresa: return

    # Ghost Plans: Anio 2025 Mes < 11 (Start Date is Nov 2025)
    # Also 2026 > 2 (Just to be safe if they were created by forward testing)
    
    # 1. Clear Jan/Feb 2025
    deleted = db.query(ControlPlanMensual).filter(
        ControlPlanMensual.empresa_id == empresa.id,
        ControlPlanMensual.anio == 2025,
        ControlPlanMensual.mes < 11
    ).delete()
    
    print(f"Deleted {deleted} ghost plans from 2025 (Pre-Nov).")
    
    db.commit()

if __name__ == "__main__":
    cleanup_ghosts()
