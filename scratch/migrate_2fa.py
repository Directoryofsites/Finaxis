from app.core.database import engine
from sqlalchemy import text

def migrate():
    print("Iniciando migracion de 2FA...")
    with engine.connect() as conn:
        try:
            # Añadir totp_secret
            conn.execute(text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS totp_secret TEXT;"))
            # Añadir totp_enabled
            conn.execute(text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS totp_enabled BOOLEAN DEFAULT FALSE;"))
            conn.commit()
            print("EXITO: Columnas totp_secret y totp_enabled añadidas.")
        except Exception as e:
            print(f"ERROR durante la migracion: {e}")

if __name__ == "__main__":
    migrate()
