import sys
import os

sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.documento import Documento

def find_last_accepted():
    session = SessionLocal()
    try:
        empresa_id = 218
        doc = session.query(Documento).filter_by(empresa_id=empresa_id, dian_estado='ACEPTADO').order_by(Documento.numero.desc()).first()
        if doc:
            print(f"Último Aceptado: No {doc.numero} (ID: {doc.id})")
        else:
            print("No se encontraron documentos aceptados para la empresa 218")
            
        # También ver los últimos 5 para contexto
        last_docs = session.query(Documento).filter_by(empresa_id=empresa_id).order_by(Documento.id.desc()).limit(10).all()
        print("\nÚltimos 10 documentos:")
        for d in last_docs:
            print(f"ID: {d.id} | No: {d.numero} | Estado: {d.dian_estado} | Error: {d.dian_error[:30] if d.dian_error else 'N/A'}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    find_last_accepted()
