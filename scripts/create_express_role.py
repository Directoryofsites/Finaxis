# scripts/create_express_role.py
import sys
import os

sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.permiso import Rol, Permiso

def create_express_role():
    db = SessionLocal()
    try:
        ROLE_NAME = "Facturador Express"
        print(f"--- CREANDO/ACTUALIZANDO ROL: {ROLE_NAME} ---")
        
        # 1. Buscar o crear Rol
        rol = db.query(Rol).filter(Rol.nombre == ROLE_NAME).first()
        if not rol:
            print("Rol no existe. Creando...")
            rol = Rol(
                nombre=ROLE_NAME,
                descripcion="Rol restringido para usuarios de Modo Express (Solo Facturación y Terceros)"
            )
            db.add(rol)
            db.commit()
            db.refresh(rol)
        else:
            print(f"Rol '{ROLE_NAME}' ya existe (ID: {rol.id}). Actualizando permisos...")

        # 2. Definir Permisos Permitidos
        # Lista blanca estricta
        PERMISOS_ALLOWED = [
            # Facturación
            "facturacion:acceso",
            "facturacion:nueva",
            "facturacion:ventas_cliente",
            "facturacion:cotizaciones", # Opcional, pero util
            "facturacion:remisiones",   # Opcional
            
            # Terceros
            "terceros:acceso",
            "terceros:gestionar",
            "terceros:estado_cuenta_cliente",
            
            # Inventario (Mínimo para ver productos al facturar)
            "inventario:acceso", 
            "inventario:ver_productos", 
            "inventario:crear_producto", # Necesario para crear items al vuelo? Tal vez.
            
            # Dashboard / General
            # "dashboard:contador" # Tal vez no
        ]
        
        # 3. Asignar Permisos
        permisos_db = db.query(Permiso).filter(Permiso.nombre.in_(PERMISOS_ALLOWED)).all()
        
        if not permisos_db:
            print("ADVERTENCIA: No se encontraron los permisos solicitados en la DB. Verifique los nombres.")
        
        # Reemplazar permisos actuales del rol
        rol.permisos = permisos_db
        db.commit()
        
        print(f"Rol '{ROLE_NAME}' configurado con {len(permisos_db)} permisos.")
        print("Permisos asignados:")
        for p in permisos_db:
            print(f" - {p.nombre}")

    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_express_role()
