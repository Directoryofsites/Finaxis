import os
import sys

sys.path.append(os.path.abspath('c:/ContaPY2'))
from app.core.database import SessionLocal
from app.models.documento import Documento
from app.models.tipo_documento import TipoDocumento

db = SessionLocal()

# Buscamos todos los tipos de documento y sus funciones especiales
tipos = db.query(TipoDocumento).all()

print(f"Tipos de Documento:")
for t in tipos:
    print(f"ID: {t.id} | Nombre: {t.nombre} | Funcion: {t.funcion_especial}")

db.close()
