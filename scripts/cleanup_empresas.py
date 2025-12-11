
import sys
import os

# Add the project root to the python path so we can import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app.core.database import SessionLocal, engine

def cleanup_empresas():
    print("--- INICIANDO LIMPIEZA DE EMPRESAS ---")
    print("ADVERTENCIA: Esto eliminará TODAS las empresas y sus datos asociados.")
    
    try:
        db = SessionLocal()
        print("Conexión establecida.")
        
        # SQL Command
        query = text("TRUNCATE TABLE empresas CASCADE;")
        
        print(f"Ejecutando: {query}")
        db.execute(query)
        db.commit()
        
        print("[OK] LIMPIEZA COMPLETADA EXITOSAMENTE.")
        print("La tabla 'empresas' está vacía.")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        # Try to rollback just in case transaction is open
        try:
             db.rollback()
        except:
             pass
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_empresas()
