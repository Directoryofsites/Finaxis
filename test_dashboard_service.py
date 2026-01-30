import sys
import os
from datetime import date

# Add project root to path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.services import dashboard as dashboard_service

def test_dashboard():
    db = SessionLocal()
    PADRE_ID = 179
    MES = 1
    ANIO = 2026
    
    try:
        print(f"=== TEST DASHBOARD SERVICE (Empresa {PADRE_ID}) ===")
        
        result = dashboard_service.get_consumo_actual(db, PADRE_ID, mes=MES, anio=ANIO)
        
        print(f"Resultado Función: {result}")
        
        if result['total_registros'] == 42:
            print(">> DEPURACIÓN EXITOSA: La función retorna el valor correcto (42).")
            print(">> CAUSA PROBABLE: El Frontend está enviando mal los parámetros o consultando otra empresa/fecha.")
        else:
            print(f">> ERROR: La función retorna {result['total_registros']}, pero esperábamos 42.")

    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_dashboard()
