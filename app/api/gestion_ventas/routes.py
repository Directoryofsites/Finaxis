# app/api/gestion_ventas/routes.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import has_permission
from app.models import usuario as models_usuario
from app.services import gestion_ventas as service_gestion_ventas
from app.schemas import gestion_ventas as schemas_ventas

router = APIRouter()

@router.post(
    "/reporte",
    response_model=schemas_ventas.GestionVentasResponse,
    summary="Genera el Reporte de Gestión de Ventas"
)
def generar_reporte_gestion_ventas(
    filtros: schemas_ventas.GestionVentasFiltros,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("ventas:ver_reporte_gestion"))
):
    """
    Endpoint para generar el reporte de gestión de ventas con estados, saldos y KPIs.
    """
    return service_gestion_ventas.get_reporte_gestion_ventas(
        db=db, 
        empresa_id=current_user.empresa_id, 
        filtros=filtros
    )

# --- INICIO DE NUEVO ENDPOINT PARA PDF ---

@router.post(
    "/solicitar-impresion-reporte",
    response_model=schemas_ventas.GestionVentasSignedURLResponse,
    summary="Solicita una URL firmada para imprimir el Reporte de Gestión de Ventas"
)
def solicitar_url_impresion_reporte(
    filtros: schemas_ventas.GestionVentasFiltros,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("ventas:ver_reporte_gestion"))
):
    """
    Crea un token temporal con los filtros y devuelve una URL segura para descargar el PDF.
    """
    signed_url = service_gestion_ventas.generar_url_firmada_reporte_gestion_ventas(
        db=db,
        empresa_id=current_user.empresa_id,
        user_id=current_user.id,
        filtros=filtros
    )
    return {"signed_url": signed_url}

# --- FIN DE NUEVO ENDPOINT PARA PDF ---