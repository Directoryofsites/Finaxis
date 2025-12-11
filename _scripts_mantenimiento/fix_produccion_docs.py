from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.tipo_documento import TipoDocumento
from app.models.empresa import Empresa

def fix_production_docs():
    db: Session = SessionLocal()
    try:
        empresas = db.query(Empresa).all()
        for empresa in empresas:
            print(f"Processing Empresa: {empresa.razon_social} (ID: {empresa.id})")
            
            # 1. Consumo Producción
            consumo_doc = db.query(TipoDocumento).filter(
                TipoDocumento.empresa_id == empresa.id,
                TipoDocumento.codigo == 'CONSP'
            ).first()
            
            if not consumo_doc:
                print("  Creating 'Consumo Producción' (CONSP)...")
                consumo_doc = TipoDocumento(
                    empresa_id=empresa.id,
                    codigo='CONSP',
                    nombre='Consumo Producción',
                    consecutivo_actual=0,
                    numeracion_manual=False,
                    funcion_especial=None, # Or 'salida_produccion' if supported
                    afecta_inventario=True
                )
                db.add(consumo_doc)
            else:
                print("  'Consumo Producción' already exists.")

            # 2. Entrada Producción
            entrada_doc = db.query(TipoDocumento).filter(
                TipoDocumento.empresa_id == empresa.id,
                TipoDocumento.codigo == 'ENTRP'
            ).first()
            
            if not entrada_doc:
                print("  Creating 'Entrada Producción' (ENTRP)...")
                entrada_doc = TipoDocumento(
                    empresa_id=empresa.id,
                    codigo='ENTRP',
                    nombre='Entrada Producción',
                    consecutivo_actual=0,
                    numeracion_manual=False,
                    funcion_especial=None, # Or 'entrada_produccion' if supported
                    afecta_inventario=True
                )
                db.add(entrada_doc)
            else:
                print("  'Entrada Producción' already exists.")
        
        db.commit()
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_production_docs()
