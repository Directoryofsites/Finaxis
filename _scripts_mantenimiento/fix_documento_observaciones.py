from app.core.database import engine
from sqlalchemy import text

def run_fix():
    print("Connecting to DB...")
    with engine.connect() as connection:
        print("Executing ALTER TABLE for documentos...")
        # Agregar columna observaciones si no existe
        try:
            connection.execute(text("ALTER TABLE documentos ADD COLUMN IF NOT EXISTS observaciones TEXT;"))
            connection.commit()
            print("Columna 'observaciones' agregada correctamente.")
        except Exception as e:
            print(f"Error executing ALTER TABLE: {e}")
            
    print("Done!")

if __name__ == "__main__":
    run_fix()
