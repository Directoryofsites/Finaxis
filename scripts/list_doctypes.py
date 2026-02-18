import sys
import os
sys.path.append(os.getcwd())
from app.core.database import SessionLocal
from app.models.tipo_documento import TipoDocumento

db = SessionLocal()
tipos = db.query(TipoDocumento).all()
for t in tipos:
    print(f"ID: {t.id}, Nombre: {t.nombre}, Codigo: {t.codigo}")
db.close()
