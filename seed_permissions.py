import os
import sys
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models import permiso as models_permiso
from app.models import usuario as models_usuario

# Añadimos la ruta del proyecto al sys.path para poder importar los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- LISTA MAESTRA DE PERMISOS ---
# Aquí definimos cada "interruptor" de nuestra aplicación.
# Esta lista crecerá a medida que añadas más funcionalidades.
PERMISOS_DATA = [
    # Módulo de Administración
    {"nombre": "admin:ver_panel", "descripcion": "Acceder a las páginas de administración general."},
    {"nombre": "admin:gestionar_usuarios", "descripcion": "Crear, editar y eliminar usuarios de su empresa."},
    {"nombre": "admin:gestionar_roles", "descripcion": "Crear, editar roles y asignarles permisos."},
    {"nombre": "admin:gestionar_puc", "descripcion": "Gestionar el Plan Único de Cuentas."},
    {"nombre": "admin:gestionar_terceros", "descripcion": "Crear, editar y fusionar terceros."},
    
    # Módulo de Contabilidad
    {"nombre": "contabilidad:crear_documento", "descripcion": "Crear nuevos documentos contables."},
    {"nombre": "contabilidad:editar_documento", "descripcion": "Editar documentos contables existentes."},
    {"nombre": "contabilidad:anular_documento", "descripcion": "Anular documentos contables."},
    {"nombre": "contabilidad:ver_reportes", "descripcion": "Ver todos los reportes contables (Balances, Auxiliares, etc.)."},
    
    # Herramientas Críticas del Sistema
    {"nombre": "sistema:cerrar_periodo", "descripcion": "Cerrar un período contable."},
    {"nombre": "sistema:reabrir_periodo", "descripcion": "Reabrir el último período contable cerrado."},
    {"nombre": "sistema:generar_libros_oficiales", "descripcion": "Generar los Libros Oficiales en PDF."},
    
    # Panel de Soporte (para el super-admin)
    {"nombre": "soporte:acceder_panel", "descripcion": "Acceder al panel de herramientas de soporte."},
]

# --- DEFINICIÓN DE ROLES INICIALES ---
ROLES_DATA = {
    "Administrador": {
        "descripcion": "Acceso total a todos los módulos y funcionalidades.",
        "permisos": "TODOS" # Palabra clave para asignar todos los permisos
    },
    "Consulta": {
        "descripcion": "Acceso de solo lectura a reportes.",
        "permisos": [
            "contabilidad:ver_reportes",
        ]
    },
    "Operador Contable": {
        "descripcion": "Puede crear y editar documentos, pero no anular ni gestionar módulos.",
        "permisos": [
            "contabilidad:crear_documento",
            "contabilidad:editar_documento",
            "contabilidad:ver_reportes",
        ]
    }
}

def seed_data(db: Session):
    print("Iniciando el sembrado de permisos y roles...")

    # 1. Sembrar Permisos
    permisos_en_db = {}
    for permiso_data in PERMISOS_DATA:
        permiso = db.query(models_permiso.Permiso).filter_by(nombre=permiso_data["nombre"]).first()
        if not permiso:
            permiso = models_permiso.Permiso(**permiso_data)
            db.add(permiso)
            print(f"  - Creando permiso: {permiso.nombre}")
        permisos_en_db[permiso.nombre] = permiso
    
    db.commit() # Commit para que los permisos tengan ID antes de asignarlos a roles

    # 2. Sembrar Roles y asignar permisos
    for nombre_rol, rol_data in ROLES_DATA.items():
        rol = db.query(models_permiso.Rol).filter_by(nombre=nombre_rol).first()
        if not rol:
            rol = models_permiso.Rol(nombre=nombre_rol, descripcion=rol_data["descripcion"])
            db.add(rol)
            print(f"  - Creando rol: {rol.nombre}")

        # Asignar permisos
        rol.permisos.clear() # Limpiamos por si el script se corre de nuevo
        
        if rol_data["permisos"] == "TODOS":
            rol.permisos.extend(permisos_en_db.values())
        else:
            for nombre_permiso in rol_data["permisos"]:
                if nombre_permiso in permisos_en_db:
                    rol.permisos.append(permisos_en_db[nombre_permiso])
    
    db.commit()
    print("¡Sembrado completado con éxito!")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()