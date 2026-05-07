import datetime
import sys
from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.models.permiso import Rol, Permiso
from app.services.usuario import get_password_hash

def configurar_nueva_instalacion():
    print("========================================")
    print("   ASISTENTE DE INSTALACIÓN FINAXIS     ")
    print("========================================")

    # 1. Recolectar datos
    nombre_empresa = input("Nombre de la Empresa: ")
    nit = input("NIT (ej. 900.123.456-1): ")
    fecha_inicio = input("Fecha Inicio Operaciones (AAAA-MM-DD): ") or "2026-01-01"
    email_admin = input("Correo del Administrador: ")
    pass_admin = input("Contraseña del Administrador: ")

    db = SessionLocal()
    try:
        # 2. Crear la Empresa
        nueva_empresa = Empresa(
            razon_social=nombre_empresa,
            nit=nit,
            fecha_inicio_operaciones=datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d").date(),
            limite_registros_mensual=200 # Inicia en modo DEMO
        )
        db.add(nueva_empresa)
        db.flush() 

        # 3. Buscar el Rol Administrador
        rol_admin = db.query(Rol).filter(Rol.nombre == "Administrador").first()
        if not rol_admin:
            print("❌ Error: El Rol 'Administrador' no existe en la BD. Ejecute el seeder primero.")
            return

        # 4. Crear el Usuario
        nuevo_usuario = Usuario(
            email=email_admin,
            nombre_completo="Administrador del Sistema",
            hashed_password=get_password_hash(pass_admin),
            empresa_id=nueva_empresa.id,
            is_active=True
        )
        nuevo_usuario.roles.append(rol_admin)
        db.add(nuevo_usuario)

        db.commit()
        print("\n✅ INSTALACIÓN COMPLETADA CON ÉXITO")
        print(f"----------------------------------------")
        print(f"Empresa: {nombre_empresa} (ID: {nueva_empresa.id})")
        print(f"Admin:   {email_admin}")
        print(f"----------------------------------------")
        print("Recuerde que la empresa no tiene Plan de Cuentas (PUC) aún.")

    except Exception as e:
        db.rollback()
        print(f"\n❌ ERROR: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    configurar_nueva_instalacion()
