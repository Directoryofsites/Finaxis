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
@router.put("/recetas/{receta_id}", response_model=schemas_prod.RecetaResponse)
def update_receta(
    receta_id: int,
    receta: schemas_prod.RecetaUpdate,
    db: Session = Depends(database.get_db),
    current_user: Usuario = Depends(security.get_current_user)
):
    updated = service_prod.update_receta(db, receta_id, receta, current_user.empresa_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    return updated

# --- ORDENES DE PRODUCCION ---

@router.post("/ordenes", response_model=schemas_prod.OrdenProduccionResponse)
def create_orden(
    orden: schemas_prod.OrdenProduccionCreate,
    db: Session = Depends(database.get_db),
    current_user: Usuario = Depends(security.get_current_user)
):
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

# --- LIFECYCLE (ANULAR / ARCHIVAR / ELIMINAR) ---

@router.post("/ordenes/{orden_id}/anular", response_model=schemas_prod.OrdenProduccionResponse)
def anular_orden(
    orden_id: int,
    motivo: str = Body(..., embed=True),
    db: Session = Depends(database.get_db),
    current_user: Usuario = Depends(security.get_current_user)
):
    return service_prod.anular_orden(db, orden_id, motivo, current_user.empresa_id, current_user.id)

@router.post("/ordenes/{orden_id}/archivar", response_model=schemas_prod.OrdenProduccionResponse)
def archivar_orden(
    orden_id: int,
    archivada: bool = Body(..., embed=True),
    db: Session = Depends(database.get_db),
    current_user: Usuario = Depends(security.get_current_user)
):
    return service_prod.archivar_orden(db, orden_id, archivada, current_user.empresa_id)

@router.delete("/ordenes/{orden_id}")
def delete_orden(
    orden_id: int,
    db: Session = Depends(database.get_db),
    current_user: Usuario = Depends(security.get_current_user)
):
    return service_prod.delete_orden(db, orden_id, current_user.empresa_id)

@router.delete("/recetas/{receta_id}")
def delete_receta(
    receta_id: int,
    db: Session = Depends(database.get_db),
    current_user: Usuario = Depends(security.get_current_user)
):
    # TODO: Validar que no tenga órdenes asociadas?
    # Por ahora borrado directo (SQLAlchemy cascade handled in relationship?)
    # En Receta no pusimos cascade en Orden -> Receta (es OneToMany Receta->Orden)
    # Si hay órdenes, fallará FK. Capturar error?
    try:
        updated = service_prod.update_receta(db, receta_id, schemas_prod.RecetaUpdate(activa=False), current_user.empresa_id) # Soft delete better? Or Hard?
        # User asked for Delete. Let's try Delete if no orders.
        # But for now, let's implement logic in service if needed.
        # Check service_prod.delete_receta? Not implemented yet.
        # For now, return status 501 or implement quick delete in service.
        pass
    except Exception as e:
        raise HTTPException(status_code=400, detail="No se puede eliminar la receta (posiblemente en uso).")
    
    # Let's implement delete_receta in service too or use direct db delete here for MVP
    receta = service_prod.get_receta_by_id(db, receta_id, current_user.empresa_id)
    if not receta: raise HTTPException(404)
    db.delete(receta)
    try:
        db.commit()
    except:
        db.rollback()
        raise HTTPException(400, detail="No se puede eliminar. Puede tener órdenes asociadas.")
    return {"message": "Receta eliminada"}

from fastapi import Response
from app.services import pdf_produccion

# --- CONFIGURACION ---
from app.services import produccion_configuracion as service_config

@router.get("/configuracion", response_model=Optional[schemas_prod.ConfigProduccionResponse])
def get_config(
    db: Session = Depends(database.get_db),
    current_user: Usuario = Depends(security.get_current_user)
):
    return service_config.get_configuracion(db, current_user.empresa_id)

@router.post("/configuracion", response_model=schemas_prod.ConfigProduccionResponse)
def save_config(
    config: schemas_prod.ConfigProduccionCreate,
    db: Session = Depends(database.get_db),
    current_user: Usuario = Depends(security.get_current_user)
):
    return service_config.save_configuracion(db, config, current_user.empresa_id)

# --- PDF REPORTS ---

@router.get("/ordenes/{orden_id}/pdf")
def get_pdf_orden(
    orden_id: int,
    db: Session = Depends(database.get_db),
    current_user: Usuario = Depends(security.get_current_user)
):
    orden = service_prod.get_orden_by_id(db, orden_id, current_user.empresa_id)
    if not orden: raise HTTPException(404, detail="Orden no encontrada")
    
    # Pass empresa object directly from current_user relationship (lazy loaded)
    pdf_content = pdf_produccion.generar_pdf_orden_produccion(orden, current_user.empresa)
    return Response(content=pdf_content, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=Orden_{orden.numero_orden}.pdf"})

@router.get("/recetas/{receta_id}/pdf")
def get_pdf_receta(
    receta_id: int,
    db: Session = Depends(database.get_db),
    current_user: Usuario = Depends(security.get_current_user)
):
    receta = service_prod.get_receta_by_id(db, receta_id, current_user.empresa_id)
    if not receta: raise HTTPException(404, detail="Receta no encontrada")
    
    pdf_content = pdf_produccion.generar_pdf_receta(receta, current_user.empresa)
    return Response(content=pdf_content, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=Receta_{receta.nombre}.pdf"})

