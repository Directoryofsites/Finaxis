# app/api/bodegas/routes.py (Versión Centralizada y Completa)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core import security
from app.models import usuario as models_usuario
from app.schemas import bodega as schemas_bodega
from app.services import inventario as service_inventario

router = APIRouter()

@router.post("/", response_model=schemas_bodega.Bodega, status_code=status.HTTP_201_CREATED)
def create_bodega(
    bodega: schemas_bodega.BodegaCreate,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(security.get_current_user)
):
    """
    Crea una nueva bodega para la empresa del usuario actual.
    """
    if not current_user.empresa_id:
        raise HTTPException(status_code=403, detail="El usuario no está asociado a ninguna empresa.")
    return service_inventario.create_bodega(db=db, bodega=bodega, empresa_id=current_user.empresa_id)

@router.get("/", response_model=List[schemas_bodega.Bodega])
def get_bodegas_por_empresa(
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(security.get_current_user)
):
    """
    Obtiene todas las bodegas que pertenecen a la empresa del usuario actual.
    """
    if not current_user.empresa_id:
        raise HTTPException(status_code=403, detail="El usuario no está asociado a ninguna empresa.")
    return service_inventario.get_bodegas_by_empresa(db=db, empresa_id=current_user.empresa_id)

@router.put("/{bodega_id}", response_model=schemas_bodega.Bodega)
def update_bodega(
    bodega_id: int,
    bodega: schemas_bodega.BodegaUpdate,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(security.get_current_user)
):
    """
    Actualiza una bodega existente.
    """
    if not current_user.empresa_id:
        raise HTTPException(status_code=403, detail="El usuario no está asociado a ninguna empresa.")
    db_bodega = service_inventario.update_bodega(db, bodega_id=bodega_id, bodega=bodega, empresa_id=current_user.empresa_id)
    if db_bodega is None:
        raise HTTPException(status_code=404, detail="Bodega no encontrada.")
    return db_bodega

@router.delete("/{bodega_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bodega(
    bodega_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(security.get_current_user)
):
    """
    Elimina una bodega, previa validación de que no esté en uso.
    """
    if not current_user.empresa_id:
        raise HTTPException(status_code=403, detail="El usuario no está asociado a ninguna empresa.")
    service_inventario.delete_bodega(db=db, bodega_id=bodega_id, empresa_id=current_user.empresa_id)
    return