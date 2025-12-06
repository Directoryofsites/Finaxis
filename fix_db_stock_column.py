import sys
import os
from sqlalchemy import create_engine, text

# Add project root to path
sys.path.append(os.getcwd())

from app.core.config import settings

def fix_database():
    print(f"Conectando a la base de datos: {settings.DATABASE_URL.split('@')[1]}") # Hide credentials
    engine = create_engine(settings.DATABASE_URL)
    
    # SQL to add the missing column safely
    sql = text("""
    DO $$ 
    BEGIN 
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name='stock_bodegas' AND column_name='stock_comprometido') THEN 
            ALTER TABLE stock_bodegas ADD COLUMN stock_comprometido NUMERIC(15, 2) DEFAULT 0; 
            RAISE NOTICE 'Columna stock_comprometido agregada exitosamente.';
        ELSE 
            RAISE NOTICE 'La columna stock_comprometido ya existe.';
        END IF; 
    END $$;
    """)
    
    with engine.connect() as connection:
        print("Ejecutando script de migración SQL...")
        # Execute the ALTER TABLE command
        connection.execute(sql)
        connection.commit()
        print("¡Corrección aplicada con éxito!")

if __name__ == "__main__":
    try:
        fix_database()
    except Exception as e:
        print(f"Error crítico al corregir la base de datos: {e}")
