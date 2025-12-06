from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.services import papelera as papelera_service
from app.schemas import papelera as schemas_papelera
from app.schemas import documento as schemas_doc
from app.core.database import get_db
# --- IMPORTACIONES CORREGIDAS Y MEJORADAS ---
from app.core.security import has_permission
from app.models import Usuario as models_usuario

router = APIRouter()

@router.get("/", response_model=List[schemas_papelera.PapeleraItem])
def get_papelera(
    db: Session = Depends(get_db),
    # --- MEJORA: Se protege con el nuevo permiso ---
    current_user: models_usuario = Depends(has_permission("papelera:usar"))
):
    """
    Obtiene la lista de documentos en la papelera para la empresa del usuario.
    """
    return papelera_service.get_documentos_eliminados(db, empresa_id=current_user.empresa_id)


@router.post("/{doc_eliminado_id}/restaurar", response_model=schemas_doc.Documento)
def restaurar_documento(
    doc_eliminado_id: int,
    db: Session = Depends(get_db),
    # --- MEJORA: Se protege con el nuevo permiso ---
    current_user: models_usuario = Depends(has_permission("papelera:usar"))
):
    """
    Restaura un documento desde la papelera a las tablas activas.
    """
    try:
        documento_restaurado = papelera_service.restaurar_documento(
            db=db,
            doc_eliminado_id=doc_eliminado_id,
            empresa_id=current_user.empresa_id
        )
        return documento_restaurado
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado al restaurar el documento: {str(e)}")

@router.post("/vaciar-automatico", status_code=status.HTTP_200_OK)
def vaciar_papelera_trigger(
    db: Session = Depends(get_db),
    # --- MEJORA: Se protege con el nuevo permiso de administrador ---
    current_user: models_usuario = Depends(has_permission("papelera:vaciar"))
):
    """
    Endpoint seguro para disparar el vaciado de la papelera de documentos
    con más de 30 días. Protegido para administradores.
    """
    # --- ELIMINADO: La comprobación manual de rol es ahora obsoleta y redundante ---
    # if current_user.rol != 'administrador':
    #     ...
    
    resultado = papelera_service.vaciar_papelera_por_antiguedad(db, empresa_id=current_user.empresa_id)
    return resultado