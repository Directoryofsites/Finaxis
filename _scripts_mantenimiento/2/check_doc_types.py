import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add app to path
sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.tipo_documento import TipoDocumento

def list_doc_types():
    db = SessionLocal()
    try:
        types = db.query(TipoDocumento).all()
        print(f"Found {len(types)} document types:")
        for t in types:
            print(f"- ID: {t.id}, Codigo: '{t.codigo}', Nombre: '{t.nombre}'")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    list_doc_types()
