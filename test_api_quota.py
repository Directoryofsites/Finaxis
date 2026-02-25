from app.core.database import SessionLocal
from app.services.soporte import search_empresas
import json

db = SessionLocal()
response = search_empresas(db, page=1, size=100)

for item in response.items:
    dump = item.model_dump()
    val = dump.get("limite_mensajes_ia_mensual")
    print(f"Empresa: {dump.get('razon_social')} | ID: {dump.get('id')} | Cuota IA: {val}")

db.close()
