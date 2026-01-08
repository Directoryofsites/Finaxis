
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.permiso import Rol, Permiso

def refine_permissions():
    db: Session = SessionLocal()
    try:
        print("--- REFINAMIENTO DE PERMISOS (Separación de Funciones) ---")

        rol_admin = db.query(Rol).filter(Rol.nombre == "administrador").first()
        if not rol_admin:
            print("Rol 'administrador' no encontrado.")
            return

        # 1. Permisos a ELIMINAR del Administrador (Exclusivos de Soporte)
        perms_to_remove = [
            "utilidades:scripts",           # Ocultar menú Scripts/Util
            "utilidades:conteo_registros",  # Ocultar menú Conteo Registros
            "soporte:acceder_panel",        # Identificador general de soporte
            "utilidades:usar_herramientas", # Backend: Herramientas peligrosas (Recodificar, Erradicar)
             # Nota: 'utilidades:migracion' SE QUEDA para que pueda hacer backups
        ]

        print(f"Eliminando {len(perms_to_remove)} permisos exclusivos de Soporte del rol 'administrador'...")
        
        # Iterar sobre una copia
        current_perms = list(rol_admin.permisos)
        for p in current_perms:
            if p.nombre in perms_to_remove:
                rol_admin.permisos.remove(p)
                print(f" - REMOVIDO: {p.nombre}")

        # 2. Verificar que se mantienen los críticos de operativa
        critical_perms = [
            "empresa:gestionar", 
            "utilidades:migracion", 
            "inventario:ver_super_informe"
        ]
        
        print("Verificando permisos críticos...")
        current_perm_names = [p.nombre for p in rol_admin.permisos]
        for cp in critical_perms:
            if cp in current_perm_names:
                print(f"OK: Mantiene {cp}")
            else:
                print(f"ALERTA: Falta {cp} (Se debería agregar manual si no está)")
                # Auto-fix safety catch
                p_obj = db.query(Permiso).filter_by(nombre=cp).first()
                if p_obj:
                    rol_admin.permisos.append(p_obj)
                    print(f" + RESTAURADO AUTOMÁTICAMENTE: {cp}")

        db.commit()
        print("--- REFINAMIENTO COMPLETADO ---")

    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    refine_permissions()
