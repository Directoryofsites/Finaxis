import sqlalchemy
from sqlalchemy import create_engine, text
import sys
import os

# Add current directory to path so we can import app
sys.path.append(os.getcwd())

from app.core.config import settings

def apply_migration():
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        print("Checking/Applying schema changes...")
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")
        
        # 1. Add documento_referencia_id to documentos
        try:
            conn.execute(text("ALTER TABLE documentos ADD COLUMN documento_referencia_id INTEGER REFERENCES documentos(id);"))
            print("Added column: documento_referencia_id to documentos")
        except sqlalchemy.exc.ProgrammingError as e:
            if "already exists" in str(e):
                print("Column documento_referencia_id already exists.")
            else:
                print(f"Error adding column documento_referencia_id: {e}")

        # 2. Add nc_rango_id to configuracion_fe
        try:
            conn.execute(text("ALTER TABLE configuracion_fe ADD COLUMN nc_rango_id INTEGER;"))
            print("Added column: nc_rango_id to configuracion_fe")
        except sqlalchemy.exc.ProgrammingError as e:
            if "already exists" in str(e):
                print("Column nc_rango_id already exists.")
            else:
                print(f"Error adding column nc_rango_id: {e}")

        # 3. Add nd_rango_id to configuracion_fe
        try:
            conn.execute(text("ALTER TABLE configuracion_fe ADD COLUMN nd_rango_id INTEGER;"))
            print("Added column: nd_rango_id to configuracion_fe")
        except sqlalchemy.exc.ProgrammingError as e:
            if "already exists" in str(e):
                print("Column nd_rango_id already exists.")
            else:
                print(f"Error adding column nd_rango_id: {e}")

if __name__ == "__main__":
    apply_migration()
