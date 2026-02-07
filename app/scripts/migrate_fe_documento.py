
import sys
import os

# Add parent directory to path to import app
sys.path.append(os.getcwd())

from app.core.database import SessionLocal, engine, Base
from sqlalchemy import text

def migrate_fe_documento():
    print("--- STARTING MIGRATION: ELECTRONIC INVOICING FIELDS FOR DOCUMENTO ---")
    
    with engine.connect() as connection:
        trans = connection.begin()
        try:
            # Add Columns to DOCUMENTOS
            columns = [
                ("dian_estado", "VARCHAR(20)"),
                ("dian_cufe", "VARCHAR(255)"),
                ("dian_xml_url", "VARCHAR(500)"),
                ("dian_error", "TEXT")
            ]
            
            for col_name, col_type in columns:
                print(f"Checking 'documentos.{col_name}'...")
                res = connection.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='documentos' AND column_name='{col_name}'"))
                if not res.fetchone():
                    print(f"Adding '{col_name}' to documentos...")
                    connection.execute(text(f"ALTER TABLE documentos ADD COLUMN {col_name} {col_type}"))
                else:
                    print(f"Column '{col_name}' exists.")

            trans.commit()
            print("--- MIGRATION COMPLETE SUCCESSFUL ---")
            
        except Exception as e:
            trans.rollback()
            print(f"--- MIGRATION FAILED: {e} ---")

if __name__ == "__main__":
    migrate_fe_documento()
