from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from app.core.database import get_db
from app.services.flujo_efectivo import CashFlowService
# Asumiendo un sistema de autenticación existente
# from app.core.auth import get_current_user 

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
    Clasifica movimientos de cuentas del Grupo 11 (Disponible) en Operación, Inversión y Financiación
    basado en su contrapartida.
    """
    result = CashFlowService.calculate_statement(db, empresa_id, fecha_inicio, fecha_fin)
    return result

# --- PUNTOS DE ACCESO PARA PDF ---

@router.get("/flujo-efectivo/get-signed-url")
def get_signed_cash_flow_url(
    fecha_inicio: date,
    fecha_fin: date,
    empresa_id: int = Query(..., description="ID de la empresa"),
    db: Session = Depends(get_db)
):
    from app.services import reports as reports_service
    
    pdf_endpoint = "/api/analisis/flujo-efectivo/imprimir"
    
    # Generar Token
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
    from fastapi.responses import Response
    from fastapi import HTTPException, status
    
    # 1. Verificar Token
    verified_params = reports_service.verify_signed_report_url(
        signed_token, 
        "/api/analisis/flujo-efectivo/imprimir"
    )
    
    if not verified_params:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="URL expirada o inválida"
        )
        
    # 2. Extraer parámetros seguros
    fecha_inicio = date.fromisoformat(verified_params["fecha_inicio"])
    fecha_fin = date.fromisoformat(verified_params["fecha_fin"])
    empresa_id = verified_params["empresa_id"]
    
    # 3. Generar PDF
    pdf_content = CashFlowService.generate_pdf_statement(db, empresa_id, fecha_inicio, fecha_fin)
    
    filename = f"Flujo_Efectivo_{fecha_inicio}_{fecha_fin}.pdf"
    
    return Response(
        content=pdf_content, 
        media_type="application/pdf", 
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )
