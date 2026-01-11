import sys
import os

# Agregamos el directorio raíz al path para poder importar módulos de la app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine
from sqlalchemy import text

def add_column_if_not_exists():
    db = SessionLocal()
    try:
        # PostgreSQL syntax for adding column if not exists
        # Note: 'IF NOT EXISTS' in ADD COLUMN is available in PG 9.6+
        # But we can also check via catch exception or information_schema.
        
        # Simple approach: Try to add, pass if fails (usually means exists)
        print("Intentando agregar columna 'precio_por_registro' a tabla 'empresas'...")
        db.execute(text("ALTER TABLE empresas ADD COLUMN IF NOT EXISTS precio_por_registro INTEGER DEFAULT NULL"))
        db.commit()
        print("Columna verificada/agregada exitosamente.")
        
    except Exception as e:
        print(f"Nota: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_column_if_not_exists()
