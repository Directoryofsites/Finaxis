import sys
import os
from sqlalchemy.orm import Session

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.permiso import Rol, Permiso

def update_express_role_permissions():
    """
    Agrega permisos faltantes al rol 'Facturador Express' para ver historial y reportes.
    """
    db = SessionLocal()
    try:
        print("Buscando rol 'Facturador Express'...")
        rol_express = db.query(Rol).filter(Rol.nombre == "Facturador Express").first()
        
        if not rol_express:
            print("ERROR: Rol 'Facturador Express' no encontrado. Asegúrate de haber corrido la inicialización.")
            return

        permisos_necesarios = [
            "contabilidad:explorador",          # Para ver historial (/api/documentos)
            "ventas:ver_reporte_gestion",       # Para reportes de ventas
            "reportes:ver_facturacion_detallado",
            "reportes:ver_officiales",
            "contabilidad:anular_documento"     # Opcional, si queremos que anulen
        ]

        print(f"Verificando {len(permisos_necesarios)} permisos adicionales...")
        
        permisos_agregados = 0
        for nombre_permiso in permisos_necesarios:
            # 1. Asegurar que el permiso exista en BD
            permiso_db = db.query(Permiso).filter(Permiso.nombre == nombre_permiso).first()
            if not permiso_db:
                print(f"  -> Creando permiso faltante en DB: {nombre_permiso}")
                permiso_db = Permiso(nombre=nombre_permiso, descripcion=f"Permiso auto-creado para {nombre_permiso}")
                db.add(permiso_db)
                db.flush()

            # 2. Asignar al rol si no lo tiene
            if permiso_db not in rol_express.permisos:
                rol_express.permisos.append(permiso_db)
                print(f"  -> Asignado '{nombre_permiso}' al rol.")
                permisos_agregados += 1
            else:
                print(f"  -> El rol ya tiene '{nombre_permiso}'.")

        if permisos_agregados > 0:
            db.commit()
            print(f"¡ÉXITO! Se agregaron {permisos_agregados} permisos nuevos.")
        else:
            print("El rol ya tenía todos los permisos necesarios.")

    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_express_role_permissions()
