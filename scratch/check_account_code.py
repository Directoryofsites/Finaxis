
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.plan_cuenta import PlanCuenta

DATABASE_URL = "sqlite:///./contapy.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def check_account_code():
    ids = [92, 169]
    accounts = db.query(PlanCuenta).filter(PlanCuenta.id.in_(ids)).all()
    for a in accounts:
        print(f"ID: {a.id} | Codigo: {a.codigo} | Nombre: {a.nombre}")

db.close()

if __name__ == "__main__":
    check_account_code()
