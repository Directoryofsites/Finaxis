import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the project root to the python path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.services.plan_cuenta import reparar_jerarquia_puc

def main():
    db = SessionLocal()
    try:
        # Assuming Company ID 5 based on previous context
        empresa_id = 5 
        print(f"Reparando jerarquía para empresa {empresa_id}...")
        result = reparar_jerarquia_puc(db, empresa_id)
        print(result)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
