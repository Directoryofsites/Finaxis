
import sys
import os

# Agrega el directorio raíz del proyecto al sys.path para poder importar app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app.core.database import SessionLocal

def add_column():
    db = SessionLocal()
    try:
        print("Intentando agregar columna 'factura_rango_id' a 'configuracion_fe'...")
        # Postgres / SQLite compatible basic add column (if not exists logic is harder in raw sql cross-db, but let's try)
        # We assume Postgres for production based on previous context, but local might be sqlite.
        # This command is generally compatible for adding nullable columns.
        
        # Check if column exists first to avoid error
        check_sql = text("SELECT count(*) FROM information_schema.columns WHERE table_name='configuracion_fe' AND column_name='factura_rango_id';")
        try:
            result = db.execute(check_sql).scalar()
            if result > 0:
                print("La columna 'factura_rango_id' YA EXISTE. No se realizaron cambios.")
                return
        except Exception as e:
            print(f"No se pudo verificar existencia (probablemente SQLite local?): {e}")
            # Fallback for SQLite or just try adding it
            pass

        sql = text("ALTER TABLE configuracion_fe ADD COLUMN factura_rango_id INTEGER;")
        db.execute(sql)
        db.commit()
        print("Columna 'factura_rango_id' agregada EXITOSAMENTE.")
    except Exception as e:
        print(f"Error al agregar columna (puede que ya exista): {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_column()
