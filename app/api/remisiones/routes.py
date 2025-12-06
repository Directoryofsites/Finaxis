from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
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
    numero: Optional[int] = Query(None),
    tercero_id: Optional[int] = Query(None, alias="tercero"),
    estado: Optional[str] = Query(None),
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    return service.get_remisiones(
        db, 
        current_user.empresa_id, 
        skip, 
        limit,
        numero=numero,
        tercero_id=tercero_id,
        estado=estado,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )

@router.get("/{remision_id}", response_model=schemas.Remision)
def get_remision(
    remision_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    remision = service.get_remision_by_id(db, remision_id, current_user.empresa_id)
    if not remision:
        raise HTTPException(status_code=404, detail="Remisión no encontrada")
    return remision

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{remision_id}", response_model=schemas.Remision)
def update_remision(
    remision_id: int,
    remision_in: schemas.RemisionCreate,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    try:
        return service.update_remision(db, remision_id, remision_in, current_user.empresa_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================= PDF ENDPOINTS =================
from fastapi.responses import Response
from app.services import pdf_remision

@router.get("/{remision_id}/pdf")
def get_remision_pdf(
    remision_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    remision = service.get_remision_by_id(db, remision_id, current_user.empresa_id)
    if not remision: raise HTTPException(status_code=404, detail="Remisión no encontrada")
    
    # Needs empresa object for header (optional, passing None for now or fetch)
    pdf_bytes = pdf_remision.generar_pdf_remision_individual(remision, None)
    
    return Response(content=pdf_bytes, media_type="application/pdf", headers={
        "Content-Disposition": f"inline; filename=Remision_{remision.numero}.pdf"
    })

@router.get("/pdf/listado")
def get_remisiones_list_pdf(
    numero: Optional[int] = Query(None),
    tercero_id: Optional[int] = Query(None, alias="tercero"),
    estado: Optional[str] = Query(None),
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    # Re-use service filter logic
    result = service.get_remisiones(
        db, current_user.empresa_id, skip=0, limit=10000, 
        numero=numero, tercero_id=tercero_id, estado=estado, 
        fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    
    filtros_desc = f"Estado: {estado or 'Todo'}, Fecha: {fecha_inicio or 'Inicio'} - {fecha_fin or 'Fin'}"
    pdf_bytes = pdf_remision.generar_pdf_listado_remisiones(result['remisiones'], None, filtros_desc)
    
    return Response(content=pdf_bytes, media_type="application/pdf", headers={
        "Content-Disposition": "inline; filename=Listado_Remisiones.pdf"
    })

@router.get("/pdf/reporte-completo")
def get_remisiones_reporte_pdf(
    filtro_estado: Optional[str] = Query(None),
    tercero_id: Optional[int] = Query(None, alias="tercero"),
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    datos = service.get_detalles_reporte(db, current_user.empresa_id, filtro_estado, tercero_id)
    pdf_bytes = pdf_remision.generar_pdf_reporte_completo(datos, None)
    
    return Response(content=pdf_bytes, media_type="application/pdf", headers={
        "Content-Disposition": "inline; filename=Reporte_Remisionado_Facturado.pdf"
    })
