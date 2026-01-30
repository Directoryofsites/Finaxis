import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.empresa import Empresa

def fix_limits():
    db = SessionLocal()
    try:
        # Buscar empresas hijas (con padre) que tengan límite > 0
        hijas = db.query(Empresa).filter(Empresa.padre_id != None).all()
        count = 0
        for h in hijas:
            if h.limite_registros_mensual != 0:
                print(f"Corrigiendo empresa {h.razon_social}: Límite {h.limite_registros_mensual} -> 0")
                h.limite_registros_mensual = 0
                count += 1
        
        db.commit()
        print(f"Total empresas corregidas: {count}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_limits()
