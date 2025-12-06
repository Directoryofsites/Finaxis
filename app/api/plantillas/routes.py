from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.services import plantilla as service
from app.schemas import plantilla as schemas
from app.core.database import get_db
# --- IMPORTACIONES CORREGIDAS ---
from app.core.security import get_current_user
from app.models import Usuario as models_usuario

router = APIRouter()

@router.post("/", response_model=schemas.PlantillaMaestra, status_code=status.HTTP_201_CREATED)
def create_plantilla(
    plantilla: schemas.PlantillaMaestraCreate,
    db: Session = Depends(get_db),
    # --- TIPO DE DATO CORREGIDO ---
    current_user: models_usuario = Depends(get_current_user)
):
    # Pasamos el empresa_id del token directamente al servicio.
    return service.create_plantilla(
        db=db, 
        plantilla=plantilla, 
        user_id=current_user.id, 
        empresa_id=current_user.empresa_id
    )

@router.get("/", response_model=List[schemas.PlantillaMaestra])
def read_plantillas(
    db: Session = Depends(get_db),
    # --- TIPO DE DATO CORREGIDO ---
    current_user: models_usuario = Depends(get_current_user)
):
    # Usamos el empresa_id del usuario autenticado.
    return service.get_plantillas_by_empresa(db, empresa_id=current_user.empresa_id)

@router.get("/{plantilla_id}", response_model=schemas.PlantillaMaestra)
def read_plantilla(
    plantilla_id: int,
    db: Session = Depends(get_db),
    # --- TIPO DE DATO CORREGIDO ---
    current_user: models_usuario = Depends(get_current_user)
):
    db_plantilla = service.get_plantilla(db, plantilla_id=plantilla_id)
    if db_plantilla is None:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    # Verificación de autorización.
    if db_plantilla.empresa_id != current_user.empresa_id:
        raise HTTPException(status_code=403, detail="No tiene permiso para acceder a esta plantilla")
    return db_plantilla

@router.put("/{plantilla_id}", response_model=schemas.PlantillaMaestra)
def update_plantilla(
    plantilla_id: int,
    plantilla_update: schemas.PlantillaMaestraUpdate,
    db: Session = Depends(get_db),
    # --- TIPO DE DATO CORREGIDO ---
    current_user: models_usuario = Depends(get_current_user)
):
    # Verificamos que el usuario tiene permiso sobre la plantilla que intenta modificar.
    db_plantilla_check = service.get_plantilla(db, plantilla_id=plantilla_id)
    if not db_plantilla_check or db_plantilla_check.empresa_id != current_user.empresa_id:
        raise HTTPException(status_code=403, detail="No tiene permiso para modificar esta plantilla")

    db_plantilla = service.update_plantilla(
        db,
        plantilla_id=plantilla_id,
        plantilla_update=plantilla_update,
        user_id=current_user.id
    )
    if db_plantilla is None:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada para actualizar")
    return db_plantilla

@router.delete("/{plantilla_id}")
def delete_plantilla(
    plantilla_id: int,
    db: Session = Depends(get_db),
    # --- TIPO DE DATO CORREGIDO ---
    current_user: models_usuario = Depends(get_current_user)
):
    # Usamos el empresa_id del usuario autenticado para la validación en el servicio.
    db_plantilla = service.delete_plantilla(db, plantilla_id=plantilla_id, empresa_id=current_user.empresa_id)
    if db_plantilla is None:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada en esta empresa.")
    return {"detail": "Plantilla eliminada exitosamente."}