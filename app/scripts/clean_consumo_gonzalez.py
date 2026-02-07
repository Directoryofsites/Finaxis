
from app.core.database import SessionLocal
from app.models.consumo_registros import HistorialConsumo, BolsaExcedente, ControlPlanMensual
from app.models.empresa import Empresa
from sqlalchemy import text

def clean_data():
    db = SessionLocal()
    empresa_id = 176 # Gonzalez Asesores
    
    print(f"--- LIMPIEZA DE CONSUMO PARA EMPRESA ID {empresa_id} ---")
    
    # 1. Eliminar Historial
    deleted_historial = db.query(HistorialConsumo).filter(HistorialConsumo.empresa_id == empresa_id).delete()
    print(f"Eliminados {deleted_historial} registros de historial.")

    # 2. Eliminar Bolsas (Para quitar el ruido de 'Cierre BOLSA')
    # OJO: Eliminar bolsas significa que perderán lo acumulado. El usuario dijo "No me interesa... limpiar esto".
    # Asumimos que quiere empezar limpia la prueba.
    deleted_bolsas = db.query(BolsaExcedente).filter(BolsaExcedente.empresa_id == empresa_id).delete()
    print(f"Eliminados {deleted_bolsas} registros de bolsas excedentes.")

    # 3. Resetear Control Plan Mensual (Poner consumo a 0)
    planes = db.query(ControlPlanMensual).filter(ControlPlanMensual.empresa_id == empresa_id).all()
    for plan in planes:
        # Resetear disponibilidad al límite total (Consumo = 0)
        plan.cantidad_disponible = plan.limite_asignado
        plan.estado = 'ABIERTO'  # Asegurar que esté abierto
        # plan.cantidad_consumida = 0 # No existe atributo físico 
    
    print(f"Reseteados {len(planes)} registros de control mensual a 0 consumo.")
    
    db.commit()
    print("--- LIMPIEZA COMPLETADA EXITOSAMENTE ---")
    db.close()

if __name__ == "__main__":
    clean_data()
