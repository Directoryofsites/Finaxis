from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.usuario import User as UserSchema
from app.schemas.import_template import ImportTemplateCreate, ImportTemplateResponse, ImportTemplateUpdate
from app.services import import_template_service

router = APIRouter()

@router.get("/", response_model=List[ImportTemplateResponse])
def read_templates(
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user)
):
    return import_template_service.get_templates(db, current_user.empresa_id)

@router.post("/", response_model=ImportTemplateResponse)
def create_template(
    template: ImportTemplateCreate,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user)
):
    return import_template_service.create_template(db, template, current_user.empresa_id)

@router.put("/{template_id}", response_model=ImportTemplateResponse)
def update_template(
    template_id: int,
    template: ImportTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user)
):
    updated = import_template_service.update_template(db, template_id, template, current_user.empresa_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return updated

@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user)
):
    success = import_template_service.delete_template(db, template_id, current_user.empresa_id)
    if not success:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return None

from fastapi import File, UploadFile
from app.services.universal_import_service import UniversalImportService

@router.post("/preview-headers", response_model=List[str])
async def preview_headers(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user)
):
    """
    Recibe un archivo (Excel/CSV) y devuelve la lista de encabezados encontrados.
    Usado para la UI de mapeo de plantillas.
    """
    content = await file.read()
    headers = UniversalImportService.get_headers(content)
    if not headers:
        raise HTTPException(status_code=400, detail="No se pudieron leer encabezados del archivo.")
    return headers
