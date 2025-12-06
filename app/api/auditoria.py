from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.schemas import usuario as usuario_schema
from app.schemas import documento as schemas_doc
from app.services import auditoria as auditoria_service

router = APIRouter()

@router.get("/consecutivos/{tipo_documento_id}", response_model=schemas_doc.AuditoriaConsecutivosResponse)
def get_consecutivos_audit(
    tipo_documento_id: int,
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
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
        # Re-lanzar excepciones HTTP conocidas (ej. 404 si no se encuentra el tipo de doc)
        raise http_exc
    except Exception as e:
        # Capturar cualquier otro error inesperado
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al realizar la auditoría: {str(e)}"
        )