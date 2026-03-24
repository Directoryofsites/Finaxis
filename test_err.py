import traceback
import sys
import codecs

# Forcar stdout a utf-8 para que no tire charmap error al imprimir a la consola
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.services import migracion as migracion_service
import json

db = SessionLocal()
emp = db.query(Empresa).first()
try:
    print(f"Respaldando: {emp.razon_social}")
    backup_data = migracion_service.generar_backup_json(db, emp.id, filtros=None)
    json_str = json.dumps(backup_data, default=str, ensure_ascii=False)
    print("Success")
except Exception as e:
    traceback.print_exc()
