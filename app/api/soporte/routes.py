# app/api/soporte/routes.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import soporte as services_soporte
from app.schemas import soporte as schemas_soporte
from app.schemas import usuario as schemas_usuario # NUEVO IMPORT
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

@router.get(
    "/users/accountants",
    response_model=list[schemas_usuario.UserBasic], # CORRECTED SCHEMA
    dependencies=[Depends(has_permission("soporte:acceder_panel"))]
)
def get_accountant_users_route(db: Session = Depends(get_db)):
    """
    Obtiene lista de usuarios con rol Contador.
    """
    return services_soporte.get_accountant_users(db)

@router.get(
    "/empresas/search",
    response_model=schemas_soporte.EmpresaSearchResponse,
    dependencies=[Depends(has_permission("soporte:acceder_panel"))]
)
def search_empresas_route(
    q: str = None,
    role_filter: str = 'ADMIN', # ADMIN | CONTADOR
    type_filter: str = 'REAL',  # REAL | PLANTILLA
    owner_id: int = None,       # NUEVO PARAM
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db)
):
    return services_soporte.search_empresas(
        db, q=q, role_filter=role_filter, type_filter=type_filter, owner_id=owner_id, page=page, size=size
    )

@router.post(
    "/empresas/from-template",
    response_model=schemas_soporte.EmpresaConUsuarios, # Reusamos el schema de respuesta
    dependencies=[Depends(has_permission("soporte:acceder_panel"))]
)
def create_empresa_from_template_route(
    data: schemas_soporte.EmpresaCreateFromTemplate,
    db: Session = Depends(get_db)
):
    """
    Crea una nueva empresa basada en una plantilla existente (copia PUC, Impuestos, Documentos).
    """
    return services_soporte.create_empresa_from_template(db, data)

@router.post(
    "/empresas/{empresa_id}/convert-to-template",
    response_model=schemas_soporte.EmpresaConUsuarios, # Uses common schema
    dependencies=[Depends(has_permission("soporte:acceder_panel"))]
)
def convert_empresa_to_template_route(
    empresa_id: int,
    data: schemas_soporte.TemplateConversionRequest,
    db: Session = Depends(get_db)
):
    """
    Crea una PLANTILLA a partir de una empresa existente (Clonación).
    La empresa original permanece intacta.
    """
    # Import service function directly from empresa service where it was implemented
    from app.services import empresa as empresa_service
    return empresa_service.create_template_from_existing(
        db, 
        source_empresa_id=empresa_id, 
        template_category=data.template_category
    )
