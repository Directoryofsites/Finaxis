from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.schemas.empresa import EmpresaConUsuarios
import json

db = SessionLocal()
emp = db.query(Empresa).first()
if emp:
    print(f"DB Model limite_mensajes_ia_mensual: {emp.limite_mensajes_ia_mensual}")
    schema_dump = EmpresaConUsuarios.model_validate(emp).model_dump()
    print("Schema Keys:")
    print("limite_mensajes_ia_mensual" in schema_dump)
    print(f"Schema Value: {schema_dump.get('limite_mensajes_ia_mensual')}")
else:
    print("No empresas found.")
db.close()
