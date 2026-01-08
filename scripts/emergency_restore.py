
import sys
import os

# Google-style import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.permiso import Rol, Permiso

def emergency_restore():
    db: Session = SessionLocal()
    try:
        print("--- RESTAURACIÓN DE PERMISOS FALTANTES ---")

        # 1. Obtener Rol Administrador
        rol_admin = db.query(Rol).filter(Rol.nombre == "administrador").first()
        if not rol_admin:
            print("CRÍTICO: Rol 'administrador' no encontrado.")
            return

        # 2. Agregar Permisos Específicos que faltan
        # El usuario reportó que "Maestros" (Migracion) y "Super Informe" se quedan cargando.
        # Esto indica que faltan estos permisos específicos.
        
        permisos_restaurar = [
            # Acceso Básico
            "empresa:gestionar",
            
            # Utilidades de Soporte (Solicitado restaurar por 'deshaz cambios')
            "soporte:acceder_panel", 
            "utilidades:scripts",
            "utilidades:usar_herramientas",
            "utilidades:conteo_registros",

            # Reportes y Migración (FALTABAN EN RESTAURACION PREVIA)
            "utilidades:migracion",           # Para Maestros de Migración / Backups
            "inventario:ver_super_informe",   # Para Super Informe
            "inventario:ver_reportes",        # General Inventarios
            "reportes:rentabilidad_producto",
            "ventas:ver_reporte_gestion",
            "conciliacion_bancaria:ver",      # Por si acaso
        ]

        print(f"Verificando {len(permisos_restaurar)} permisos en 'administrador'...")

        for pname in permisos_restaurar:
            # Asegurar que existe el permiso
            permiso = db.query(Permiso).filter_by(nombre=pname).first()
            if not permiso:
                permiso = Permiso(nombre=pname, descripcion=pname)
                db.add(permiso)
                db.flush()
            
            # Asignar si no lo tiene
            if permiso not in rol_admin.permisos:
                rol_admin.permisos.append(permiso)
                print(f" + AGREGADO: {pname}")
            else:
                pass # Ya lo tiene

        db.commit()
        print("--- PERMISOS ACTUALIZADOS. PRUEBE AHORA. ---")

    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    emergency_restore()
