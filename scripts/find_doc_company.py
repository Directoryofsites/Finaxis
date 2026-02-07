
import sys
sys.path.append('c:\\ContaPY2')
from app.core.database import SessionLocal
from app.models.documento import Documento

def find_company_by_doc():
    session = SessionLocal()
    try:
        doc_id = 12223
        doc = session.query(Documento).filter_by(id=doc_id).first()
        if doc:
            print(f"DOCUMENTO {doc_id} ENCONTRADO.")
            print(f"Empresa ID: {doc.empresa_id}")
            print(f"Consecutivo: {doc.consecutivo}")
        else:
            print(f"Documento {doc_id} NO encontrado.")
    finally:
        session.close()

if __name__ == "__main__":
    find_company_by_doc()
