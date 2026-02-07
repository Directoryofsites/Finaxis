
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.services.factura_electronica_service import factura_electronica_service
from app.models.documento import Documento
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class EmisionResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    cufe: Optional[str] = None
    xml_url: Optional[str] = None
    error: Optional[str] = None

@router.post("/emitir/{documento_id}", response_model=EmisionResponse)
def emitir_factura_electronica(
    documento_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Intenta emitir una factura electrónica.
    Valida datos -> Mapea JSON -> Envía a Proveedor (Mock/Real).
    """
    # Verificar permisos (Opcional: Agregar Rol.ADMIN o CONTADOR)
    
    # Verificar propiedad
    doc = db.query(Documento).get(documento_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
        
    # Verificar Consistencia
    if doc.dian_estado == 'ACEPTADO':
         return {
            "success": True, 
            "message": "Este documento ya fue emitido previamente.",
            "cufe": doc.dian_cufe,
            "xml_url": doc.dian_xml_url
        }

    # Ejecutar Servicio
    resultado = factura_electronica_service.emitir_factura(db, documento_id, current_user.id)
    
    return resultado

@router.get("/status/{documento_id}")
def consultar_estado_dian(
    documento_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    doc = db.query(Documento).get(documento_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
        
    return {
        "estado": doc.dian_estado, # NULL, PENDIENTE, ENVIADO, ACEPTADO, ERROR
        "cufe": doc.dian_cufe,
        "xml_url": doc.dian_xml_url,
        "error": doc.dian_error
    }
