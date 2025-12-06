from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.services import centro_costo as service
from app.schemas import centro_costo as schemas
from app.core.database import get_db
# --- IMPORTACIONES CORREGIDAS ---
from app.core.security import get_current_user
from app.models import Usuario as models_usuario


router = APIRouter()

@router.post("/", response_model=schemas.CentroCosto, status_code=status.HTTP_201_CREATED)
def create_centro_costo(
    centro_costo_input: schemas.CentroCostoInput,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    return service.create_centro_costo(
        db=db,
        centro_costo=centro_costo_input,
        empresa_id=current_user.empresa_id,
        user_id=current_user.id
    )

@router.get("/get-flat", response_model=List[schemas.CentroCosto])
def get_centros_costo_flat(
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    return service.get_centros_costo_flat(db, empresa_id=current_user.empresa_id)

@router.put("/{centro_costo_id}", response_model=schemas.CentroCosto)
def update_centro_costo(
    centro_costo_id: int,
    centro_costo: schemas.CentroCostoUpdateInput,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    db_cc = service.update_centro_costo(
        db,
        centro_costo_id=centro_costo_id,
        centro_costo_update=centro_costo,
        empresa_id=current_user.empresa_id,
        user_id=current_user.id
    )
    if db_cc is None:
        raise HTTPException(status_code=404, detail="Centro de costo no encontrado en esta empresa.")
    return db_cc

@router.delete("/{centro_costo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_centro_costo(
    centro_costo_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    result = service.delete_centro_costo(db, centro_costo_id=centro_costo_id, empresa_id=current_user.empresa_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Centro de costo no encontrado en esta empresa.")
    return