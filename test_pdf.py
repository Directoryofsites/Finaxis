import sys
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.documento import Documento
from app.services.documento import generar_pdf_documento

db = SessionLocal()
try:
    doc = db.query(Documento).filter(Documento.id == 13550).first()
    print(Empresa: , doc.empresa_id if doc else No encontrado)
    pdf, name = generar_pdf_documento(db, 13550, doc.empresa_id)
    print(EXITO)
except Exception as e:
    import traceback
    traceback.print_exc()

