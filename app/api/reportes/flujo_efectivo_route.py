from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import usuario as models_usuario
from app.services.flujo_efectivo import CashFlowService

router = APIRouter()

@router.get("/flujo-efectivo")
def get_cash_flow_statement(
    fecha_inicio: date,
    fecha_fin: date,
    empresa_id: int = Query(..., description="ID de la empresa a consultar"),
    db: Session = Depends(get_db)
):
    """
    Obtiene el reporte de Estado de Flujos de Efectivo (Método Directo Simulado).
    """
    result = CashFlowService.calculate_statement(db, empresa_id, fecha_inicio, fecha_fin)
    return result


@router.get("/flujo-efectivo/pdf", summary="Genera el PDF del flujo de efectivo (autenticado)")
def get_cash_flow_pdf(
    fecha_inicio: date,
    fecha_fin: date,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """
    Genera y retorna el PDF del Estado de Flujos de Efectivo.
    Usa autenticación JWT estándar, sin tokens firmados.
    """
    empresa_id = current_user.empresa_id
    pdf_content = CashFlowService.generate_pdf_statement(db, empresa_id, fecha_inicio, fecha_fin)
    filename = f"Flujo_Efectivo_{fecha_inicio}_{fecha_fin}.pdf"
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )


# --- Endpoints legacy de token firmado (mantenidos por compatibilidad pero redirigen al nuevo flujo) ---

@router.get("/flujo-efectivo/get-signed-url")
def get_signed_cash_flow_url(
    fecha_inicio: date,
    fecha_fin: date,
    empresa_id: int = Query(..., description="ID de la empresa"),
    db: Session = Depends(get_db)
):
    from app.services import reports as reports_service
    
    pdf_endpoint = "/api/analisis/flujo-efectivo/imprimir"
    
    signed_token = reports_service.generate_signed_report_url(
        endpoint=pdf_endpoint,
        expiration_seconds=60,
        fecha_inicio=fecha_inicio.isoformat(),
        fecha_fin=fecha_fin.isoformat(),
        empresa_id=empresa_id
    )
    
    return {"signed_url_token": signed_token}

@router.get("/flujo-efectivo/imprimir")
def print_cash_flow_pdf(
    signed_token: str = Query(..., description="Token firmado"),
    db: Session = Depends(get_db)
):
    from app.services import reports as reports_service
    from fastapi import HTTPException, status
    
    verified_params = reports_service.verify_signed_report_url(
        signed_token, 
        "/api/analisis/flujo-efectivo/imprimir"
    )
    
    if not verified_params:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="URL expirada o inválida"
        )
        
    fecha_inicio = date.fromisoformat(verified_params["fecha_inicio"])
    fecha_fin = date.fromisoformat(verified_params["fecha_fin"])
    empresa_id = verified_params["empresa_id"]
    
    pdf_content = CashFlowService.generate_pdf_statement(db, empresa_id, fecha_inicio, fecha_fin)
    filename = f"Flujo_Efectivo_{fecha_inicio}_{fecha_fin}.pdf"
    
    return Response(
        content=pdf_content, 
        media_type="application/pdf", 
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )
