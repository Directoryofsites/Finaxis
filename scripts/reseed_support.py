
import sys
import os

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.seeder import seed_database
from app.core.database import SessionLocal
from app.models.usuario import Usuario

def force_reseed():
    print("--- FORZANDO RE-SEMBRADO DE SOPORTE ---")
    try:
        # Run standard seeder
        seed_database()
        
        # Verify
        db = SessionLocal()
        soporte = db.query(Usuario).filter(Usuario.email == "soporte@soporte.com").first()
        if soporte:
            print(f"✅ Usuario de Soporte Restaurado: {soporte.email}")
        else:
            print("❌ ERROR: El usuario de soporte no aparece tras el sembrado.")
        db.close()
        
    except Exception as e:
        print(f"❌ ERROR CRÍTICO: {e}")

if __name__ == "__main__":
    force_reseed()
