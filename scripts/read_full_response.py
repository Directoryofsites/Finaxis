import sys
import os
import json

sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.documento import Documento

def read_full_response():
    session = SessionLocal()
    try:
        doc_id = 12252
        doc = session.query(Documento).filter_by(id=doc_id).first()
        if doc:
            print(f"--- Doc ID: {doc.id} | Numero: {doc.numero} ---")
            print(f"DIAN Estado: {doc.dian_estado}")
            print(f"Contenido dian_error:")
            print(doc.dian_error)
        else:
            print(f"ERROR: No se encontró el documento con ID {doc_id}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    read_full_response()
