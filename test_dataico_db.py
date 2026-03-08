import json
import sys
import os
sys.path.append('C:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.documento import Documento

db = SessionLocal()
doc = db.query(Documento).filter(Documento.numero == 127).first()

if doc:
    print(f"Doc encontrado: {doc.numero}")
    print(doc.provider_response)
else:
    print("No encontrado")
