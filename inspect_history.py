import sys
import os
from sqlalchemy import func
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.consumo_registros import HistorialConsumo

def inspect_history():
    db = SessionLocal()
    PADRE_ID = 179 # Mejia y Mejia Tributos
    try:
        print(f"=== INSPECCIÓN DE HISTORIAL DE CONSUMO (Empresa {PADRE_ID}) ===")
        
        # 1. Conteo total
        count = db.query(HistorialConsumo).filter(HistorialConsumo.empresa_id == PADRE_ID).count()
        print(f"Total registros encontrados: {count}")

        # 2. Listar últimos 10
        registros = db.query(HistorialConsumo).filter(
            HistorialConsumo.empresa_id == PADRE_ID
        ).order_by(HistorialConsumo.fecha.desc()).limit(10).all()
        
        if not registros:
            print("No hay registros recientes.")
        else:
            print(f"{'ID':<5} | {'Fecha':<20} | {'Tipo':<10} | {'Cant':<5} | {'Fuente':<10} | {'Doc ID'}")
            print("-" * 80)
            for r in registros:
                print(f"{r.id:<5} | {str(r.fecha):<20} | {r.tipo_operacion:<10} | {r.cantidad:<5} | {r.fuente_tipo:<10} | {r.documento_id}")

    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_history()
