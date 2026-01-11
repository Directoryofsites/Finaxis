
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.core.config import settings
from app.models import permiso as models_permiso

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_restricted_clone_role():
    db = SessionLocal()
    try:
        print("Iniciando creación/actualización de rol 'clon_restringido'...")

        permisos_clon = [
             "contabilidad:explorador",
             "contabilidad:configuracion_tipos_doc",
             "contabilidad:gestionar_puc",
             "inventario:ver_super_informe",
             "inventario:ver_reportes",
             "reportes:rentabilidad_producto",
             "ventas:ver_reporte_gestion",
             "reportes:ver_facturacion_detallado",
             "reportes:ver_officiales",
             "cartera:ver_informes",
             "conciliacion_bancaria:ver",
             "conciliacion_bancaria:reportes",
             "conciliacion_bancaria:auditoria",
             
             # --- PERMISOS DE ACCESO A MÓDULOS (Para ver el menú) ---
             "contabilidad:acceso",
             "facturacion:acceso", 
             "inventario:acceso",
             "terceros:acceso",
             "impuestos:acceso",
             "activos:acceso",
             "analisis_financiero:acceso",
             "administracion:acceso", # Si existe para el menú admin
             # -------------------------------------------------------
             
             # NO INCLUIR:
             # - contabilidad:crear_documento
             # - contabilidad:captura_rapida
             # - facturacion:nueva
             # - compras:acceso (Bloquea entrar a Compras)
             # - soporte:acceder_panel
             # - utilidades:scripts
        ]

        # 1. Asegurar Permisos
        print("--> Verificando permisos...")
        permisos_db_list = []
        for nombre_permiso in permisos_clon:
            permiso = db.query(models_permiso.Permiso).filter_by(nombre=nombre_permiso).first()
            if not permiso:
                print(f"    Creando permiso faltante: {nombre_permiso}")
                permiso = models_permiso.Permiso(nombre=nombre_permiso, descripcion=f"Permiso para {nombre_permiso}")
                db.add(permiso)
                db.flush()
            permisos_db_list.append(permiso)

        # 2. Asegurar Rol
        print("--> Verificando rol 'clon_restringido'...")
        rol = db.query(models_permiso.Rol).filter_by(nombre="clon_restringido").first()
        if not rol:
            print("    Creando rol 'clon_restringido'...")
            rol = models_permiso.Rol(nombre="clon_restringido", descripcion="Rol para empresas en modo Auditoría/Solo Lectura")
            db.add(rol)
            db.flush()

        # 3. Asignar Permisos
        print("--> Asignando permisos al rol...")
        rol.permisos = permisos_db_list
        
        db.commit()
        print("¡Rol 'clon_restringido' configurado exitosamente!")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_restricted_clone_role()
