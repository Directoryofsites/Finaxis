import requests
import json
import os

# Create an auth token based on standard credentials
# Usually finaxis seed has a default user or we can just fetch one from DB
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.database import SessionLocal
from app.models.usuario import Usuario

db = SessionLocal()
user = db.query(Usuario).first()
if not user:
    print("No users found.")
    sys.exit()

# Wait, instead of running HTTP, I can just call the router endpoint directly 
# since I can import Depends and pass the session and user directly!

from app.api.utilidades.routes import exportar_datos
from app.schemas.migracion import ExportRequest

payload = {
    "paquetes": {
        "maestros": {},
        "modulos_especializados": {},
        "configuraciones": {},
        "transacciones_contabilidad": True
    },
    "cuentaId": 51159501
}
req = ExportRequest(**payload)

from app.models.movimiento_contable import MovimientoContable
mov = db.query(MovimientoContable).first()
if mov:
    req.cuentaId = mov.cuenta_id
    print(f"Testing filter with cuentaId = {req.cuentaId}")

try:
    response = exportar_datos(export_request=req, db=db, current_user=user)
    print("Respuesta del generador:")
    # the response is a FastAPI Response object...
    import json
    data_dict = json.loads(response.body)
    docs = data_dict.get("data", {}).get("transacciones", [])
    print(f"Total documentos exportados en JSON = {len(docs)}")
except Exception as e:
    print(f"Error test local: {e}")

db.close()
