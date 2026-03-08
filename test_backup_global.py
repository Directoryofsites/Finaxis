import os
import sys

# Asegurar que el path sea el correcto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services import scheduler_backup
import json

def test_backup():
    print("Iniciando prueba de config global...")
    config = scheduler_backup.load_config("global")
    print("Configuración inicial:", config)
    
    print("\nGuardando nueva configuración...")
    config["hora_ejecucion"] = "14:30"
    scheduler_backup.save_global_config(config)
    
    print("\nConfiguración guardada:", scheduler_backup.load_config("global"))
    
    print("\nEjecutando backup manual global (simulado o real si hay db)...")
    try:
        scheduler_backup.run_global_backup()
        print("Backup global finalizado.")
    except Exception as e:
        print(f"Error durante el backup global: {e}")

if __name__ == "__main__":
    test_backup()
