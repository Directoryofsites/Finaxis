import sys
import os
import re

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.models.nomina import DetalleNomina
from app.models import Documento, Empresa

# Database connection
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:mysecretpassword@localhost:5432/contapy_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def fix_links():
    db = SessionLocal()
    try:
        print("Iniciando reparación de vínculos Nómina -> Contabilidad...")
        
        # 1. Obtener detalles sin vínculo
        detalles = db.query(DetalleNomina).filter(DetalleNomina.documento_contable_id == None).all()
        print(f"Encontrados {len(detalles)} detalles sin vínculo.")
        
        updated_count = 0
        
        for d in detalles:
            ref_str = f"Ref: {d.id}"
            
            # Buscar documento que contenga esa referencia
            # Optimización: Filtrar por fecha cercana si fuera posible, pero por ahora scan
            # Como optimización, buscamos documentos que NO estén anulados preferiblemente
            doc = db.query(Documento).filter(
                Documento.observaciones.contains(ref_str),
                Documento.estado != 'ANULADO'
            ).first()
            
            if doc:
                d.documento_contable_id = doc.id
                updated_count += 1
                print(f"[OK] Detalle {d.id} vinculado a Documento {doc.id} ({doc.numero})")
            else:
                # Intento buscar en anulados por si acaso
                doc_anulado = db.query(Documento).filter(
                    Documento.observaciones.contains(ref_str)
                ).first()
                if doc_anulado:
                     d.documento_contable_id = doc_anulado.id
                     updated_count += 1
                     print(f"[OK-ANULADO] Detalle {d.id} vinculado a Documento {doc_anulado.id} (ANULADO)")
                else:
                    print(f"[WARN] No se encontró documento para Detalle {d.id}")
        
        db.commit()
        print(f"Reparación completada. {updated_count} registros actualizados.")
        
    except Exception as e:
        print(f"Error crítico: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_links()
