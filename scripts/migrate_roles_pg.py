import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    engine = create_engine(settings.DATABASE_URL)
    connection = engine.connect()
    
    try:
        print("Iniciando migración de Roles...")
        
        # 1. Agregar columna empresa_id si no existe
        print("-> Agregando columna empresa_id...")
        connection.execute(text("ALTER TABLE roles ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE;"))
        
        # 2. Eliminar restricciones antiguas de unicidad
        # Intentamos eliminar tanto el constraint potential como el índice
        print("-> Eliminando restricciones antiguas...")
        try:
            connection.execute(text("ALTER TABLE roles DROP CONSTRAINT IF EXISTS roles_nombre_key;"))
        except Exception as e:
            print(f"Nota: No se pudo eliminar constraint roles_nombre_key (puedes ignorar si no existía): {e}")
            
        try:
            connection.execute(text("DROP INDEX IF EXISTS ix_roles_nombre;"))
        except Exception as e:
            print(f"Nota: No se pudo eliminar índice ix_roles_nombre (puedes ignorar si no existía): {e}")

        # 3. Crear nuevos índices parciales para garantizar unicidad correcta
        print("-> Creando nuevos índices de unicidad...")
        
        # Unicidad para roles globales (empresa_id IS NULL)
        connection.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_roles_global 
            ON roles (nombre) 
            WHERE empresa_id IS NULL;
        """))
        
        # Unicidad para roles por empresa (empresa_id IS NOT NULL)
        connection.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_roles_empresa 
            ON roles (nombre, empresa_id) 
            WHERE empresa_id IS NOT NULL;
        """))

        connection.commit()
        print("¡Migración completada exitosamente!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        connection.rollback()
    finally:
        connection.close()

if __name__ == "__main__":
    run_migration()
