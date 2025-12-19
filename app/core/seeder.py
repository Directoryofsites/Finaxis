# app/core/seeder.py (Versión con permiso para Super Informe Inventarios)

from datetime import datetime
from sqlalchemy.orm import Session
from .database import SessionLocal
from ..models.empresa import Empresa
from ..models.usuario import Usuario
from ..models import permiso as models_permiso
from ..schemas import usuario as usuario_schema
from ..services import usuario as usuario_service
from ..services.seeder_puc import seed_puc_simplificado # Importar seeder PUC

def seed_database():
    """
    Función principal para sembrar la base de datos con datos iniciales.
    Sigue el Principio de la "Instalación Atómica".
    """
    db = SessionLocal()
    try:
        # Nota: Eliminamos el check de 'Rol' al inicio para permitir que updates progresivos (como nuevos permisos o PUC) corran.
        # En su lugar, cada bloque debe ser idempotente (verificar si existe antes de crear).
        
        print("Iniciando proceso de sembrado/actualización...")

        # ... (Mantener lógica de permisos y roles igual) ...

        
        # --- FASE 1: DEFINIR Y CREAR TODOS LOS DATOS INICIALES ---
        print("--> Definiendo roles y su mapa de permisos inicial...")

        # --- INICIO DE LA MODIFICACIÓN: Añadir permiso Super Informe ---
        permisos_por_rol = {
            "soporte": [
                "soporte:acceder_panel",
                "empresa:gestionar",
                "utilidades:usar_herramientas",
                "inventario:ver_super_informe" # <-- NUEVO PERMISO AÑADIDO
            ],
            "administrador": [
                "utilidades:migracion",
                "inventario:ver_reportes",
                "reportes:rentabilidad_producto",
                "ventas:ver_reporte_gestion",
                "reportes:ver_facturacion_detallado",
                "papelera:usar",
                "plantilla:crear",
                "inventario:eliminar_producto", # Añadido en misión anterior
                "inventario:ver_super_informe", # <-- NUEVO PERMISO AÑADIDO
                # Permisos de Conciliación Bancaria
                "conciliacion_bancaria:ver",
                "conciliacion_bancaria:configurar",
                "conciliacion_bancaria:importar",
                "conciliacion_bancaria:conciliar",
                "conciliacion_bancaria:ajustar",
                "conciliacion_bancaria:reportes",
                "conciliacion_bancaria:auditoria"
            ],
            "operador_bancario": [
                # Rol especializado para conciliación bancaria
                "conciliacion_bancaria:ver",
                "conciliacion_bancaria:configurar",
                "conciliacion_bancaria:importar",
                "conciliacion_bancaria:conciliar",
                "conciliacion_bancaria:ajustar",
                "conciliacion_bancaria:reportes",
                "inventario:ver_reportes"
            ],
            "Administrador": [
                # Rol Administrador con mayúscula (usado por el sistema)
                "utilidades:migracion",
                "inventario:ver_reportes",
                "reportes:rentabilidad_producto",
                "ventas:ver_reporte_gestion",
                "reportes:ver_facturacion_detallado",
                "papelera:usar",
                "plantilla:crear",
                "inventario:eliminar_producto",
                "inventario:ver_super_informe",
                # Permisos de Conciliación Bancaria
                "conciliacion_bancaria:ver",
                "conciliacion_bancaria:configurar",
                "conciliacion_bancaria:importar",
                "conciliacion_bancaria:conciliar",
                "conciliacion_bancaria:ajustar",
                "conciliacion_bancaria:reportes",
                "conciliacion_bancaria:auditoria"
            ]
            # Añadir aquí permisos para 'contador' o 'invitado' si es necesario
        }
        # --- FIN DE LA MODIFICACIÓN ---
        
        todos_los_permisos_nombres = set()
        for _, lista_permisos in permisos_por_rol.items():
            todos_los_permisos_nombres.update(lista_permisos)

        print(f"--> Asegurando la existencia de {len(todos_los_permisos_nombres)} permisos...")
        for nombre_permiso in todos_los_permisos_nombres:
            if not db.query(models_permiso.Permiso).filter(models_permiso.Permiso.nombre == nombre_permiso).first():
                db.add(models_permiso.Permiso(nombre=nombre_permiso, descripcion=f"Permiso para {nombre_permiso}"))
        
        db.flush()

        print("--> Asegurando la existencia de todos los roles...")
        roles_a_crear = ["soporte", "administrador", "Administrador", "contador", "invitado", "operador_bancario"]
        for nombre_rol in roles_a_crear:
            if not db.query(models_permiso.Rol).filter(models_permiso.Rol.nombre == nombre_rol).first():
                db.add(models_permiso.Rol(nombre=nombre_rol, descripcion=f"Rol para {nombre_rol}"))
        
        db.flush()

        # --- FASE 2: ASIGNAR PERMISOS A ROLES ---
        print("--> Asignando permisos a los roles correspondientes...")
        for rol_nombre, lista_permisos in permisos_por_rol.items():
            rol_db = db.query(models_permiso.Rol).filter(models_permiso.Rol.nombre == rol_nombre).one()
            permisos_db = db.query(models_permiso.Permiso).filter(models_permiso.Permiso.nombre.in_(lista_permisos)).all()
            rol_db.permisos = permisos_db
        
        print("--> Permisos asignados exitosamente.")

        # --- FASE 3: CREAR EMPRESAS Y USUARIOS INICIALES ---
        print("--> Creando empresa y usuarios de demostración...")
        
        # Check if exists (Idempotency Fix)
        empresa_demo = db.query(Empresa).filter(Empresa.nit == "800000001-1").first()
        
        if not empresa_demo:
            empresa_demo = Empresa(
                razon_social="Empresa de Demostración", 
                nit="800000001-1", 
                fecha_inicio_operaciones=datetime.fromisoformat("2025-01-01").date(), 
                limite_registros=1500
            )
            db.add(empresa_demo)
            db.flush() # Asegurar que empresa_demo tenga su ID
            print(f"--> Empresa Demo Creada (ID: {empresa_demo.id})")
        else:
            print(f"--> Empresa Demo ya existe (ID: {empresa_demo.id}). Saltando creación.")
        
        # --- NUEVO: SEMBRAR PUC SIMPLIFICADO ---
        seed_puc_simplificado(db, empresa_demo.id)
        # ---------------------------------------

        usuarios_data = [
            {"email": "soporte@soporte.com", "nombre_completo": "Usuario de Soporte Global", "password": "Jh811880", "rol_nombre": "soporte", "empresa_id": None},
            {"email": "admin@empresa.com", "nombre_completo": "Admin de Empresa Demo", "password": "admin123", "rol_nombre": "administrador", "empresa_id": empresa_demo.id}
        ]
        
        for usuario_data in usuarios_data:
            rol_db_usr = db.query(models_permiso.Rol).filter(models_permiso.Rol.nombre == usuario_data['rol_nombre']).first()
            if not rol_db_usr: 
                print(f"WARN: Rol '{usuario_data['rol_nombre']}' no encontrado, saltando usuario {usuario_data['email']}.")
                continue
            
            usuario_a_crear = usuario_schema.UserCreateInCompany(
                email=usuario_data['email'], 
                nombre_completo=usuario_data.get('nombre_completo'), 
                password=usuario_data['password'], 
                roles_ids=[rol_db_usr.id]
            )
            
            if not usuario_service.get_user_by_email(db, email=usuario_a_crear.email):
                usuario_service.create_user_in_company(db=db, user_data=usuario_a_crear, empresa_id=usuario_data['empresa_id'])
            else:
                 print(f"INFO: Usuario {usuario_data['email']} ya existe, saltando creación.")


        # --- FASE 4: CIERRE DE LA TRANSACCIÓN ---
        db.commit()
        print("Proceso de sembrado atómico completado exitosamente. ¡La base de datos está lista!")
    except Exception as e:
        print(f"ERROR DURANTE EL SEMBRADO: {e}")
        db.rollback()
    finally:
        db.close()