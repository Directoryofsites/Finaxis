
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services import cartera as cartera_service
from app.models.propiedad_horizontal import PHConfiguracion

DATABASE_URL = "sqlite:///./contapy.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def check_accounts():
    empresa_id = 1 # Supongo 1 o 2. Vamos a ver.
    configs = db.query(PHConfiguracion).all()
    for config in configs:
        print(f"EMPRESA ID: {config.empresa_id}")
        cxc_ids = cartera_service.get_cuentas_especiales_ids(db, config.empresa_id, 'cxc')
        print(f"  CUENTAS CXC: {cxc_ids}")
        print(f"  CUENTA CARTERA GLOBAL: {config.cuenta_cartera_id}")
        print(f"  CUENTA ANTICIPOS: {config.cuenta_anticipos_id}")

db.close()

if __name__ == "__main__":
    check_accounts()
