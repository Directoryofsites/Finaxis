from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Usuario
from app.schemas.propiedad_horizontal import unidad as schemas
from app.schemas.propiedad_horizontal import configuracion as config_schemas
from app.services.propiedad_horizontal import unidad_service, configuracion_service, facturacion_service, pago_service

router = APIRouter()

# --- REQUEST SCHEMAS ---
class FacturacionMasivaRequest(BaseModel):
    fecha: date
    conceptos_ids: Optional[List[int]] = None

class PagoRequest(BaseModel):
    unidad_id: int
    monto: float
    fecha: date
    forma_pago_id: int = None # Opcional por ahora

# --- UNIDADES ---

@router.get("/unidades", response_model=List[schemas.PHUnidad])
def listar_unidades(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return unidad_service.get_unidades(db, empresa_id=current_user.empresa_id, skip=skip, limit=limit)

@router.post("/unidades", response_model=schemas.PHUnidad, status_code=status.HTTP_201_CREATED)
def crear_unidad(
    unidad: schemas.PHUnidadCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return unidad_service.crear_unidad(db, unidad, empresa_id=current_user.empresa_id)

@router.get("/unidades/{unidad_id}", response_model=schemas.PHUnidad)
def ver_unidad(
    unidad_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    db_unidad = unidad_service.get_unidad_by_id(db, unidad_id, empresa_id=current_user.empresa_id)
    if not db_unidad:
        raise HTTPException(status_code=404, detail="Unidad no encontrada")
    return db_unidad

@router.put("/unidades/{unidad_id}", response_model=schemas.PHUnidad)
def actualizar_unidad(
    unidad_id: int,
    unidad: schemas.PHUnidadCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    updated_unidad = unidad_service.update_unidad(
        db, 
        unidad_id, 
        unidad, 
        empresa_id=current_user.empresa_id,
        usuario_id=current_user.id
    )
    if not updated_unidad:
        raise HTTPException(status_code=404, detail="Unidad no encontrada")
    return updated_unidad

@router.delete("/unidades/{unidad_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_unidad(
    unidad_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    success = unidad_service.delete_unidad(db, unidad_id, empresa_id=current_user.empresa_id)
    if not success:
         raise HTTPException(status_code=404, detail="Unidad no encontrada")
    return None

# --- CONFIGURACION ---
@router.get("/configuracion", response_model=config_schemas.PHConfiguracionResponse)
def get_configuracion(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return configuracion_service.get_configuracion(db, current_user.empresa_id)

@router.put("/configuracion", response_model=config_schemas.PHConfiguracionResponse)
def update_configuracion(
    config: config_schemas.PHConfiguracionUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    print(f"DEBUG: update_configuracion called by user {current_user.id}. Payload: {config.dict()}")
    return configuracion_service.update_configuracion(db, current_user.empresa_id, config)

@router.get("/conceptos", response_model=List[config_schemas.PHConceptoResponse])
def get_conceptos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return configuracion_service.get_conceptos(db, current_user.empresa_id)

@router.post("/conceptos", response_model=config_schemas.PHConceptoResponse)
def create_concepto(
    concepto: config_schemas.PHConceptoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return configuracion_service.crear_concepto(db, concepto, current_user.empresa_id)

@router.put("/conceptos/{concepto_id}", response_model=config_schemas.PHConceptoResponse)
def update_concepto(
    concepto_id: int,
    concepto: config_schemas.PHConceptoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    updated = configuracion_service.update_concepto(db, concepto_id, concepto, current_user.empresa_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Concepto no encontrado")
    return updated

@router.delete("/conceptos/{concepto_id}")
def delete_concepto(
    concepto_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    success = configuracion_service.delete_concepto(db, concepto_id, current_user.empresa_id)
    if not success:
        raise HTTPException(status_code=404, detail="Concepto no encontrado")
    return {"message": "Concepto eliminado correctamente"}

# --- FACTURACION MASIVA ---
@router.post("/facturacion/masiva")
def generar_facturacion_masiva(
    payload: FacturacionMasivaRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    resultado = facturacion_service.generar_facturacion_masiva(
        db, 
        empresa_id=current_user.empresa_id, 
        fecha_factura=payload.fecha,
        usuario_id=current_user.id,
        conceptos_ids=payload.conceptos_ids
    )
    return resultado

# --- PAGOS Y TESORERIA ---
@router.get("/pagos/estado-cuenta/{unidad_id}")
def get_estado_cuenta(
    unidad_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return pago_service.get_estado_cuenta_unidad(db, unidad_id, current_user.empresa_id)

@router.post("/pagos/registrar")
def registrar_pago(
    payload: PagoRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return pago_service.registrar_pago_unidad(
        db,
        unidad_id=payload.unidad_id,
        empresa_id=current_user.empresa_id,
        usuario_id=current_user.id,
        monto=payload.monto,
        fecha_pago=payload.fecha,
        forma_pago_id=payload.forma_pago_id
    )

@router.get("/pagos/historial/{unidad_id}")
def get_historial_cuenta(
    unidad_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return pago_service.get_historial_cuenta_unidad(db, unidad_id, current_user.empresa_id)
