import sys
from sqlalchemy import text
from app.core.database import SessionLocal

db = SessionLocal()
try:
    print("Conectado a PostgreSQL...")
    db.execute(text("ALTER TABLE indicadores_economicos ADD COLUMN IF NOT EXISTS tasa_usura FLOAT DEFAULT 0;"))
    db.execute(text("ALTER TABLE indicadores_economicos ADD COLUMN IF NOT EXISTS fecha_sincronizacion DATE;"))
    db.commit()
    print("Columnas tasa_usura y fecha_sincronizacion añadidas a PostgreSQL exitosamente.")
except Exception as e:
    print("Error conectando a Postgres:", e)
    db.rollback()
finally:
    db.close()
