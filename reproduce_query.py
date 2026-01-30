import sys
import os
from sqlalchemy import func, extract
from datetime import date

# Add project root to path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.consumo_registros import HistorialConsumo, TipoOperacionConsumo

def reproduce_query():
    db = SessionLocal()
    PADRE_ID = 179
    target_year = 2026
    target_month = 1
    
    try:
        print(f"=== REPRODUCCIÓN DE QUERY (Empresa {PADRE_ID}, {target_month}/{target_year}) ===")
        
        # 1. Query Exacta del Dashboard
        total_consumo = db.query(func.sum(HistorialConsumo.cantidad)).filter(
            HistorialConsumo.empresa_id == PADRE_ID,
            extract('year', HistorialConsumo.fecha) == target_year,
            extract('month', HistorialConsumo.fecha) == target_month,
            HistorialConsumo.tipo_operacion == TipoOperacionConsumo.CONSUMO
        ).scalar() or 0
        
        print(f"Resultado Query Original (con Enum): {total_consumo}")
        
        # 2. Query Alternativa con String Literal
        total_consumo_str = db.query(func.sum(HistorialConsumo.cantidad)).filter(
            HistorialConsumo.empresa_id == PADRE_ID,
            extract('year', HistorialConsumo.fecha) == target_year,
            extract('month', HistorialConsumo.fecha) == target_month,
            HistorialConsumo.tipo_operacion == "CONSUMO"
        ).scalar() or 0
        
        print(f"Resultado Query String Literal: {total_consumo_str}")
        
         # 3. Query Alternativa usando .value
        total_consumo_val = db.query(func.sum(HistorialConsumo.cantidad)).filter(
            HistorialConsumo.empresa_id == PADRE_ID,
            extract('year', HistorialConsumo.fecha) == target_year,
            extract('month', HistorialConsumo.fecha) == target_month,
            HistorialConsumo.tipo_operacion == TipoOperacionConsumo.CONSUMO.value
        ).scalar() or 0
        
        print(f"Resultado Query Enum.value: {total_consumo_val}")


    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reproduce_query()
