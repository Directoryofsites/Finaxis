# app/api/soporte/routes.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import soporte as services_soporte
from app.schemas import soporte as schemas_soporte
from app.core.security import has_permission

router = APIRouter(
    # CORRECCIÓN: Se elimina el prefijo duplicado. 
    # main.py ahora tiene el control total de la ruta.
    tags=["Panel de Soporte"]
)

@router.get(
    "/dashboard-data", 
    response_model=schemas_soporte.DashboardData,
    dependencies=[Depends(has_permission("soporte:acceder_panel"))]
)
def get_dashboard_data_route(db: Session = Depends(get_db)):
    """
    Endpoint "Todo en Uno": Devuelve toda la información necesaria para
    el Panel de Mando de Soporte en una sola llamada.
    """
    return services_soporte.get_dashboard_data(db=db)