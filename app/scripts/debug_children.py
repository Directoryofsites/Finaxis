import sys
import os
sys.path.append(os.path.abspath("c:/ContaPY2"))
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.empresa import Empresa
from app.models.consumo_registros import ControlPlanMensual
from datetime import datetime

# Use the loaded settings to ensure we hit the same DB
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def main():
    print(f"--- DEBUGGING CHILDREN (DB: {settings.DATABASE_URL}) ---")
    
    # 1. Inspect Company 179 children
    print("\n[CHILDREN OF 179 (Mejia)]")
    children = db.query(Empresa).filter(Empresa.padre_id == 179).all()
    for child in children:
        print(f"ID: {child.id} | Name: {child.razon_social} | Limit: {child.limite_registros_mensual} / {child.limite_registros}")
        check_plan(child.id)

    # 2. Inspect ANY company with Limit 1000
    print("\n[SUSPECTS WITH LIMIT 1000]")
    suspects = db.query(Empresa).filter(
        (Empresa.limite_registros == 1000) | (Empresa.limite_registros_mensual == 1000)
    ).all()
    
    for s in suspects:
        print(f"ID: {s.id} | Name: {s.razon_social} | Parent: {s.padre_id} | Limits: {s.limite_registros_mensual}/{s.limite_registros}")
        check_plan(s.id)

def check_plan(empresa_id):
    now = datetime.now()
    plan = db.query(ControlPlanMensual).filter(
        ControlPlanMensual.empresa_id == empresa_id,
        ControlPlanMensual.anio == now.year,
        ControlPlanMensual.mes == now.month
    ).first()
    
    if plan:
        print(f"   -> PLAN: Limit={plan.limite_asignado}, Avail={plan.cantidad_disponible}")
        if plan.limite_asignado == 1000:
            print("   *** MATCH FOUND ***")
    else:
        print("   -> NO PLAN FOUND")

if __name__ == "__main__":
    main()
