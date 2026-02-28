from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from ...core.database import get_db
from ...core.security import get_current_user
from ...models.usuario import Usuario
from ...services.buzon_tributario_service import procesar_buzon
from ...models.empresa_config_buzon import EmpresaConfigBuzon
from ...schemas.empresa_config_buzon import BuzonConfigDTO, EmpresaConfigBuzonCreate, EmpresaConfigBuzonResponse

router = APIRouter()

class BuzonTributarioRequest(BaseModel):
    email_addr: Optional[str] = None
    password_app: Optional[str] = None
    tipo_documento_id: Optional[int] = None
    cuenta_gasto_id: Optional[int] = None
    cuenta_caja_id: Optional[int] = None

@router.post("/sincronizar")
def sincronizar_buzon(
    request: BuzonTributarioRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lee la bandeja de entrada, busca XML de factura electrónica 
    y genera asientos contables de compra automáticamente.
    """
    try:
        # Resolvemos los parámetros (del Request, o de la BD)
        config = db.query(EmpresaConfigBuzon).filter(EmpresaConfigBuzon.empresa_id == current_user.empresa_id).first()
        
        email_addr = request.email_addr or (config.email_addr if config else None)
        password_app = request.password_app or (config.password_app if config else None)
        tipo_documento_id = request.tipo_documento_id or (config.tipo_documento_id if config else None)
        cuenta_gasto_id = request.cuenta_gasto_id or (config.cuenta_gasto_id if config else None)
        cuenta_caja_id = request.cuenta_caja_id or (config.cuenta_caja_id if config else None)
        
        # Validaciones
        if not email_addr or not password_app:
            raise HTTPException(status_code=400, detail="Faltan credenciales del correo. Revise la configuración.")
        if not tipo_documento_id or not cuenta_gasto_id or not cuenta_caja_id:
            raise HTTPException(status_code=400, detail="Faltan parámetros contables. Revise la configuración.")
            
        resultado = procesar_buzon(
            db=db,
            empresa_id=current_user.empresa_id,
            user_id=current_user.id,
            email_addr=email_addr,
            password=password_app,
            tipo_documento_id=tipo_documento_id,
            cuenta_gasto_id=cuenta_gasto_id,
            cuenta_caja_id=cuenta_caja_id
        )
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config", response_model=BuzonConfigDTO)
def obtener_configuracion_buzon(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene la configuración actual del buzón tributario de la empresa.
    """
    config = db.query(EmpresaConfigBuzon).filter(EmpresaConfigBuzon.empresa_id == current_user.empresa_id).first()
    if not config:
        return BuzonConfigDTO()
    
    masked_pw = "********" if config.password_app else None
    
    return BuzonConfigDTO(
        email_addr=config.email_addr,
        password_app_masked=masked_pw,
        tipo_documento_id=config.tipo_documento_id,
        cuenta_gasto_id=config.cuenta_gasto_id,
        cuenta_caja_id=config.cuenta_caja_id,
        is_active=config.is_active
    )

@router.post("/config", response_model=EmpresaConfigBuzonResponse)
def guardar_configuracion_buzon(
    config_in: EmpresaConfigBuzonCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crea o actualiza la configuración del buzón tributario de la empresa.
    """
    config = db.query(EmpresaConfigBuzon).filter(EmpresaConfigBuzon.empresa_id == current_user.empresa_id).first()
    
    if config:
        # Update
        if config_in.email_addr is not None: config.email_addr = config_in.email_addr
        # Solo actualizamos la contraseña si nos envían una nueva que no sea asteriscos o vacía
        if config_in.password_app and config_in.password_app != "********":
            config.password_app = config_in.password_app
        
        if config_in.tipo_documento_id is not None: config.tipo_documento_id = config_in.tipo_documento_id
        if config_in.cuenta_gasto_id is not None: config.cuenta_gasto_id = config_in.cuenta_gasto_id
        if config_in.cuenta_caja_id is not None: config.cuenta_caja_id = config_in.cuenta_caja_id
        if config_in.is_active is not None: config.is_active = config_in.is_active
    else:
        # Create
        config = EmpresaConfigBuzon(
            empresa_id=current_user.empresa_id,
            email_addr=config_in.email_addr,
            password_app=config_in.password_app,
            tipo_documento_id=config_in.tipo_documento_id,
            cuenta_gasto_id=config_in.cuenta_gasto_id,
            cuenta_caja_id=config_in.cuenta_caja_id,
            is_active=config_in.is_active
        )
        db.add(config)
        
    db.commit()
    db.refresh(config)
    return config

