from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from datetime import date

from app.core import database, security
from app.models.usuario import Usuario
from app.schemas import produccion as schemas_prod
from app.services import produccion as service_prod

router = APIRouter()

# --- RECETAS ---

@router.post("/recetas", response_model=schemas_prod.RecetaResponse)
def create_receta(
    receta: schemas_prod.RecetaCreate,
    db: Session = Depends(database.get_db),
    current_user: Usuario = Depends(security.get_current_user)
):
    return service_prod.create_receta(db, receta, current_user.empresa_id)

@router.get("/recetas", response_model=List[schemas_prod.RecetaResponse])
def get_recetas(
    db: Session = Depends(database.get_db),
    current_user: Usuario = Depends(security.get_current_user)
):
    return service_prod.get_recetas(db, current_user.empresa_id)

@router.get("/recetas/{receta_id}", response_model=schemas_prod.RecetaResponse)
def get_receta(
    receta_id: int,
    db: Session = Depends(database.get_db),
    current_user: Usuario = Depends(security.get_current_user)
):
    receta = service_prod.get_receta_by_id(db, receta_id, current_user.empresa_id)
    if not receta:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    return receta

# --- ORDENES DE PRODUCCION ---

@router.post("/ordenes", response_model=schemas_prod.OrdenProduccionResponse)
def create_orden(
    orden: schemas_prod.OrdenProduccionCreate,
    db: Session = Depends(database.get_db),
    current_user: Usuario = Depends(security.get_current_user)
):
    return service_prod.create_orden(db, orden, current_user.empresa_id, current_user.id)

    return service_prod.create_orden(db, orden, current_user.empresa_id, current_user.id)

@router.get("/ordenes", response_model=List[schemas_prod.OrdenProduccionResponse])
def get_ordenes(
    db: Session = Depends(database.get_db),
    current_user: Usuario = Depends(security.get_current_user)
):
    return service_prod.get_ordenes(db, current_user.empresa_id)

@router.get("/ordenes/{orden_id}", response_model=schemas_prod.OrdenProduccionResponse)
def get_orden(
    orden_id: int,
    db: Session = Depends(database.get_db),
    current_user: Usuario = Depends(security.get_current_user)
):
    orden = service_prod.get_orden_by_id(db, orden_id, current_user.empresa_id)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    return orden

# --- ACCIONES DE PRODUCCION ---

@router.post("/ordenes/{orden_id}/consumo", response_model=schemas_prod.OrdenProduccionResponse)
def procesar_consumo(
    orden_id: int,
    bodega_origen_id: int = Query(..., description="Bodega de donde sale la MP"),
    items: List[schemas_prod.RecetaDetalleCreate] = Body(..., description="Lista de insumos y cantidades a consumir"),
    db: Session = Depends(database.get_db),
    current_user: Usuario = Depends(security.get_current_user)
):
    """
    Registra el consumo batch de materia prima.
    Genera documento contable y descarga de inventario.
    """
    return service_prod.procesar_consumo_mp(
        db, orden_id, items, bodega_origen_id, current_user.empresa_id, current_user.id
    )

@router.post("/ordenes/{orden_id}/recurso", response_model=schemas_prod.OrdenProduccionResponse)
def agregar_recurso(
    orden_id: int,
    recurso: schemas_prod.OrdenProduccionRecursoCreate,
    db: Session = Depends(database.get_db),
    current_user: Usuario = Depends(security.get_current_user)
):
    return service_prod.agregar_recurso(db, orden_id, recurso, current_user.empresa_id)

@router.post("/ordenes/{orden_id}/cierre", response_model=schemas_prod.OrdenProduccionResponse)
def cerrar_orden(
    orden_id: int,
    cantidad_real: float = Query(..., gt=0),
    db: Session = Depends(database.get_db),
    current_user: Usuario = Depends(security.get_current_user)
):
    """
    Cierra la orden de producción.
    Calcula costos finales, ingresa producto terminado a bodega y genera contabilidad.
    """
    return service_prod.cerrar_orden(db, orden_id, cantidad_real, current_user.empresa_id, current_user.id)
