# app/api/traslados_inventario/routes.py (Nuevo)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.services import inventario as service_inventario
from app.services import documento as service_documento # Para crear el documento TR
from app.schemas import traslado_inventario as schemas
from app.core.database import get_db
from app.core.security import get_current_user, has_permission
from app.models import Usuario as models_usuario

router = APIRouter()

@router.post("/", response_model=schemas.TrasladoInventarioResponse, status_code=status.HTTP_201_CREATED)
def crear_traslado(
    traslado_input: schemas.TrasladoInventarioCreate,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user),
    # Permiso requerido: inventario:crear_traslado
    permiso: bool = Depends(has_permission("inventario:crear_traslado"))
):
    """
    Registra un traslado atómico de inventario entre una bodega de origen y una de destino.
    """
    
    # 1. Validaciones de negocio (Origen != Destino)
    if traslado_input.bodega_origen_id == traslado_input.bodega_destino_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La bodega de origen y destino no pueden ser la misma."
        )

    # 2. La lógica atómica reside en el servicio de inventario
    traslado_creado = service_inventario.crear_traslado_entre_bodegas(
        db=db,
        traslado=traslado_input,
        empresa_id=current_user.empresa_id,
        user_id=current_user.id
    )
    
    # El servicio devuelve el objeto Documento creado, lo mapeamos al Response Schema
    return traslado_creado
