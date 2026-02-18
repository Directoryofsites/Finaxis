# scripts/list_permissions.py
import sys
import os
from sqlalchemy import text

sys.path.append(os.getcwd())
try:
    from app.core.database import engine
except:
    print("Error importing engine")
    sys.exit(1)

def list_permissions():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT nombre, descripcion FROM permisos ORDER BY nombre;"))
        print(f"{'NOMBRE':<40} | DESCRIPCION")
        print("-" * 80)
        for row in result:
            print(f"{row.nombre:<40} | {row.descripcion}")

if __name__ == "__main__":
    list_permissions()
