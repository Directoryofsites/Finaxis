from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services import dashboard

def verify():
    db = SessionLocal()
    try:
        empresa_id = 179 # Mejía (Contador)
        print(f"--- VERIFICACIÓN DASHBOARD (EMPRESA {empresa_id}) ---")
        
        # Test default (Current Month)
        stats = dashboard.get_consumo_actual(db, empresa_id)
        
        print(f"Resultado Stats:")
        print(f"   - Total Registros (Consumo): {stats['total_registros']}")
        print(f"   - Limite Registros: {stats['limite_registros']}")
        print(f"   - Porcentaje: {stats['porcentaje']}%")
        print(f"   - Estado: {stats['estado']}")
        
        if stats['total_registros'] >= 35:
            print("\n[EXITO] El dashboard ahora refleja el consumo global (>= 35).")
        else:
            print("\n[FALLO] El dashboard sigue mostrando consumo bajo.")

    finally:
        db.close()

if __name__ == "__main__":
    verify()
