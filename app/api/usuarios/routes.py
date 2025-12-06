from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import usuario as services_usuario
from app.schemas import usuario as schemas_usuario
from app.core.security import get_current_user
from app.models import usuario as models_usuario

router = APIRouter()

# --- INICIO: GUARDIA DE SEGURIDAD CORREGIDO ---
def get_current_active_soporte_user(
    current_user: models_usuario.Usuario = Depends(get_current_user)
) -> models_usuario.Usuario:
    """
    Guardia de seguridad que verifica si el usuario actual es de soporte.
    La nueva regla es: un usuario de soporte NO tiene empresa_id.
    """
    # CAMBIO CRÍTICO: Reemplazamos la lógica obsoleta.
    if current_user.empresa_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para realizar esta operación de soporte."
        )
    return current_user
# --- FIN: GUARDIA DE SEGURIDAD CORREGIDO ---


@router.get("/soporte", response_model=List[schemas_usuario.User])
def read_soporte_users(
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_active_soporte_user)
):
    """
    Obtiene una lista de todos los usuarios de soporte.
    """
    # CAMBIO CRÍTICO: Actualizamos el servicio para que no dependa de la columna 'rol'.
    return services_usuario.get_soporte_users(db)

@router.post("/soporte", response_model=schemas_usuario.User, status_code=status.HTTP_201_CREATED)
def create_new_soporte_user(
    user_data: schemas_usuario.SoporteUserCreate,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_active_soporte_user)
):
    """
    Crea un nuevo usuario de soporte.
    """
    return services_usuario.create_soporte_user(db, user_data)

@router.put("/soporte/{usuario_id}/password", status_code=status.HTTP_200_OK)
def change_soporte_user_password(
    usuario_id: int,
    password_update: schemas_usuario.UserPasswordUpdate,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_active_soporte_user)
):
    """
    Permite a un usuario de soporte cambiar la contraseña de OTRO usuario de soporte.
    """
    user_to_update = services_usuario.get_user_by_id(db, usuario_id=usuario_id)

    # CAMBIO CRÍTICO: La verificación de seguridad ahora usa la regla de 'empresa_id'.
    if not user_to_update or user_to_update.empresa_id is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró un usuario de soporte con el id {usuario_id}"
        )

    services_usuario.update_password(
        db=db, 
        user=user_to_update, 
        new_password=password_update.nuevaPassword
    )

    return {"message": "Contraseña de usuario de soporte actualizada exitosamente."}


# --- RUTA ANTIGUA OBSOLETA ---
# NOTA: He comentado esta ruta. La nueva lógica de permisos la hace redundante y
# riesgosa. La mantenemos aquí por si necesitas consultarla, pero no debería
# estar activa en producción.
# @router.put("/{usuario_id}/password", status_code=status.HTTP_200_OK, include_in_schema=False)
# def change_user_password(...):
#     ...

@router.delete("/{usuario_id}", response_model=schemas_usuario.UserDeleteResponse)
def delete_single_user(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_active_soporte_user)
):
    """
    Elimina un usuario específico por su ID.
    Solo los usuarios de soporte pueden realizar esta acción.
    El servicio subyacente previene el borrado si el usuario tiene historial.
    """
    return services_usuario.delete_usuario(db=db, usuario_id=usuario_id)