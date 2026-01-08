
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.permiso import Rol, Permiso
from app.models.usuario import Usuario

def audit():
    db: Session = SessionLocal()
    try:
        print("--- AUDITORÍA DE PERMISOS ---")
        
        # 1. Check Administrator Role
        admin_role = db.query(Rol).filter(Rol.nombre == "administrador").first()
        if admin_role:
            print(f"ROL: administrador (ID: {admin_role.id})")
            perms = sorted([p.nombre for p in admin_role.permisos])
            print("  PERMISOS:")
            for p in perms:
                mark = ""
                if p == "utilidades:scripts": mark = " <--- CULPRIT (Debe ser eliminado)"
                if p == "utilidades:usar_herramientas": mark = " <--- OJO (Verificar uso)"
                if p == "utilidades:migracion": mark = " <--- OK (Necesario)"
                print(f"    - {p}{mark}")
        else:
            print("ROL administrador NO ENCONTRADO")

        # 2. Check Soporte Role
        soporte_role = db.query(Rol).filter(Rol.nombre == "soporte").first()
        if soporte_role:
            print(f"\nROL: soporte (ID: {soporte_role.id})")
            perms = sorted([p.nombre for p in soporte_role.permisos])
            print(f"  Total Permisos: {len(perms)}")
            if "utilidades:scripts" in perms: print("  -> TIENE utilidades:scripts (Correcto)")

        # 3. Check Users
        print("\n--- USUARIOS ---")
        users = db.query(Usuario).all()
        for u in users:
            roles = [r.nombre for r in u.roles]
            print(f"User: {u.email} | Roles: {roles}")

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    audit()
