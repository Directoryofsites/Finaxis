
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

def audit_plans():
    print("--- AUDITING PLANS FOR PELAEZ ---")
    empresa = db.query(Empresa).filter(Empresa.razon_social.ilike("%Pelaez%")).first()
    if not empresa:
        print("Empresa Pelaez not found")
        return

    print(f"Empresa: {empresa.razon_social} (ID: {empresa.id})")
    print(f"Fecha Inicio Operaciones: {empresa.fecha_inicio_operaciones}")
    print(f"Created At: {empresa.created_at}")
    
    plans = db.query(ControlPlanMensual).filter(
        ControlPlanMensual.empresa_id == empresa.id
    ).order_by(ControlPlanMensual.anio, ControlPlanMensual.mes).all()
    
    print(f"\nFound {len(plans)} plans:")
    for p in plans:
        print(f"  - {p.mes}/{p.anio} | Disp: {p.cantidad_disponible} | Estado: {p.estado}")
        
if __name__ == "__main__":
    audit_plans()
