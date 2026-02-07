
from app.core.database import SessionLocal
from app.models.consumo_registros import ControlPlanMensual

def inspect():
    db = SessionLocal()
    empresa_id = 176
    print(f"--- INSPECTING PLAN FOR EMPRESA {empresa_id} ---")
    planes = db.query(ControlPlanMensual).filter(ControlPlanMensual.empresa_id == empresa_id).order_by(ControlPlanMensual.anio, ControlPlanMensual.mes).all()
    
    for p in planes:
        print(f"Mes: {p.mes}/{p.anio} - Consumido: {p.cantidad_consumida} / {p.limite_asignado} - Estado: {p.estado}")
    
    db.close()

if __name__ == "__main__":
    inspect()
