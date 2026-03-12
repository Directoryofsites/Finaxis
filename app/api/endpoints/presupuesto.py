from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal

from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_optional
from app.models.usuario import Usuario
from app.models.presupuesto import (
    PresupuestoCabecera as PresupuestoCabeceraModel,
    PresupuestoDetalle as PresupuestoDetalleModel
)
from app.schemas.presupuesto import (
    PresupuestoCabecera as PresupuestoCabeceraSchema, 
    PresupuestoCabeceraCreate,
    PresupuestoDetalle as PresupuestoDetalleSchema, 
    BudgetEntryRequest, BatchBudgetEdit, PresupuestoDetalleUpdate
)
from app.services.presupuesto_service import PresupuestoService

router = APIRouter()

@router.get("/puc", response_model=List[dict])
def get_puc_for_budget(
    anio: int = Query(..., description="Año presupuestal"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return PresupuestoService.get_puc_for_budget(db, current_user.empresa_id, anio)

@router.post("/registrar", status_code=201)
def registrar_presupuesto(
    request: BudgetEntryRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return PresupuestoService.register_account_budget(db, current_user.empresa_id, request)

@router.get("/detalle/{codigo}/{anio}", response_model=List[PresupuestoDetalleSchema])
def get_detalle_mensual(
    codigo: str,
    anio: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    cabecera = db.query(PresupuestoCabeceraModel).filter(
        PresupuestoCabeceraModel.empresa_id == current_user.empresa_id,
        PresupuestoCabeceraModel.anio == anio
    ).first()
    
    if not cabecera:
        return []
        
    return db.query(PresupuestoDetalleModel).filter(
        PresupuestoDetalleModel.cabecera_id == cabecera.id,
        PresupuestoDetalleModel.codigo_cuenta == codigo
    ).order_by(PresupuestoDetalleModel.mes).all()

@router.patch("/editar-mes/{detalle_id}", response_model=PresupuestoDetalleSchema)
def editar_mes(
    detalle_id: int,
    request: PresupuestoDetalleUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        return PresupuestoService.edit_monthly_budget(db, detalle_id, current_user.id, request.nuevo_valor, request.motivo)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/comparativo")
def get_comparativo(
    anio: int = Query(...),
    meses: List[int] = Query(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return PresupuestoService.get_comparative_report(db, current_user.empresa_id, anio, meses)

@router.get("/comparativo/get-signed-url")
def get_signed_comparativo_url(
    anio: int = Query(...),
    meses: List[int] = Query(...),
    current_user: Usuario = Depends(get_current_user)
):
    """Generates a signed URL for budget exports."""
    from app.services.reports import generate_signed_report_url
    
    # We use a generic endpoint base, the frontend will append /csv or /pdf
    signed_token = generate_signed_report_url(
        endpoint="/api/presupuesto/comparativo",
        expiration_seconds=60,
        empresa_id=current_user.empresa_id,
        anio=anio,
        meses=meses
    )
    return {"signed_url_token": signed_token}

@router.get("/comparativo/csv")
def get_comparativo_csv(
    anio: int = Query(None),
    meses: List[int] = Query(None),
    signed_token: str = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[Usuario] = Depends(get_current_user_optional)
):
    from app.services.reports import verify_signed_report_url
    
    empresa_id = None
    if signed_token:
        params = verify_signed_report_url(signed_token, "/api/presupuesto/comparativo")
        if not params:
            raise HTTPException(status_code=401, detail="Token no válido o expirado")
        empresa_id = params["empresa_id"]
        anio = params["anio"]
        meses = params["meses"]
    elif current_user:
        empresa_id = current_user.empresa_id
    else:
        raise HTTPException(status_code=401, detail="No autenticado")

    csv_data = PresupuestoService.generate_comparative_csv(db, empresa_id, anio, meses)
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=comparativo_presupuesto_{anio}.csv"}
    )

@router.get("/comparativo/pdf")
def get_comparativo_pdf(
    anio: int = Query(None),
    meses: List[int] = Query(None),
    signed_token: str = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[Usuario] = Depends(get_current_user_optional)
):
    from app.services.reports import verify_signed_report_url
    
    empresa_id = None
    if signed_token:
        params = verify_signed_report_url(signed_token, "/api/presupuesto/comparativo")
        if not params:
            raise HTTPException(status_code=401, detail="Token no válido o expirado")
        empresa_id = params["empresa_id"]
        anio = params["anio"]
        meses = params["meses"]
    elif current_user:
        empresa_id = current_user.empresa_id
    else:
        raise HTTPException(status_code=401, detail="No autenticado")

    return PresupuestoService.generate_comparative_pdf(db, empresa_id, anio, meses)

@router.post("/importar")
async def importar_presupuesto(
    anio: int = Form(...),
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Endpoint para importar presupuesto desde CSV o Excel.
    """
    contents = await archivo.read()
    try:
        return PresupuestoService.bulk_import_budget(
            db=db, 
            empresa_id=current_user.empresa_id, 
            anio=anio, 
            file_content=contents, 
            filename=archivo.filename
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/comparativo/pdf-grafico")
def get_comparativo_pdf_grafico(
    anio: int = Query(None),
    meses: List[int] = Query(None),
    signed_token: str = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[Usuario] = Depends(get_current_user_optional)
):
    from app.services.reports import verify_signed_report_url
    
    empresa_id = None
    if signed_token:
        params = verify_signed_report_url(signed_token, "/api/presupuesto/comparativo")
        if not params:
            raise HTTPException(status_code=401, detail="Token no válido o expirado")
        empresa_id = params["empresa_id"]
        anio = params["anio"]
        meses = params["meses"]
    elif current_user:
        empresa_id = current_user.empresa_id
    else:
        raise HTTPException(status_code=401, detail="No autenticado")

    return PresupuestoService.generate_graphical_pdf(db, empresa_id, anio, meses)
