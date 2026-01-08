
import sys
import os

# Add parent dir to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.permiso import Rol, Permiso
from app.models.usuario import Usuario

def diagnose():
    db: Session = SessionLocal()
    try:
        print("--- DIAGNOSTICO DE USUARIOS Y ROLES ---")
        
        roles = db.query(Rol).all()
        print(f"Roles encontrados: {len(roles)}")
        for r in roles:
            print(f"ID: {r.id} | Nombre: {r.nombre} | Permisos: {len(r.permisos)}")
            # Listar permisos clave
            perms = [p.nombre for p in r.permisos]
            if "empresa:gestionar" in perms: print("  -> TIENE empresa:gestionar")
            else: print("  -> NO TIENE empresa:gestionar")
        
        print("-" * 30)
        
        users = db.query(Usuario).all()
        print(f"Usuarios encontrados: {len(users)}")
        for u in users:
            role_names = [r.nombre for r in u.roles]
            print(f"User: {u.email} | EmpresaID: {u.empresa_id} | Roles: {role_names}")

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    diagnose()
