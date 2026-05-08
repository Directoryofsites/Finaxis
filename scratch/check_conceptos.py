
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.propiedad_horizontal.concepto import PHConcepto

DATABASE_URL = "sqlite:///./contapy.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def check_conceptos():
    empresa_id = 2
    conceptos = db.query(PHConcepto).filter(PHConcepto.empresa_id == empresa_id).all()
    print(f"CONCEPTOS EMPRESA {empresa_id}:")
    for c in conceptos:
        print(f"ID: {c.id} | Nombre: {c.nombre} | Ingreso: {c.cuenta_ingreso_id} | CXC: {c.cuenta_cxc_id}")

db.close()

if __name__ == "__main__":
    check_conceptos()
