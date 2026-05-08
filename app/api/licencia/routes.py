"""
Endpoints de gestión de licencias de Finaxis.
Accesible solo por administradores de la empresa.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.licencia import activar_licencia, obtener_estado_licencia, LicenciaInvalidaError
from app.models.usuario import Usuario

router = APIRouter(prefix="/api/licencia", tags=["Licencia"])

# Roles que pueden gestionar la licencia
_ROLES_ADMIN = {"administrador", "superadmin", "soporte", "contador"}


class ActivarLicenciaRequest(BaseModel):
    empresa_id: int
    llave: str


def _verificar_admin(current_user: Usuario):
    """Valida que el usuario tenga un rol administrativo."""
    nombres_roles = {r.nombre.lower() for r in current_user.roles}
    if not nombres_roles.intersection(_ROLES_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador de la empresa puede gestionar la licencia."
        )


@router.post("/activar")
def activar(
    body: ActivarLicenciaRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Activa una llave de licencia para la empresa indicada.
    Solo accesible por Administrador, Superadmin o Soporte.
    """
    _verificar_admin(current_user)

    # El usuario solo puede activar su propia empresa (a menos que sea soporte)
    nombres_roles = {r.nombre.lower() for r in current_user.roles}
    if "soporte" not in nombres_roles and current_user.empresa_id != body.empresa_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para activar la licencia de otra empresa."
        )

    try:
        resultado = activar_licencia(
            db=db,
            empresa_id=body.empresa_id,
            llave=body.llave.strip()
        )
        return resultado
    except LicenciaInvalidaError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/estado/{empresa_id}")
def estado_licencia(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Retorna el estado actual de la licencia de la empresa.
    Muestra si está en modo DEMO o FULL.
    """
    # Solo puede consultar su propia empresa (o soporte puede ver cualquiera)
    nombres_roles = {r.nombre.lower() for r in current_user.roles}
    if "soporte" not in nombres_roles and current_user.empresa_id != empresa_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para consultar la licencia de otra empresa."
        )

    return obtener_estado_licencia(db=db, empresa_id=empresa_id)
