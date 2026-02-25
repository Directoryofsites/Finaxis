from sqlalchemy import text
from app.core.database import engine

def upgrade():
    with engine.begin() as conn:
        try:
            # Check if column exists
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='usuarios' AND column_name='whatsapp_number';"))
            if not result.fetchone():
                conn.execute(text("ALTER TABLE usuarios ADD COLUMN whatsapp_number VARCHAR(50) UNIQUE;"))
                print("Columna 'whatsapp_number' agregada exitosamente a 'usuarios'.")
                
                # Create an index for faster lookups
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_usuarios_whatsapp_number ON usuarios (whatsapp_number);"))
                print("Índice 'ix_usuarios_whatsapp_number' creado exitosamente.")
            else:
                print("La columna 'whatsapp_number' ya existe.")
        except Exception as e:
            print(f"Error al agregar la columna: {e}")

if __name__ == "__main__":
    upgrade()
