import sys
import os
sys.path.append(os.getcwd())
from app.core.database import SessionLocal
from app.models.consumo_registros import BolsaExcedente, EstadoBolsa

def check_bolsas():
    db = SessionLocal()
    try:
        bolsas = db.query(BolsaExcedente).all()
        print(f"Total bolsas encontradas: {len(bolsas)}")
        for b in bolsas:
            print(f"ID: {b.id} | Origen: {b.mes_origen}/{b.anio_origen} | Vence: {b.fecha_vencimiento} | Estado: {b.estado}")
    finally:
        db.close()

if __name__ == "__main__":
    check_bolsas()
