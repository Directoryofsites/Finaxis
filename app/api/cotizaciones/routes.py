from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from ...core.database import get_db
from ...services import cotizacion as service
from ...schemas import cotizacion as schemas
from ...core.security import get_current_user
from ...models.usuario import Usuario
from fastapi.responses import Response
from ...services import reportes_cotizacion

router = APIRouter(
    tags=["cotizaciones"]
)

@router.post("/", response_model=schemas.Cotizacion)
def crear_cotizacion(
    cotizacion_in: schemas.CotizacionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return service.create_cotizacion(db, cotizacion_in, current_user.id, current_user.empresa_id)

@router.get("/", response_model=schemas.CotizacionResponse)
def listar_cotizaciones(
    skip: int = 0,
    limit: int = 100,
    numero: Optional[int] = None,
    tercero_id: Optional[int] = None,
    estado: Optional[str] = None,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return service.get_cotizaciones(
        db, 
        current_user.empresa_id, 
        skip, limit, 
        numero, tercero_id, estado, fecha_inicio, fecha_fin
    )

@router.get("/{id}", response_model=schemas.Cotizacion)
def obtener_cotizacion(
    id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    cot = service.get_cotizacion_by_id(db, id, current_user.empresa_id)
    if not cot:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    return cot

@router.put("/{id}", response_model=schemas.Cotizacion)
def actualizar_cotizacion(
    id: int,
    cotizacion_in: schemas.CotizacionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return service.update_cotizacion(db, id, cotizacion_in, current_user.empresa_id)

@router.patch("/{id}/estado")
def cambiar_estado(
    id: int,
    estado: str = Query(..., description="Nuevo estado: APROBADA, ANULADA, FACTURADA"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return service.cambiar_estado(db, id, estado, current_user.empresa_id)

@router.get("/{id}/pdf")
def descargar_pdf(
    id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    pdf_content = reportes_cotizacion.generar_pdf_cotizacion(db, id, current_user.empresa_id)
    return Response(content=pdf_content, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=cotizacion_{id}.pdf"})
