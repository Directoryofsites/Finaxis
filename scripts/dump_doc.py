import sys
import os
import json

sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.documento import Documento

def dump_doc():
    session = SessionLocal()
    try:
        doc_id = 12252
        doc = session.query(Documento).filter_by(id=doc_id).first()
        if doc:
            data = {c.name: getattr(doc, c.name) for c in doc.__table__.columns}
            # Convertir objetos no serializables
            for k, v in data.items():
                if hasattr(v, 'isoformat'): data[k] = v.isoformat()
                elif hasattr(v, '__str__'): 
                    if not isinstance(v, (str, int, float, bool, type(None))):
                        data[k] = str(v)
            
            print("--- DUMP DOC 12252 ---")
            print(json.dumps(data, indent=2))
        else:
            print("No se encontró doc 12252")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    dump_doc()
