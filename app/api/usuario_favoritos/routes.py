# app/api/usuario_favoritos/routes.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

# Importaciones del Core
from ...core.database import get_db
from ...core.security import get_current_user
from ...models.usuario import Usuario # Necesario para la dependencia de usuario
from ...schemas import usuario_favorito as schemas_favorito
from ...services import favoritos as service_favoritos

router = APIRouter(
    prefix="/favoritos",
    tags=["Favoritos (Accesos Rápidos)"],
)

# ===============================================
# GET: Obtener todos los favoritos del usuario
# ===============================================
@router.get(
    "/", 
    response_model=List[schemas_favorito.UsuarioFavoritoResponse],
    status_code=status.HTTP_200_OK,
    summary="Obtiene los 6 accesos rápidos del usuario autenticado."
)
def read_favoritos(
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user)
):
    """
    Retorna la lista ordenada de accesos rápidos (favoritos)
    para el usuario que ha iniciado sesión.
    """
    return service_favoritos.get_favoritos_by_user_id(db, current_user.id)

# ===============================================
# POST: Crear un nuevo favorito
# ===============================================
@router.post(
    "/", 
    response_model=schemas_favorito.UsuarioFavoritoResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Crea un nuevo acceso rápido (máximo 6)."
)
def create_favorito_route(
    favorito: schemas_favorito.UsuarioFavoritoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crea un nuevo acceso rápido. Valida el límite de 6 botones y la unicidad del orden.
    """
    return service_favoritos.create_favorito(db, favorito, current_user.id)

# ===============================================
# PUT: Actualizar un favorito
# ===============================================
@router.put(
    "/{favorito_id}", 
    response_model=schemas_favorito.UsuarioFavoritoResponse,
    summary="Actualiza un acceso rápido por su ID."
)
def update_favorito_route(
    favorito_id: int,
    favorito_update: schemas_favorito.UsuarioFavoritoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualiza el nombre, ruta o el orden de un acceso rápido existente.
    """
    return service_favoritos.update_favorito(db, favorito_id, favorito_update, current_user.id)

# ===============================================
# DELETE: Eliminar un favorito
# ===============================================
@router.delete(
    "/{favorito_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Elimina un acceso rápido por su ID."
)
def delete_favorito_route(
    favorito_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Elimina un acceso rápido si pertenece al usuario autenticado.
    """
    service_favoritos.delete_favorito(db, favorito_id, current_user.id)
    return {"detail": "Acceso rápido eliminado exitosamente."}