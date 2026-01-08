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

        perms = sorted([p.nombre for p in admin_role.permisos])
        print(f"Permisos actuales de Administrador ({len(perms)}):")
        for p in perms:
            print(f" - {p}")
            
        required = ["contabilidad:crear_documento", "contabilidad:explorador", "inventario:ver_super_informe"]
        missing = [req for req in required if req not in perms]
        
        if missing:
            print(f"\n[PELIGRO] FALTAN PERMISOS CRÍTICOS: {missing}")
        else:
            print("\n[OK] Todos los permisos críticos parecen estar presentes.")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_admin_permissions()
