# app/api/ajuste_inventario/routes.py (NUEVO ARCHIVO)

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core import security
from app.models import usuario as models_usuario
from app.schemas import inventario as schemas_inventario, documento as schemas_documento
from app.services import ajuste_inventario as service_ajuste_inventario

router = APIRouter()

@router.post(
    "/", 
    response_model=schemas_documento.Documento, 
    status_code=status.HTTP_201_CREATED,
    summary="Crea un nuevo documento de ajuste de inventario",
    description="Recibe los items a ajustar, genera el documento contable 'AI' y los movimientos de Kardex correspondientes de forma atómica."
)
def procesar_ajuste_inventario(
    ajuste_data: schemas_inventario.AjusteInventarioCreate,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(security.get_current_user)
):
    """
    Endpoint para procesar una toma de inventario físico y generar los ajustes.
    """
    return service_ajuste_inventario.crear_ajuste_inventario(
        db=db, 
        ajuste_data=ajuste_data, 
        empresa_id=current_user.empresa_id,
        user_id=current_user.id
    )