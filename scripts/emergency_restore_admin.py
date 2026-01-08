import sys
import os

# Añadir el directorio raíz al path para importar módulos de la app
sys.path.append("c:/ContaPY2")

from app.core.database import SessionLocal
from app.core import seeder

def emergency_restore():
    print("INICIANDO RESTAURACIÓN DE EMERGENCIA DE PERMISOS DE ADMINISTRADOR...")
    try:
        # Ejecutamos el seeder. 
        # El seeder es idempotente en creación, pero actualiza relaciones.
        # Al correrlo, actualizará la relación rol_admin -> permisos 
        # con la nueva lista definida en seeder.py
        seeder.seed_database()
        print("RESTAURACIÓN COMPLETADA EXITOSAMENTE.")
    except Exception as e:
        print(f"ERROR CRÍTICO: {e}")

if __name__ == "__main__":
    emergency_restore()
