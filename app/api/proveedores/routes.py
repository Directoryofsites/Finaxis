from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.services import cartera as cartera_service
from app.schemas import cartera as cartera_schema
from app.core.database import get_db
# --- IMPORTACIONES CORREGIDAS ---
from app.core.security import get_current_user
from app.models import Usuario as models_usuario

router = APIRouter()

@router.get("/facturas-pendientes/{tercero_id}", response_model=List[cartera_schema.FacturaPendiente])
def get_facturas_pendientes_proveedor(
    tercero_id: int,
    db: Session = Depends(get_db),
    # --- TIPO DE DATO CORREGIDO ---
    current_user: models_usuario = Depends(get_current_user)
):
    """
    Obtiene la lista de facturas de compra pendientes de pago para un proveedor específico.
    """
    facturas = cartera_service.get_facturas_compra_pendientes_por_tercero(
        db=db,
        tercero_id=tercero_id,
        empresa_id=current_user.empresa_id
    )
    if not facturas:
        return []
    return facturas