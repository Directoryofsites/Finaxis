from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.services import tercero as tercero_service
from app.schemas import tercero as tercero_schema
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Usuario as models_usuario

router = APIRouter()

@router.post("/", response_model=tercero_schema.Tercero, status_code=status.HTTP_201_CREATED)
def create_tercero(
    tercero: tercero_schema.TerceroCreate,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    tercero.empresa_id = current_user.empresa_id
    db_tercero = tercero_service.get_tercero_by_nit(db, nit=tercero.nit, empresa_id=current_user.empresa_id)
    if db_tercero:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un tercero con el NIT {tercero.nit} para esta empresa."
        )
    return tercero_service.create_tercero(db=db, tercero=tercero, user_id=current_user.id)

@router.get("/check-name/", response_model=tercero_schema.TerceroExiste)
def check_tercero_name(
    nombre: str,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    db_tercero = tercero_service.get_tercero_by_razon_social(db, razon_social=nombre, empresa_id=current_user.empresa_id)
    return {"existe": db_tercero is not None}

@router.get("/", response_model=List[tercero_schema.Tercero])
def read_terceros(
    filtro: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    terceros = tercero_service.get_terceros(db, empresa_id=current_user.empresa_id, filtro=filtro, skip=skip, limit=limit)
    return terceros

@router.get("/{tercero_id}", response_model=tercero_schema.Tercero)
def read_tercero(
    tercero_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    db_tercero = tercero_service.get_tercero(db, tercero_id=tercero_id, empresa_id=current_user.empresa_id)
    if db_tercero is None:
        raise HTTPException(status_code=404, detail="Tercero no encontrado")
    return db_tercero

@router.put("/{tercero_id}", response_model=tercero_schema.Tercero)
def update_tercero(
    tercero_id: int,
    tercero: tercero_schema.TerceroUpdate,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    db_tercero = tercero_service.update_tercero(
        db,
        tercero_id=tercero_id,
        tercero_update=tercero,
        empresa_id=current_user.empresa_id,
        user_id=current_user.id
    )
    if db_tercero is None:
        raise HTTPException(status_code=404, detail="Tercero no encontrado para actualizar")
    return db_tercero

@router.delete("/{tercero_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tercero(
    tercero_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    deleted_tercero = tercero_service.delete_tercero(
        db, 
        tercero_id=tercero_id, 
        empresa_id=current_user.empresa_id
    )
    if deleted_tercero is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tercero no encontrado para eliminar")
    return

@router.get("/{tercero_id}/cuentas", response_model=List[Dict[str, Any]])
def get_cuentas_by_tercero(
    tercero_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    cuentas = tercero_service.get_cuentas_asociadas_tercero(
        db=db,
        empresa_id=current_user.empresa_id,
        tercero_id=tercero_id
    )
    return cuentas

# --- CÓDIGO NUEVO Y CORREGIDO ---
class FusionarPayload(tercero_schema.BaseModel): # CORREGIDO: Usamos el alias correcto 'tercero_schema'
    origenId: int
    destinoId: int

@router.post("/fusionar", response_model=Dict[str, Any])
def fusionar(
    payload: FusionarPayload,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    if payload.origenId == payload.destinoId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El tercero de origen y destino no pueden ser el mismo."
        )
    
    resultado = tercero_service.fusionar_terceros(
        db=db,
        origen_id=payload.origenId,
        destino_id=payload.destinoId,
        empresa_id=current_user.empresa_id
    )
    return resultado