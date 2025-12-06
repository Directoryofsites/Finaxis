from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.services import cartera as cartera_service
from app.core.database import get_db
# --- IMPORTACIONES CORREGIDAS ---
from app.core.security import get_current_user
from app.models import Usuario as models_usuario

router = APIRouter()

@router.get("/facturas-pendientes/{tercero_id}", response_model=List[Dict[str, Any]])
def get_facturas_pendientes(
    tercero_id: int,
    db: Session = Depends(get_db),
    # --- TIPO DE DATO CORREGIDO ---
    current_user: models_usuario = Depends(get_current_user)
):
    """
    Obtiene la lista de facturas con saldo pendiente para un tercero específico.
    """
    try:
        facturas = cartera_service.get_facturas_pendientes_por_tercero(
            db=db,
            tercero_id=tercero_id,
            empresa_id=current_user.empresa_id
        )
        return facturas
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al consultar la cartera: {str(e)}"
        )