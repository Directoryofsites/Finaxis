
import sys
import os
sys.path.append(os.getcwd())
from app.core.database import SessionLocal
from sqlalchemy import text

def check_fe_error(doc_id):
    db = SessionLocal()
    try:
        res = db.execute(text(f"SELECT dian_estado, dian_error FROM documentos WHERE id = {doc_id}")).fetchone()
        if res:
            print(f"Estado: {res[0]}")
            print(f"Error Completo: {res[1]}")
    finally:
        db.close()

if __name__ == "__main__":
    db = SessionLocal()
    max_id = db.execute(text("SELECT MAX(id) FROM documentos")).fetchone()[0]
    db.close()
    print(f"Checking Doc ID: {max_id}")
    check_fe_error(max_id)
