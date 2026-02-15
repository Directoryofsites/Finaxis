import sys
import os
# Add parent dir to path to find app module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate():
    print(f"Connecting to: {settings.DATABASE_URL}")
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            print("Executing ALTER TABLE...")
            # PostgreSQL syntax
            connection.execute(text("ALTER TABLE usuarios_busquedas_guardadas ALTER COLUMN titulo TYPE VARCHAR(255);"))
            connection.commit()
            print("Migration successful: titulo column increased to 255 chars.")
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate()
