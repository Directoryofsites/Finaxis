from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    print("Eliminando tabla ph_conceptos defectuosa...")
    conn.execute(text("DROP TABLE IF EXISTS ph_conceptos CASCADE"))
    conn.commit()
    print("Tabla eliminada.")
