import sys
import os

sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.documento import Documento

def save_error_to_file():
    session = SessionLocal()
    try:
        doc_id = 12252
        doc = session.query(Documento).filter_by(id=doc_id).first()
        if doc and doc.dian_error:
            with open('c:\\ContaPY2\\scripts\\debug_dian_error.json', 'w', encoding='utf-8') as f:
                f.write(doc.dian_error)
            print("Archivo scripts\\debug_dian_error.json creado con éxito.")
        else:
            print("No hay dian_error o doc no encontrado")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    save_error_to_file()
