import sys
import os

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.services import usuario as usuario_service
from app.models.usuario import Usuario

def check_permissions():
    db = SessionLocal()
    try:
        user = usuario_service.get_user_by_email(db, "soporte@soporte.com")
        if not user:
            print("User not found!")
            return

        print(f"User: {user.email}")
        print(f"Roles: {[r.nombre for r in user.roles]}")
        
        # Manually query all permissions for this user's roles
        all_perms = set()
        for role in user.roles:
            print(f"Role '{role.nombre}' has {len(role.permisos)} permissions.")
            for p in role.permisos:
                all_perms.add(p.nombre)
        
        print(f"Total Unique Permissions: {len(all_perms)}")
        
        required = ["contabilidad:crear_documento", "contabilidad:acceso"]
        for req in required:
            if req in all_perms:
                print(f"OK: '{req}' FOUND.")
            else:
                print(f"FAIL: '{req}' MISSING.")

    finally:
        db.close()

if __name__ == "__main__":
    check_permissions()
