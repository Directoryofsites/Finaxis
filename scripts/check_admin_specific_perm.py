import sys
import os
sys.path.append("c:/ContaPY2")
from app.core.database import SessionLocal
from app.models import permiso as models_permiso

def check_admin_permissions():
    db = SessionLocal()
    try:
        admin_role = db.query(models_permiso.Rol).filter(models_permiso.Rol.nombre == "administrador").first()
        if not admin_role:
            print("Rol administrador no encontrado.")
            return

        print(f"Permisos del rol 'administrador' (ID: {admin_role.id}):")
        perms = [p.nombre for p in admin_role.permisos]
        for p in sorted(perms):
            print(f" - {p}")
            
        if "utilidades:scripts" in perms:
            print("\n[ALERTA] El permiso 'utilidades:scripts' ESTÁ presente en el rol administrador.")
        else:
            print("\n[OK] El permiso 'utilidades:scripts' NO está presente en el rol administrador.")

    finally:
        db.close()

if __name__ == "__main__":
    check_admin_permissions()
