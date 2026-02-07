
from app.core.database import SessionLocal
from app.models.consumo_registros import ControlPlanMensual
from app.models.empresa import Empresa
from sqlalchemy import text
from datetime import datetime

def fix_ghost_plans():
    db = SessionLocal()
    print("--- INICIANDO LIMPIEZA DE PLANES FANTASMA ---")
    
    # Obtener todas las empresas
    empresas = db.query(Empresa).all()
    total_deleted = 0
    
    for emp in empresas:
        if not emp.created_at:
            continue
            
        created_date = emp.created_at
        # Normalizar a inicio de mes para comparación segura
        start_month_year = (created_date.year, created_date.month)
        
        print(f"Empresa ID {emp.id} ({emp.razon_social}) - Creada: {created_date.strftime('%Y-%m')}")
        
        # Buscar planes anteriores a la fecha de creación
        # Lógica: Año del plan < Año creación OR (Año plan == Año creación AND Mes plan < Mes creación)
        
        ghost_plans = db.query(ControlPlanMensual).filter(
            ControlPlanMensual.empresa_id == emp.id
        ).all()
        
        count_emp = 0
        for plan in ghost_plans:
            is_ghost = False
            if plan.anio < created_date.year:
                is_ghost = True
            elif plan.anio == created_date.year and plan.mes < created_date.month:
                is_ghost = True
                
            if is_ghost:
                print(f"  [DELETE] Plan Fantasma detectado: {plan.mes}/{plan.anio}")
                db.delete(plan)
                count_emp += 1
        
        if count_emp > 0:
            print(f"  -> Eliminados {count_emp} planes fantasma para Empresa {emp.id}")
            total_deleted += count_emp
            
    db.commit()
    print(f"--- FIN DEL PROCESO. Total eliminados: {total_deleted} ---")
    db.close()

if __name__ == "__main__":
    fix_ghost_plans()
