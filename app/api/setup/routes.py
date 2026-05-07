from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.models.permiso import Rol
from app.services.usuario import get_password_hash
from pydantic import BaseModel
from datetime import date

router = APIRouter(prefix="/setup", tags=["setup"])

class InitialSetupSchema(BaseModel):
    razon_social: str
    nit: str
    fecha_inicio: date
    admin_email: str
    admin_password: str

@router.get("/check")
def check_setup_needed():
    """Verifica si el sistema necesita configuración inicial (si hay 0 empresas)."""
    db = SessionLocal()
    try:
        count = db.query(Empresa).count()
        return {"setup_needed": count == 0}
    finally:
        db.close()

@router.post("/initialize")
def initialize_system(data: InitialSetupSchema):
    """Crea la primera empresa y el administrador global."""
    db = SessionLocal()
    try:
        # 1. Doble verificación: ¿Realmente no hay empresas?
        if db.query(Empresa).count() > 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El sistema ya ha sido inicializado anteriormente."
            )

        # 2. Buscar el Rol Administrador (Debe existir por el seeder base)
        rol_admin = db.query(Rol).filter(Rol.nombre == "Administrador").first()
        if not rol_admin:
            # Si por algo no existe, lo creamos de emergencia
            rol_admin = Rol(nombre="Administrador", descripcion="Administrador Global")
            db.add(rol_admin)
            db.flush()

        # 3. Crear la Empresa
        nueva_empresa = Empresa(
            razon_social=data.razon_social,
            nit=data.nit,
            fecha_inicio_operaciones=data.fecha_inicio,
            limite_registros_mensual=200 # Inicia como Demo
        )
        db.add(nueva_empresa)
        db.flush()

        # 4. Crear el Usuario Administrador
        nuevo_usuario = Usuario(
            email=data.admin_email,
            nombre_completo="Administrador Principal",
            password_hash=get_password_hash(data.admin_password),
            empresa_id=nueva_empresa.id
        )
        nuevo_usuario.roles.append(rol_admin)
        db.add(nuevo_usuario)

        db.commit()
        return {"status": "success", "message": "Sistema inicializado correctamente. Ya puede iniciar sesión."}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en la inicialización: {str(e)}")
    finally:
        db.close()
