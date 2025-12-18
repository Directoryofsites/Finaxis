from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.schemas.propiedad_horizontal import concepto as schemas
from app.services.propiedad_horizontal import concepto_service

router = APIRouter()

@router.get("/conceptos", response_model=List[schemas.PHConcepto])
def listar_conceptos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Ruta para listar conceptos de facturación PH.
    """
    return concepto_service.service.get_all(db, current_user.empresa_id)

@router.post("/conceptos", response_model=schemas.PHConcepto)
def crear_concepto(
    concepto_in: schemas.PHConceptoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crea un nuevo concepto de facturación.
    """
    return concepto_service.service.create(db, concepto_in, current_user.empresa_id)

@router.put("/conceptos/{id}", response_model=schemas.PHConcepto)
def actualizar_concepto(
    id: int,
    concepto_in: schemas.PHConceptoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualiza un concepto existente.
    """
    concepto = concepto_service.service.get_by_id(db, id)
    if not concepto or concepto.empresa_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Concepto no encontrado")
    return concepto_service.service.update(db, concepto, concepto_in)

@router.delete("/conceptos/{id}")
def eliminar_concepto(
    id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Elimina (lógicamente) un concepto.
    """
    concepto = concepto_service.service.get_by_id(db, id)
    if not concepto or concepto.empresa_id != current_user.empresa_id:
        raise HTTPException(status_code=404, detail="Concepto no encontrado")
    return concepto_service.service.delete(db, id)
