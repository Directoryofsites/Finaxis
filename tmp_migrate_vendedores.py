import sys
import os
from sqlalchemy import create_engine, text

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.core.config import settings

def migrate():
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        print("Iniciando migración de base de datos para Vendedores...")
        
        # 1. Agregar es_vendedor a terceros
        try:
            conn.execute(text("ALTER TABLE terceros ADD COLUMN es_vendedor BOOLEAN DEFAULT FALSE"))
            conn.commit()
            print("- Columna 'es_vendedor' añadida a 'terceros'")
        except Exception as e:
            print(f"- Error o ya existe 'es_vendedor' en 'terceros': {e}")

        # 2. Agregar vendedor_id a documentos
        try:
            conn.execute(text("ALTER TABLE documentos ADD COLUMN vendedor_id INTEGER REFERENCES terceros(id)"))
            conn.commit()
            print("- Columna 'vendedor_id' añadida a 'documentos'")
        except Exception as e:
            print(f"- Error o ya existe 'vendedor_id' en 'documentos': {e}")
            
        print("Migración completada.")

if __name__ == "__main__":
    migrate()
