
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.tercero import Tercero

DATABASE_URL = "sqlite:///./contapy.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def check_tercero():
    t = db.query(Tercero).filter(Tercero.id == 12).first()
    if t:
        print(f"TERCERO ID 12: {t.razon_social}")
    else:
        print("Tercero 12 no encontrado")

db.close()

if __name__ == "__main__":
    check_tercero()
