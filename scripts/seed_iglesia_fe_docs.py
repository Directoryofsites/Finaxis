
import sys
import os

# Ajustar path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.models.tipo_documento import TipoDocumento

def seed_fe_documents(empresa_id):
    session = SessionLocal()
    try:
        print(f"Verificando Tipos de Documento FE para Empresa ID {empresa_id}...")
        
        docs_to_create = [
            {
                "nombre": "Factura Electrónica de Venta",
                "codigo": "FE", # Usamos prefijo como código interno
                "consecutivo_actual": 0,
                "funcion_especial": "factura_venta",
                "es_venta": True
            },
            {
                "nombre": "Documento Soporte Electrónico",
                "codigo": "DS",
                "consecutivo_actual": 0,
                "funcion_especial": "documento_soporte",
                "es_compra": True
            },
            {
                "nombre": "Nota Crédito Electrónica",
                "codigo": "NCE",
                "consecutivo_actual": 0,
                "funcion_especial": None,
                "es_venta": True # Rebaja la venta
            },
            {
                "nombre": "Nota Débito Electrónica",
                "codigo": "NDE",
                "consecutivo_actual": 0,
                "funcion_especial": None,
                "es_venta": True # Aumenta la venta
            }
        ]
        
        for d in docs_to_create:
            exists = session.query(TipoDocumento).filter_by(
                empresa_id=empresa_id, 
                nombre=d["nombre"]
            ).first()
            
            if not exists:
                print(f"Creando: {d['nombre']}")
                new_doc = TipoDocumento(
                    empresa_id=empresa_id,
                    **d
                )
                session.add(new_doc)
            else:
                print(f"Ya existe: {d['nombre']}")
                
        session.commit()
        print("✅ Tipos de Documento FE listos.")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    emp_id = 140 # Iglesia por defecto
    seed_fe_documents(emp_id)
