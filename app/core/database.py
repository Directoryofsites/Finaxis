# app/core/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ..core.config import settings

# --- INICIO DE LA CORRECCIÓN ---
# Se cambia el parámetro echo=True por echo=False para desactivar
# el registro detallado de consultas SQL en la terminal.
# Esto resultará en un arranque del servidor mucho más limpio.
engine = create_engine(
    settings.DATABASE_URL, 
    echo=False  # <-- "Interruptor" de diagnóstico APAGADO
)
# --- FIN DE LA CORRECCIÓN ---

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()