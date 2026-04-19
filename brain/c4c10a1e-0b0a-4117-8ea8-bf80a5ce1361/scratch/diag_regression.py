import os
import sys

sys.path.append(os.path.abspath('c:/ContaPY2'))
from app.core.database import SessionLocal
from app.models.documento import Documento
from app.models.tipo_documento import TipoDocumento

db = SessionLocal()

# Buscamos Documento #125 en todo el sistema
docs = db.query(Documento).filter(Documento.numero == 125).all()

print(f"--- BUSQUEDA GLOBAL DOC #125 ---")
for d in docs:
    tipo = db.query(TipoDocumento).get(d.tipo_documento_id)
    print(f"ID: {d.id} | Emp: {d.empresa_id} | Tipo: {tipo.nombre if tipo else 'N/A'} | Fecha: {d.fecha} | Benef: {d.beneficiario_id}")

db.close()
