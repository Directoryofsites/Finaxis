# app/api/favoritos/routes.py

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import usuario as models_usuario
from app.schemas import usuario_favorito as schemas_favorito
from app.services import favoritos as service_favoritos

router = APIRouter(
    prefix="/favoritos",
    tags=["Favoritos (Accesos Rápidos)"],
)

@router.get("/", response_model=List[schemas_favorito.UsuarioFavoritoResponse])
def get_favoritos(
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """
    Obtiene todos los accesos rápidos definidos por el usuario actual, ordenados por 'orden'.
    """
    return service_favoritos.get_favoritos_by_user_id(db, current_user.id)

@router.post("/", response_model=schemas_favorito.UsuarioFavoritoResponse, status_code=status.HTTP_201_CREATED)
def create_favorito_route(
    favorito_input: schemas_favorito.UsuarioFavoritoCreate,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """
    Crea un nuevo acceso rápido. Aplica validación de límite (máximo 24) y unicidad de orden en el servicio.
    """
    return service_favoritos.create_favorito(db, favorito_input, current_user.id)

@router.put("/{favorito_id}", response_model=schemas_favorito.UsuarioFavoritoResponse)
def update_favorito_route(
    favorito_id: int,
    favorito_update: schemas_favorito.UsuarioFavoritoUpdate,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """
    Actualiza un acceso rápido existente (ruta, nombre, orden).
    Verifica que pertenezca al usuario actual.
    """
    return service_favoritos.update_favorito(db, favorito_id, favorito_update, current_user.id)

@router.delete("/{favorito_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_favorito_route(
    favorito_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """
    Elimina un acceso rápido.
    Verifica que pertenezca al usuario actual.
    """
    service_favoritos.delete_favorito(db, favorito_id, current_user.id)
    return {"ok": True}