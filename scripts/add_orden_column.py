from sqlalchemy import text
from app.core.database import SessionLocal

db = SessionLocal()
try:
    result = db.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='ph_conceptos' AND column_name='orden'"
    )).fetchone()

    if result:
        print("OK: La columna 'orden' YA EXISTE en ph_conceptos.")
    else:
        print("ADVERTENCIA: La columna 'orden' NO existe. Creándola...")
        db.execute(text("ALTER TABLE ph_conceptos ADD COLUMN orden INTEGER DEFAULT 100"))
        db.commit()
        print("OK: Columna 'orden' creada exitosamente con valor por defecto 100.")
except Exception as e:
    print(f"ERROR: {e}")
finally:
    db.close()
