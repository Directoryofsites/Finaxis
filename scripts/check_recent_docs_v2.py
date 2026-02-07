import sys
import os

# Asegurar que el directorio raíz esté en el path
sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.documento import Documento
from datetime import datetime, timedelta

def check_recent_docs():
    session = SessionLocal()
    try:
        empresa_id = 218
        # Buscar docs de las últimas 2 horas
        since = datetime.utcnow() - timedelta(hours=2)
        docs = session.query(Documento).filter(
            Documento.empresa_id == empresa_id,
            Documento.created_at >= since
        ).order_by(Documento.id.desc()).all()
        
        print(f"Encontrados {len(docs)} documentos recientes para empresa {empresa_id}:")
        for d in docs:
            print(f"ID: {d.id} | No: {d.numero} | Estado DIAN: {d.dian_estado} | Error: {d.dian_error[:100] if d.dian_error else 'N/A'}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_recent_docs()
