
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.services.factura_electronica_service import factura_electronica_service
from app.models.documento import Documento
from app.schemas.configuracion_fe import ConfiguracionFEResponse, ConfiguracionFEUpdate
from app.models.configuracion_fe import ConfiguracionFE
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
    # --- HOTFIX: Asegurar que los rangos existan para Sandbox si faltan ---
    try:
        config = db.query(ConfiguracionFE).filter_by(empresa_id=doc.empresa_id).first()
        if config and config.ambiente == 'PRUEBAS':
             updated = False
             if not config.nc_rango_id: 
                 config.nc_rango_id = 9; updated = True
             if not config.nd_rango_id: 
                 config.nd_rango_id = 9; updated = True
             if not config.ds_rango_id: 
                 config.ds_rango_id = 148; updated = True
             if not config.factura_rango_id:
                 config.factura_rango_id = 8; updated = True
                 
             if updated:
                 db.commit()
                 db.refresh(config)
                 print(f"HOTFIX: Rangos actualizados automáticamente para empresa {doc.empresa_id}")
    except Exception as e:
        print(f"Advertencia en Hotfix Rangos: {e}")
    # -----------------------------------------------------------------------

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

@router.get("/config/{empresa_id}", response_model=ConfiguracionFEResponse)
def get_fe_config(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Validación de permiso simple (mismo que emitir)
    if current_user.empresa_id != empresa_id and not any(r.nombre == 'soporte' for r in current_user.roles):
        raise HTTPException(status_code=403, detail="No tienes permisos para ver esta configuración")

    config = db.query(ConfiguracionFE).filter(ConfiguracionFE.empresa_id == empresa_id).first()
    if not config:
        # Si no existe, devolvemos una vacía o 404. 
        # Dado que el seeder la crea, debería existir.
        raise HTTPException(status_code=404, detail="Configuración FE no encontrada para esta empresa")
    
    return config

@router.put("/config/{empresa_id}", response_model=ConfiguracionFEResponse)
def update_fe_config(
    empresa_id: int,
    config_in: ConfiguracionFEUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.empresa_id != empresa_id and not any(r.nombre == 'soporte' for r in current_user.roles):
        raise HTTPException(status_code=403, detail="No tienes permisos para modificar esta configuración")

    config = db.query(ConfiguracionFE).filter(ConfiguracionFE.empresa_id == empresa_id).first()
    if not config:
        config = ConfiguracionFE(empresa_id=empresa_id)
        db.add(config)

    for field, value in config_in.model_dump(exclude_unset=True).items():
        setattr(config, field, value)

    db.commit()
    db.refresh(config)
    return config
