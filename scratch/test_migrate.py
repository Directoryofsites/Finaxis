import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from app.core.auto_migrate import run_auto_migrations

if __name__ == "__main__":
    run_auto_migrations()
    print("Auto-migraciones ejecutadas sin errores.")
