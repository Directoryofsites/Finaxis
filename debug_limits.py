from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.consumo_registros import ControlPlanMensual
from sqlalchemy import text

db = SessionLocal()

try:
    # 1. Inspect Companies and Limits
    print("--- EMPRESAS ---")
    empresas = db.query(Empresa).all()
    for e in empresas:
        print(f"ID: {e.id} | Name: {e.razon_social} | Limit: {e.limite_registros}")

    # 2. Inspect Plans for relevant companies (assuming user is one of them, likely the one with limits)
    print("\n--- PLANES MENSUALES (Nov 2025) ---")
    for e in empresas:
        planes = db.query(ControlPlanMensual).filter(
            ControlPlanMensual.empresa_id == e.id,
            ControlPlanMensual.anio == 2025,
            ControlPlanMensual.mes == 11
        ).all()
        for p in planes:
            print(f"Empresa {e.id} | Plan {p.mes}/{p.anio} | Limit Asignado: {p.limite_asignado} | Disp: {p.cantidad_disponible} | Estado: {p.estado}")
            
finally:
    db.close()
