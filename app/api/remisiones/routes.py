from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Usuario as models_usuario
from app.schemas import remision as schemas
from app.services import remision as service

router = APIRouter()

@router.post("/", response_model=schemas.Remision, status_code=status.HTTP_201_CREATED)
def create_remision(
    remision_in: schemas.RemisionCreate,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    try:
        return service.create_remision(db, remision_in, current_user.id, current_user.empresa_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=schemas.RemisionResponse)
def get_remisiones(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    return service.get_remisiones(db, current_user.empresa_id, skip, limit)

@router.put("/{remision_id}/aprobar", response_model=schemas.Remision)
def aprobar_remision(
    remision_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    try:
        return service.aprobar_remision(db, remision_id, current_user.empresa_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{remision_id}/anular", response_model=schemas.Remision)
def anular_remision(
    remision_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    try:
        return service.anular_remision(db, remision_id, current_user.empresa_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
