# app/api/dashboard/routes.py

from fastapi import APIRouter, Depends, status, Body
from sqlalchemy.orm import Session
from datetime import date # Se usa en FinancialRatiosRequest
from pydantic import BaseModel # Necesaria para la clase de Request

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import usuario as models_usuario
from app.schemas import dashboard as schemas_dashboard
from app.services import dashboard as service_dashboard

from typing import Optional # Asegúrate de importar esto

router = APIRouter(prefix="/dashboard", tags=["Dashboard Financiero"])

class FinancialRatiosRequest(BaseModel):
    """Schema para solicitar el cálculo de las razones financieras."""
    fecha_inicio: date
    fecha_fin: date

@router.post(
    "/ratios-financieros",
    response_model=schemas_dashboard.FinancialRatiosResponse,
    status_code=status.HTTP_200_OK,
    summary="Calcula las 9 Razones Financieras para el Tablero de Control."
)
def get_ratios_financieros_route(
    request: FinancialRatiosRequest, # Recibe las fechas por POST
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """
    Calcula y devuelve las 9 Razones Financieras de la empresa en el rango de fechas solicitado.
    """
    # Llama al servicio de cálculo con la nueva función y las fechas
    return service_dashboard.get_financial_ratios_analysis(
        db=db,
        empresa_id=current_user.empresa_id,
        fecha_inicio=request.fecha_inicio, # Pasar las fechas
        fecha_fin=request.fecha_fin
    )

# --- NUEVO ENDPOINT: CONSUMO DE REGISTROS ---
@router.get("/consumo", summary="Obtener consumo de registros mensual")
def get_consumo_usuario(
    mes: Optional[int] = None,
    anio: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """
    Devuelve el conteo de registros.
    Params: mes (1-12), anio (2025). Si se omiten, devuelve el mes actual.
    """
    return service_dashboard.get_consumo_actual(db, current_user.empresa_id, mes, anio)