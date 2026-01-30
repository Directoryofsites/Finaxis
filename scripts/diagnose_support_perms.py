
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.permiso import Rol

def check_support_perms():
    db = SessionLocal()
    try:
        soporte_role = db.query(Rol).filter(Rol.nombre == "soporte").first()
        if not soporte_role:
            print("Rol 'soporte' no encontrado.")
            return

        print(f"Permisos de '{soporte_role.nombre}' (ID: {soporte_role.id}):")
        perms = sorted([p.nombre for p in soporte_role.permisos])
        
        found_target = False
        for p in perms:
            marker = " [MISSING??]"
            if p == "empresa:gestionar_empresas":
                marker = " [OK - PRESENT]"
                found_target = True
            print(f" - {p}{marker if p == 'empresa:gestionar_empresas' else ''}")
            
        if not found_target:
            print("\n[CRITICAL] El permiso 'empresa:gestionar_empresas' NO está asignado al rol 'soporte'.")
        else:
            print("\n[OK] El permiso requerido está presente.")

    finally:
        db.close()

if __name__ == "__main__":
    check_support_perms()
