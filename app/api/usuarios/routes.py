from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import usuario as services_usuario
from app.schemas import usuario as schemas_usuario
from app.core.security import get_current_user, has_permission
from app.models import usuario as models_usuario

router = APIRouter()

# --- UTILS ---
def get_current_active_soporte_user(
    current_user: models_usuario.Usuario = Depends(get_current_user)
) -> models_usuario.Usuario:
    if current_user.empresa_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para realizar esta operación de soporte."
        )
    return current_user

# --- ENDPOINTS GLOBALES (AUTOSERVICIO) ---

@router.get("/me", response_model=schemas_usuario.User)
def read_users_me(current_user: models_usuario.Usuario = Depends(get_current_user)):
    """
    Retorna el perfil del usuario actual, incluyendo ROLES y PERMISOS.
    Esencial para que el frontend pueda renderizar los menús correctamente.
    """
    return current_user

@router.get("/", response_model=List[schemas_usuario.User])
def read_company_users(
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("empresa:usuarios_roles"))
):
    """
    Lista usuarios.
    - Si es Soporte: Lista TODOS (o debería filtrar? Usaremos /soporte para soporte).
      Aquí listaremos los de la empresa actual si el usuario tiene empresa.
    """
    if current_user.empresa_id:
        # Usuario de empresa: listar solo los de SU empresa
        return services_usuario.get_users_by_company(db, current_user.empresa_id)
    else:
        # Usuario de soporte: prohibido listar TODO el sistema por aquí por performance/seguridad
        # Usar endpoints específicos de soporte o retornar lista vacía
        return []

@router.post("/", response_model=schemas_usuario.User, status_code=status.HTTP_201_CREATED)
def create_company_user(
    user_data: schemas_usuario.UserCreateInCompany,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("empresa:usuarios_roles"))
):
    """
    Crea un usuario en la MISMMA empresa que el usuario actual.
    Autoservicio.
    """
    if not current_user.empresa_id:
        raise HTTPException(status_code=400, detail="Soporte debe usar el panel de empresas.")
    
    return services_usuario.create_user_in_company(db, user_data, current_user.empresa_id)

@router.put("/{usuario_id}", response_model=schemas_usuario.User)
def update_user_details(
    usuario_id: int,
    user_update: schemas_usuario.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("empresa:usuarios_roles"))
):
    """
    Actualiza usuario.
    Permitido si:
    1. Soy Soporte.
    2. Soy Admin de empresa Y el usuario destino es de MI empresa.
    """
    user_to_update = services_usuario.get_user_by_id(db, usuario_id=usuario_id)
    if not user_to_update:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    
    is_soporte = current_user.empresa_id is None
    is_same_company = user_to_update.empresa_id == current_user.empresa_id
    
    if not is_soporte and not is_same_company:
         raise HTTPException(status_code=403, detail="No tiene permiso para editar este usuario.")

    return services_usuario.update_user(db=db, user=user_to_update, user_update=user_update)

@router.delete("/{usuario_id}", response_model=schemas_usuario.UserDeleteResponse)
def delete_single_user(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("empresa:usuarios_roles"))
):
    """
    Elimina usuario.
    Mismas reglas: Soporte o Misma Empresa.
    """
    user_to_delete = services_usuario.get_user_by_id(db, usuario_id=usuario_id)
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
        
    is_soporte = current_user.empresa_id is None
    is_same_company = user_to_delete.empresa_id == current_user.empresa_id
    
    if not is_soporte and not is_same_company:
         raise HTTPException(status_code=403, detail="No tiene permiso para eliminar este usuario.")

    return services_usuario.delete_usuario(db=db, usuario_id=usuario_id)

# --- ENDPOINTS DE SOPORTE (LEGACY/SPECIFIC) ---

@router.get("/soporte", response_model=List[schemas_usuario.User])
def read_soporte_users(
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_active_soporte_user)
):
    return services_usuario.get_soporte_users(db)

@router.post("/soporte", response_model=schemas_usuario.User, status_code=status.HTTP_201_CREATED)
def create_new_soporte_user(
    user_data: schemas_usuario.SoporteUserCreate,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_active_soporte_user)
):
    return services_usuario.create_soporte_user(db, user_data)

@router.put("/soporte/{usuario_id}/password", status_code=status.HTTP_200_OK)
def change_soporte_user_password(
    usuario_id: int,
    password_update: schemas_usuario.UserPasswordUpdate,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_active_soporte_user)
):
    user_to_update = services_usuario.get_user_by_id(db, usuario_id=usuario_id)
    if not user_to_update or user_to_update.empresa_id is not None:
        raise HTTPException(status_code=404, detail="Usuario de soporte no encontrado")

    services_usuario.update_password(db, user_to_update, password_update.nuevaPassword)
    return {"message": "Contraseña actualizada."}