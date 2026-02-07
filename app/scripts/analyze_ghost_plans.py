
from app.core.database import SessionLocal
from app.models.consumo_registros import ControlPlanMensual
from app.models.empresa import Empresa

def analyze_ghost_plans():
    db = SessionLocal()
    empresa_id = 176
    
    # 1. Check Company Creation Date
    empresa = db.query(Empresa).get(empresa_id)
    print(f"--- EMPRESA 176: {empresa.razon_social} ---")
    print(f"Fecha Creación: {empresa.created_at}")
    
    # 2. Check all plans for 2025
    print("\n--- PLANES 2025 ---")
    planes = db.query(ControlPlanMensual).filter(
        ControlPlanMensual.empresa_id == empresa_id,
        ControlPlanMensual.anio == 2025
    ).order_by(ControlPlanMensual.mes).all()
    
    for p in planes:
        print(f"Mes {p.mes}: Límite={p.limite_asignado}, Disp={p.cantidad_disponible}, Estado={p.estado}, Creado={p.fecha_creacion}")

    db.close()

if __name__ == "__main__":
    analyze_ghost_plans()
