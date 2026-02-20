
import sys
import os
sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.tipo_documento import TipoDocumento

def list_types():
    session = SessionLocal()
    try:
        empresa_id = 134
        types = session.query(TipoDocumento).filter_by(empresa_id=empresa_id).all()
        
        print(f"Total Types for Company {empresa_id}: {len(types)}")
        print("-" * 80)
        print(f"{'ID':<5} | {'COD':<10} | {'NOMBRE':<30} | {'FUNCION_ESPECIAL':<20}")
        print("-" * 80)
        
        for t in types:
            uid = str(t.id) if t.id else ""
            cod = str(t.codigo) if t.codigo else ""
            nom = str(t.nombre) if t.nombre else ""
            func = str(t.funcion_especial) if t.funcion_especial else "None"
            print(f"{uid:<5} | {cod:<10} | {nom:<30} | {func:<20}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    list_types()
