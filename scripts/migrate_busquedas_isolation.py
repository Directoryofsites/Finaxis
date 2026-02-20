import sys
import os

# Ajustar path para importar app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine

def run_migration():
    print("Iniciando migración: Agregar empresa_id a usuarios_busquedas_guardadas...")
    with engine.connect() as connection:
        try:
            # PostgreSQL check if column exists might be complex, so we try adding it and catch error if it exists?
            # Better to use IF NOT EXISTS if supported or check schema.
            # Simple approach: Check information schema
            
            check_sql = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='usuarios_busquedas_guardadas' AND column_name='empresa_id';
            """)
            result = connection.execute(check_sql).fetchone()
            
            if not result:
                print("Columna empresa_id no existe. Creando...")
                alter_sql = text("""
                    ALTER TABLE usuarios_busquedas_guardadas 
                    ADD COLUMN empresa_id INTEGER REFERENCES empresas(id);
                """)
                connection.execute(alter_sql)
                connection.commit()
                print("Columna creada exitosamente.")
            else:
                print("La columna empresa_id ya existe.")
                
        except Exception as e:
            print(f"Error durante la migración: {e}")

if __name__ == "__main__":
    run_migration()
