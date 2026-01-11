
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.core.config import settings
from app.models.empresa import Empresa

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_companies():
    db = SessionLocal()
    try:
        empresas = db.query(Empresa).all()
        print(f"Total Companies Found: {len(empresas)}")
        for i, emp in enumerate(empresas):
            print(f"{i+1}. ID: {emp.id}, NIT: {emp.nit}, Razon Social: {emp.razon_social}")
            print(f"   Usuarios count: {len(emp.usuarios)}")
    except Exception as e:
        print(f"Error querying database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_companies()
