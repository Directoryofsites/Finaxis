
import sys
import os

# Add parent directory to path to import app
sys.path.append(os.getcwd())

from app.core.database import SessionLocal, engine, Base
from sqlalchemy import text
from app.models.configuracion_fe import ConfiguracionFE # Import to register metadata

def migrate_fe_schema():
    print("--- STARTING MIGRATION: ELECTRONIC INVOICING FIELDS ---")
    
    # 1. Create New Tables (ConfiguracionFE)
    print("Creating new tables if not exist (ConfiguracionFE)...")
    Base.metadata.create_all(bind=engine)
    
    with engine.connect() as connection:
        trans = connection.begin()
        try:
            # 2. Add Columns to EMPRESAS
            columns_empresa = [
                ("dv", "VARCHAR(1)"),
                ("tipo_documento", "VARCHAR(5) DEFAULT '31'"),
                ("tipo_persona", "VARCHAR(1) DEFAULT '1'"),
                ("regimen_fiscal", "VARCHAR(5) DEFAULT '48'"),
                ("responsabilidad_fiscal", "VARCHAR(20) DEFAULT 'R-99-PN'"),
                ("municipio_dane", "VARCHAR(10)"),
                ("codigo_postal", "VARCHAR(10)")
            ]
            
            for col_name, col_type in columns_empresa:
                print(f"Checking 'empresas.{col_name}'...")
                res = connection.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='empresas' AND column_name='{col_name}'"))
                if not res.fetchone():
                    print(f"Adding '{col_name}' to empresas...")
                    connection.execute(text(f"ALTER TABLE empresas ADD COLUMN {col_name} {col_type}"))
                else:
                    print(f"Column '{col_name}' exists.")

            # 3. Add Columns to TERCEROS
            columns_tercero = [
                ("tipo_documento", "VARCHAR(5) DEFAULT '13'"),
                ("tipo_persona", "VARCHAR(1) DEFAULT '2'"),
                ("municipio_dane", "VARCHAR(10)"),
                ("codigo_postal", "VARCHAR(10)"),
                ("regimen_fiscal", "VARCHAR(5)"),
                ("responsabilidad_fiscal", "VARCHAR(20)")
            ]
            
            for col_name, col_type in columns_tercero:
                print(f"Checking 'terceros.{col_name}'...")
                res = connection.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='terceros' AND column_name='{col_name}'"))
                if not res.fetchone():
                    print(f"Adding '{col_name}' to terceros...")
                    connection.execute(text(f"ALTER TABLE terceros ADD COLUMN {col_name} {col_type}"))
                else:
                    print(f"Column '{col_name}' exists.")

            trans.commit()
            print("--- MIGRATION COMPLETE SUCCESSFUL ---")
            
        except Exception as e:
            trans.rollback()
            print(f"--- MIGRATION FAILED: {e} ---")

if __name__ == "__main__":
    migrate_fe_schema()
