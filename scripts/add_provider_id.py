import sys
import os
sys.path.append(os.getcwd())

from sqlalchemy import create_engine, text
from app.core.config import settings

def add_provider_id_column():
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE documentos ADD COLUMN provider_id VARCHAR(255)"))
            print("Columna provider_id agregada exitosamente.")
            conn.commit()
        except Exception as e:
            print(f"Error (puede que ya exista): {e}")

if __name__ == "__main__":
    add_provider_id_column()
