from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.services import tipo_documento as service
from app.schemas import tipo_documento as schemas
from app.core.database import get_db
# --- IMPORTACIONES CORREGIDAS ---
from app.core.security import get_current_user, has_permission
from app.models import Usuario as models_usuario

router = APIRouter()

@router.post("/", response_model=schemas.TipoDocumento, status_code=status.HTTP_201_CREATED)
def create_tipo_documento(
    tipo_documento: schemas.TipoDocumentoCreate, 
    db: Session = Depends(get_db),
    # --- TIPO DE DATO CORREGIDO ---
    current_user: models_usuario = Depends(has_permission("contabilidad:configuracion_tipos_doc"))
):
    # Forzamos el uso del empresa_id del token.
    tipo_documento.empresa_id = current_user.empresa_id

    db_tipo_doc = service.get_tipo_documento_by_codigo(db, codigo=tipo_documento.codigo, empresa_id=current_user.empresa_id)
    if db_tipo_doc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un tipo de documento con el código {tipo_documento.codigo} para esta empresa."
        )
    return service.create_tipo_documento(db=db, tipo_documento=tipo_documento, user_id=current_user.id)

# ##################################################################
# ########### INICIO DE LA CORRECCIÓN DEFINITIVA ###########
# ##################################################################
@router.get("/", response_model=List[schemas.TipoDocumento])
def read_tipos_documento(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(has_permission("contabilidad:configuracion_tipos_doc"))
):
    """
    [FIX] Obtiene la lista COMPLETA de tipos de documento.
    """
    # [FIX] Ahora llama a la función renombrada 'get_tipos_documento'
    return service.get_tipos_documento(db, empresa_id=current_user.empresa_id, skip=skip, limit=limit)
# ##################################################################
# ########### FIN DE LA CORRECCIÓN DEFINITIVA ###########
# ##################################################################

@router.get("/{tipo_documento_id}", response_model=schemas.TipoDocumento)
def read_tipo_documento(
    tipo_documento_id: int, 
    db: Session = Depends(get_db),
    # --- TIPO DE DATO CORREGIDO ---
    current_user: models_usuario = Depends(has_permission("contabilidad:configuracion_tipos_doc"))
):
    db_tipo_doc = service.get_tipo_documento(db, tipo_documento_id=tipo_documento_id)
    if not db_tipo_doc:
        raise HTTPException(status_code=404, detail="Tipo de documento no encontrado")
    # Verificación de autorización
    if db_tipo_doc.empresa_id != current_user.empresa_id:
        raise HTTPException(status_code=403, detail="No tiene permiso para acceder a este recurso")
    return db_tipo_doc

@router.get("/{tipo_documento_id}/siguiente-numero", response_model=schemas.SiguienteNumero)
def get_siguiente_numero(
    tipo_documento_id: int, 
    db: Session = Depends(get_db),
    # --- TIPO DE DATO CORREGIDO ---
    current_user: models_usuario = Depends(has_permission("contabilidad:configuracion_tipos_doc"))
):
    # Verificación de autorización previa
    db_tipo_doc_check = service.get_tipo_documento(db, tipo_documento_id=tipo_documento_id)
    if not db_tipo_doc_check or db_tipo_doc_check.empresa_id != current_user.empresa_id:
        raise HTTPException(status_code=403, detail="No tiene permiso para acceder a este recurso")

    resultado = service.get_siguiente_numero_documento(db, tipo_documento_id=tipo_documento_id)
    if resultado is None:
        raise HTTPException(status_code=404, detail="Tipo de documento no encontrado.")
    return resultado

@router.put("/{tipo_documento_id}", response_model=schemas.TipoDocumento)
def update_tipo_documento(
    tipo_documento_id: int, 
    tipo_documento_update: schemas.TipoDocumentoUpdate, 
    db: Session = Depends(get_db),
    # --- TIPO DE DATO CORREGIDO ---
    current_user: models_usuario = Depends(has_permission("contabilidad:configuracion_tipos_doc"))
):
    # Verificación de autorización previa
    db_tipo_doc_check = service.get_tipo_documento(db, tipo_documento_id=tipo_documento_id)
    if not db_tipo_doc_check or db_tipo_doc_check.empresa_id != current_user.empresa_id:
        raise HTTPException(status_code=403, detail="No tiene permiso para modificar este recurso")

    db_tipo_doc = service.update_tipo_documento(
        db, 
        tipo_documento_id=tipo_documento_id, 
        tipo_documento=tipo_documento_update, 
        user_id=current_user.id
    )
    if db_tipo_doc is None:
        raise HTTPException(status_code=404, detail="Tipo de documento no encontrado para actualizar")
    return db_tipo_doc

@router.delete("/{tipo_documento_id}")
def delete_tipo_documento(
    tipo_documento_id: int, 
    db: Session = Depends(get_db),
    # --- TIPO DE DATO CORREGIDO ---
    current_user: models_usuario = Depends(has_permission("contabilidad:configuracion_tipos_doc"))
):
    # Usamos el empresa_id del usuario autenticado para la validación en el servicio.
    result = service.delete_tipo_documento(db, tipo_documento_id=tipo_documento_id, empresa_id=current_user.empresa_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Tipo de documento no encontrado en esta empresa.")

    if isinstance(result, str):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=result)

    return {"detail": "Tipo de documento eliminado exitosamente."}