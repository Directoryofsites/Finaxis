import sys
import os
from sqlalchemy.orm import Session

# Add project root to path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.empresa import Empresa

def diagnose_companies():
    db = SessionLocal()
    try:
        print("=== DIAGNÓSTICO DE EMPRESAS Y RELACIONES ===")
        empresas = db.query(Empresa).all()
        
        padres = {e.id: e.razon_social for e in empresas}
        
        print(f"{'ID':<5} | {'Nombre':<30} | {'NIT':<15} | {'Padre ID':<10} | {'Nombre Padre'}")
        print("-" * 80)
        
        for e in empresas:
            padre_nombre = padres.get(e.padre_id, "---") if e.padre_id else "---"
            print(f"{e.id:<5} | {e.razon_social:<30} | {e.nit:<15} | {str(e.padre_id):<10} | {padre_nombre}")
            
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        db.close()

if __name__ == "__main__":
    diagnose_companies()
