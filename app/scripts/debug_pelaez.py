from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.consumo_registros import ControlPlanMensual, HistorialConsumo

def check_pelaez_data():
    db = SessionLocal()
    try:
        # 1. Find Company
        empresa = db.query(Empresa).filter(Empresa.nit == '5456748787').first()
        if not empresa:
            print("Empresa Pelaez Hermanos not found by NIT 5456748787")
            return

        print(f"Empresa: {empresa.razon_social} (ID: {empresa.id})")

        # 2. Check Plan November 2025
        plan_nov = db.query(ControlPlanMensual).filter(
            ControlPlanMensual.empresa_id == empresa.id,
            ControlPlanMensual.anio == 2025,
            ControlPlanMensual.mes == 11
        ).first()

        if not plan_nov:
            print("Plan Nov 2025 not found.")
        else:
            print(f"\n--- Plan Nov 2025 (ID: {plan_nov.id}) ---")
            print(f"Limite: {plan_nov.limite_asignado}")
            print(f"Disponible (DB): {plan_nov.cantidad_disponible}")
            print(f"Consumido (Calc): {plan_nov.limite_asignado - plan_nov.cantidad_disponible}")

            # 3. Check History for this Plan
            # History linked to this Plan ID
            history = db.query(HistorialConsumo).filter(
                HistorialConsumo.empresa_id == empresa.id,
                HistorialConsumo.fuente_id == plan_nov.id,
                HistorialConsumo.fuente_tipo == 'PLAN' # or 'PLAN_PASADO'? Check service logic.
            ).all()
            
            # OR Check source logic more broadly if source_type inconsistent
            history_all = db.query(HistorialConsumo).filter(
                HistorialConsumo.empresa_id == empresa.id,
                HistorialConsumo.fuente_id == plan_nov.id
            ).all()

            print(f"\n--- History Linked to Plan {plan_nov.id} ---")
            total_history = 0
            for h in history_all:
                print(f"Op: {h.tipo_operacion}, FuenteTipo: {h.fuente_tipo}, Cant: {h.cantidad}, Fecha: {h.fecha}")
                if h.tipo_operacion == 'CONSUMO':
                    total_history += h.cantidad
                elif h.tipo_operacion == 'REVERSION':
                    total_history -= h.cantidad
            
            print(f"Total Consumption from History: {total_history}")
            
            # 4. Check December Plan for context
            plan_dec = db.query(ControlPlanMensual).filter(
                 ControlPlanMensual.empresa_id == empresa.id,
                 ControlPlanMensual.anio == 2025,
                 ControlPlanMensual.mes == 12
            ).first()
            if plan_dec:
                print(f"\n--- Plan Dec 2025 ---")
                print(f"Disponible: {plan_dec.cantidad_disponible}")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_pelaez_data()
