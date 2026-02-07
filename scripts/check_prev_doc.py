import sys
import os

sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.documento import Documento

def check_prev_doc():
    session = SessionLocal()
    try:
        empresa_id = 218
        numero = 23
        doc = session.query(Documento).filter_by(empresa_id=empresa_id, numero=numero).first()
        if doc:
            print(f"Doc 23 ID: {doc.id}")
            print(f"Estado DIAN: {doc.dian_estado}")
            print(f"CUFE: {doc.dian_cufe}")
            print(f"Error: {doc.dian_error}")
        else:
            print("No se encontró el documento 23 para la empresa 218")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_prev_doc()
