import sys
import os

# Asegurar que el path del proyecto está en sys.path
sys.path.append(os.getcwd())

from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate_ph_conceptos_v2():
    print("Iniciando migración v2 de PHConceptos...")
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # 1. Agregar tipo_documento_recibo_id
            try:
                conn.execute(text("ALTER TABLE ph_conceptos ADD COLUMN tipo_documento_recibo_id INTEGER REFERENCES tipos_documento(id)"))
                print("Columna 'tipo_documento_recibo_id' agregada exitosamente.")
            except Exception as e:
                print(f"Nota: Columna 'tipo_documento_recibo_id' ya existía o error: {e}")

            # 2. Agregar cuenta_caja_id
            try:
                conn.execute(text("ALTER TABLE ph_conceptos ADD COLUMN cuenta_caja_id INTEGER REFERENCES plan_cuentas(id)"))
                print("Columna 'cuenta_caja_id' agregada exitosamente.")
            except Exception as e:
                print(f"Nota: Columna 'cuenta_caja_id' ya existía o error: {e}")
                
            conn.commit()
            print("Migración v2 de conceptos completada.")
        except Exception as e:
            print(f"Error general en la migración: {e}")

if __name__ == "__main__":
    migrate_ph_conceptos_v2()
