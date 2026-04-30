from app.core.database import engine
from sqlalchemy import text

def migrate():
    print("Actualizando tabla copia_seguridad para verificacion...")
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE copia_seguridad ADD COLUMN IF NOT EXISTS es_valido INTEGER DEFAULT 0;"))
            conn.execute(text("ALTER TABLE copia_seguridad ADD COLUMN IF NOT EXISTS error_verificacion TEXT;"))
            conn.commit()
            print("EXITO: Columnas de verificacion añadidas localmente.")
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    migrate()
