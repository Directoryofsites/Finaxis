
import sys
import os

# Add parent dir to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.permiso import Rol, Permiso
from app.models.usuario import Usuario

def cleanup_roles():
    db: Session = SessionLocal()
    try:
        print("--- Iniciando Limpieza de Roles ---")

        # 1. Identificar Roles
        rol_admin_lower = db.query(Rol).filter(Rol.nombre == "administrador").first()
        rol_admin_upper = db.query(Rol).filter(Rol.nombre == "Administrador").first()
        rol_soporte = db.query(Rol).filter(Rol.nombre == "soporte").first()

        if not rol_admin_lower:
            print("ERROR: Rol 'administrador' (minúscula) no encontrado. Creándolo...")
            rol_admin_lower = Rol(nombre="administrador", descripcion="Rol para administrador")
            db.add(rol_admin_lower)
            db.flush()

        # 2. Migrar Usuarios de 'Administrador' a 'administrador'
        if rol_admin_upper:
            migrated_count = 0
            # Buscar usuarios con el rol duplicado (M2M relation users)
            # SQLAlchemy M2M is managed via rol.usuarios
            for user in rol_admin_upper.usuarios:
                print(f"Migrando usuario {user.email} de 'Administrador' a 'administrador'...")
                if rol_admin_lower not in user.roles:
                    user.roles.append(rol_admin_lower)
                user.roles.remove(rol_admin_upper)
                migrated_count += 1
            
            db.flush()
            print(f"Usuarios migrados: {migrated_count}")

            # 3. Eliminar Rol Duplicado
            print("Eliminando rol 'Administrador'...")
            db.delete(rol_admin_upper)
            db.flush()
        else:
            print("Rol 'Administrador' (duplicado) no encontrado. Saltando eliminación.")

        # 4. Definir Permisos Estrictos
        # Lista exacta de permisos deseados para Soporte (Full + Herramientas)
        perms_soporte = [
            "soporte:acceder_panel",
            "empresa:gestionar",
            "utilidades:usar_herramientas",
            "utilidades:scripts",             # Frontend Scripts/Util
            "utilidades:conteo_registros",    # Frontend Conteo
            "utilidades:migracion",
            "utilidades:auditoria_consecutivos",
            "inventario:ver_super_informe",
            # Heredar otros si es necesario, pero estos son los criticos seguridad
        ]

        # Lista exacta de permisos prohibidos para Administrador
        prohibidos_admin = [
            "utilidades:usar_herramientas",
            "utilidades:scripts",
            "utilidades:conteo_registros",
            "soporte:acceder_panel",
            "empresa:gestionar" # Admin no debe gestionar otras empresas
        ]

        # Asegurar existencia de permisos
        all_perms_needed = set(perms_soporte)
        for pname in all_perms_needed:
            p = db.query(Permiso).filter_by(nombre=pname).first()
            if not p:
                print(f"Creando permiso faltante: {pname}")
                db.add(Permiso(nombre=pname, descripcion=pname))
        db.flush()

        # 5. Aplicar Permisos a Soporte
        print("Actualizando permisos de 'soporte'...")
        # (Añadimos sin borrar los existentes para no romper nada más, pero aseguramos los críticos)
        current_perms_soporte = {p.nombre for p in rol_soporte.permisos}
        for pname in perms_soporte:
            if pname not in current_perms_soporte:
                p_obj = db.query(Permiso).filter_by(nombre=pname).first()
                rol_soporte.permisos.append(p_obj)
        
        # 6. Limpiar Permisos de Administrador
        print("Purgando permisos prohibidos de 'administrador'...")
        # Iterar sobre una copia de la lista para poder modificarla
        perms_to_remove = []
        for p in rol_admin_lower.permisos:
            if p.nombre in prohibidos_admin:
                print(f" - Removiendo '{p.nombre}' de administrador")
                perms_to_remove.append(p)
        
        for p in perms_to_remove:
            rol_admin_lower.permisos.remove(p)

        db.commit()
        print("--- Limpieza Completada Exitosamente ---")

    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_roles()
