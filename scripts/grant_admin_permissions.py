import sys
import os

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.models.usuario import Usuario
from app.models.permiso import Permiso, Rol

def grant_all_to_admin():
    db = SessionLocal()
    try:
        print("Searching for Admin role...")
        # Search for Admin role (usually id 1 or name 'Admin' or 'Administrador')
        # We'll try common names
        roles = db.query(Rol).filter(Rol.nombre.in_(['Admin', 'Administrador', 'Super Admin', 'Admon'])).all()
        
        if not roles:
            print("No Admin roles found!")
            return

        all_permissions = db.query(Permiso).all()
        print(f"Found {len(all_permissions)} total permissions in system.")

        for rol in roles:
            print(f"Updating role: {rol.nombre} (ID: {rol.id})")
            
            # Get current permission IDs
            current_perm_ids = {p.id for p in rol.permisos}
            
            added_count = 0
            for perm in all_permissions:
                if perm.id not in current_perm_ids:
                    rol.permisos.append(perm)
                    added_count += 1
            
            print(f"  -> Added {added_count} new permissions.")
        
        db.commit()
        print("Successfully updated Admin roles.")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    grant_all_to_admin()
