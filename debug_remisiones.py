import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.remision import Remision

db = SessionLocal()

print("-" * 50)
print(" INSPECCION DE REMISIONES")
print("-" * 50)

try:
    remisiones = db.query(Remision).all()

    if not remisiones:
        print("No existen remisiones en la base de datos.")
    else:
        for r in remisiones:
            print(f"ID: {r.id} | Numero: {r.numero} | Estado: {r.estado} | Cliente ID: {r.tercero_id}")
finally:
    db.close()

print("-" * 50)
