import sys
import os

# Asegurar que el path del proyecto está en sys.path
sys.path.append(os.getcwd())

from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate_ph_config():
    print("Iniciando migración de PHConfiguracion...")
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # 1. Agregar cuenta_cartera_id
            try:
                conn.execute(text("ALTER TABLE ph_configuracion ADD COLUMN cuenta_cartera_id INTEGER REFERENCES plan_cuentas(id)"))
                print("Columna 'cuenta_cartera_id' agregada exitosamente.")
            except Exception as e:
                print(f"Nota: Columna 'cuenta_cartera_id' ya existía o error: {e}")

            # 2. Agregar cuenta_caja_id
            try:
                conn.execute(text("ALTER TABLE ph_configuracion ADD COLUMN cuenta_caja_id INTEGER REFERENCES plan_cuentas(id)"))
                print("Columna 'cuenta_caja_id' agregada exitosamente.")
            except Exception as e:
                print(f"Nota: Columna 'cuenta_caja_id' ya existía o error: {e}")
                
            conn.commit()
            print("Migración completada.")
        except Exception as e:
            print(f"Error general en la migración: {e}")

if __name__ == "__main__":
    migrate_ph_config()
