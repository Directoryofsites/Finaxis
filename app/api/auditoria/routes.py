from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.services import auditoria as auditoria_service
from app.schemas import auditoria as auditoria_schemas
from app.schemas import documento as schemas_doc
from app.core.database import get_db
# --- IMPORTACIONES CORREGIDAS ---
from app.core.security import get_current_user
from app.models import Usuario as models_usuario

router = APIRouter()

@router.get("/log-operaciones", response_model=List[auditoria_schemas.LogOperacionItem])
def get_log_operaciones(
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    db: Session = Depends(get_db),
    # --- TIPO DE DATO CORREGIDO ---
    current_user: models_usuario = Depends(get_current_user)
):
    """
    Obtiene el log de operaciones de auditoría (anulaciones) para la empresa,
    con un filtro opcional por rango de fechas.
    """
    return auditoria_service.get_log_operaciones(
        db=db,
        empresa_id=current_user.empresa_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )

@router.get("/consecutivos/{tipo_documento_id}", response_model=schemas_doc.AuditoriaConsecutivosResponse)
def get_consecutivos_audit(
    tipo_documento_id: int,
    db: Session = Depends(get_db),
    # --- TIPO DE DATO CORREGIDO ---
    current_user: models_usuario = Depends(get_current_user)
):
    """
    Endpoint para ejecutar la auditoría de consecutivos de un tipo de documento.
    """
    try:
        resultado_auditoria = auditoria_service.get_auditoria_consecutivos(
            db=db,
            empresa_id=current_user.empresa_id,
            tipo_documento_id=tipo_documento_id
        )
        return resultado_auditoria
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al realizar la auditoría: {str(e)}"
        )