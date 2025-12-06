from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.services import formato_impresion as service
from app.schemas import formato_impresion as schemas
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Usuario as models_usuario

router = APIRouter()

@router.post("/", response_model=schemas.FormatoImpresion, status_code=status.HTTP_201_CREATED)
def create_formato(
    formato: schemas.FormatoImpresionCreate,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    # El servidor asigna el empresa_id de forma segura.
    formato.empresa_id = current_user.empresa_id
    return service.create_formato(db=db, formato=formato, user_id=current_user.id)

@router.get("/", response_model=List[schemas.FormatoImpresion])
def read_formatos(
    tipo_documento_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    return service.get_formatos_by_empresa(
        db=db, 
        empresa_id=current_user.empresa_id,
        tipo_documento_id=tipo_documento_id
    )

@router.get("/{formato_id}", response_model=schemas.FormatoImpresion)
def read_formato(
    formato_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    db_formato = service.get_formato_by_id(db, formato_id=formato_id, empresa_id=current_user.empresa_id)
    if db_formato is None:
        raise HTTPException(status_code=404, detail="Formato de impresión no encontrado.")
    return db_formato

@router.put("/{formato_id}", response_model=schemas.FormatoImpresion)
def update_formato(
    formato_id: int,
    formato: schemas.FormatoImpresionUpdate,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    db_formato = service.update_formato(db, formato_id=formato_id, formato_update=formato, empresa_id=current_user.empresa_id)
    if db_formato is None:
        raise HTTPException(status_code=404, detail="Formato de impresión no encontrado para actualizar.")
    return db_formato

@router.delete("/{formato_id}", response_model=schemas.FormatoImpresion)
def delete_formato(
    formato_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    db_formato = service.delete_formato(db, formato_id=formato_id, empresa_id=current_user.empresa_id)
    if db_formato is None:
        raise HTTPException(status_code=404, detail="Formato de impresión no encontrado para eliminar.")
    return db_formato