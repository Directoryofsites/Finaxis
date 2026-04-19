import os
import sys

sys.path.append(os.path.abspath('c:/ContaPY2'))
from app.core.database import SessionLocal
from app.models.documento import Documento
from app.models.tipo_documento import TipoDocumento

db = SessionLocal()

# Find all documents with numero == 13
docs = db.query(Documento).filter(Documento.numero == 13).all()
print("Documentos con numero 13:")
for d in docs:
    tipo = db.query(TipoDocumento).get(d.tipo_documento_id)
    print(f"ID={d.id}, empresa={d.empresa_id}, tipo={tipo.nombre}, tercero={d.beneficiario_id}, anulado={d.anulado}, estado={d.estado}, fecha={d.fecha}")

db.close()
