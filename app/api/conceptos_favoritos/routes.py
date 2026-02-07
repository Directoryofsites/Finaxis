from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import usuario as models_usuario
from app.schemas import concepto_favorito as schemas
from app.services import concepto_favorito as service

router = APIRouter(
    prefix="/conceptos-favoritos",
    tags=["Conceptos Favoritos (Contabilidad)"],
)

@router.get("/", response_model=List[schemas.ConceptoFavoritoResponse])
def get_conceptos_favoritos(
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """
    Obtiene todos los conceptos favoritos de la empresa del usuario actual.
    """
    if not current_user.empresa_id:
        return []
    return service.get_conceptos_by_empresa(db, current_user.empresa_id)

@router.post("/", response_model=schemas.ConceptoFavoritoResponse, status_code=status.HTTP_201_CREATED)
def create_concepto_favorito(
    concepto_in: schemas.ConceptoFavoritoBase,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """
    Crea un nuevo concepto favorito para la empresa del usuario.
    """
    if not current_user.empresa_id:
        raise HTTPException(status_code=400, detail="Usuario no tiene empresa asignada.")
        
    # Construir el objeto completo para el servicio
    concepto_create = schemas.ConceptoFavoritoCreate(
        **concepto_in.model_dump(),
        empresa_id=current_user.empresa_id,
        created_by=current_user.id,
        updated_by=current_user.id
    )
    
    return service.create_concepto_favorito(db, concepto_create, current_user.id)