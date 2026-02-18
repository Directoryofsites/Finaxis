import sys
import os
from sqlalchemy import create_engine, text

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.core.config import settings

def add_column():
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        try:
            # Check if column exists
            check_sql = text("SELECT column_name FROM information_schema.columns WHERE table_name='empresas' AND column_name='saldo_notas_credito'")
            result = conn.execute(check_sql).fetchone()
            
            if not result:
                print("Adding 'saldo_notas_credito' column to 'empresas' table...")
                alter_sql = text("ALTER TABLE empresas ADD COLUMN saldo_notas_credito INTEGER DEFAULT 0 NOT NULL")
                conn.execute(alter_sql)
                conn.commit()
                print("Column added successfully.")
            else:
                print("Column 'saldo_notas_credito' already exists.")
                
        except Exception as e:
            print(f"Error adding column: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    add_column()
