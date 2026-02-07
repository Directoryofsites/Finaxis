import sys
sys.path.append('c:\\ContaPY2')
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.consumo_registros import ControlPlanMensual
from app.services.consumo.cierre_mensual_service import ejecutar_cierre_mensual, revertir_cierre_mensual

def test_cierre():
    db = SessionLocal()
    try:
        empresa_id = 211
        anio = 2025
        mes = 11
        
        # 1. Estado Inicial
        plan = db.query(ControlPlanMensual).filter_by(
            empresa_id=empresa_id, anio=anio, mes=mes
        ).first()
        
        if not plan:
            print("Plan no encontrado")
            return

        print(f"--- INICIO ---")
        print(f"Plan {mes}/{anio}: Estado={plan.estado}, Disp={plan.cantidad_disponible}, Limite={plan.limite_asignado}")
        
        # 2. Cerrar
        print(f"--- EJECUTANDO CIERRE ---")
        ejecutar_cierre_mensual(db, empresa_id, anio, mes)
        db.commit() # Commit real para ver persistencia
        
        db.refresh(plan)
        print(f"Plan {mes}/{anio}: Estado={plan.estado}, Disp={plan.cantidad_disponible}, Limite={plan.limite_asignado}")
        
        if plan.cantidad_disponible == 0 and plan.limite_asignado > 0:
             print("ALERTA: EL CIERRE PUSO EL DISPONIBLE EN 0")
        else:
             print("OK: El saldo se mantuvo.")

        # 3. Revertir
        print(f"--- REVIRTIENDO CIERRE ---")
        revertir_cierre_mensual(db, empresa_id, anio, mes)
        db.commit()
        
        db.refresh(plan)
        print(f"Plan {mes}/{anio}: Estado={plan.estado}, Disp={plan.cantidad_disponible}, Limite={plan.limite_asignado}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_cierre()
