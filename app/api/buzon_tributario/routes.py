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
    # Estos campos ya no se usarían tanto individualmente si usamos la config de la BD,
    # pero los mantenemos o los expandimos si se requiere sobrescribir manualmente.
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
    Lee la bandeja de entrada, busca XML y genera asientos contables 
    automáticamente (Compras, Ventas o Soporte).
    """
    try:
        config = db.query(EmpresaConfigBuzon).filter(EmpresaConfigBuzon.empresa_id == current_user.empresa_id).first()
        
        email_addr = request.email_addr or (config.email_addr if config else None)
        password_app = request.password_app or (config.password_app if config else None)
        
        # Validaciones básicas
        if not email_addr or not password_app:
            raise HTTPException(status_code=400, detail="Faltan credenciales del correo. Revise la configuración.")
        
        if not config:
             raise HTTPException(status_code=400, detail="Debe configurar los parámetros contables primero.")

        resultado = procesar_buzon(
            db=db,
            empresa_id=current_user.empresa_id,
            user_id=current_user.id,
            email_addr=email_addr,
            password=password_app,
            config=config # Pasamos el objeto de configuración completo
        )
        return resultado
    except Exception as e:
        import traceback
        traceback.print_exc()
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
        # Compras
        tipo_documento_id=config.tipo_documento_id,
        cuenta_gasto_id=config.cuenta_gasto_id,
        cuenta_caja_id=config.cuenta_caja_id,
        # Ventas
        venta_tipo_documento_id=config.venta_tipo_documento_id,
        venta_cuenta_ingreso_id=config.venta_cuenta_ingreso_id,
        venta_cuenta_caja_id=config.venta_cuenta_caja_id,
        # Soporte
        soporte_tipo_documento_id=config.soporte_tipo_documento_id,
        soporte_cuenta_gasto_id=config.soporte_cuenta_gasto_id,
        soporte_cuenta_caja_id=config.soporte_cuenta_caja_id,
        
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
        if config_in.password_app and config_in.password_app != "********":
            config.password_app = config_in.password_app
        
        # Compras
        if config_in.tipo_documento_id is not None: config.tipo_documento_id = config_in.tipo_documento_id
        if config_in.cuenta_gasto_id is not None: config.cuenta_gasto_id = config_in.cuenta_gasto_id
        if config_in.cuenta_caja_id is not None: config.cuenta_caja_id = config_in.cuenta_caja_id
        
        # Ventas
        if config_in.venta_tipo_documento_id is not None: config.venta_tipo_documento_id = config_in.venta_tipo_documento_id
        if config_in.venta_cuenta_ingreso_id is not None: config.venta_cuenta_ingreso_id = config_in.venta_cuenta_ingreso_id
        if config_in.venta_cuenta_caja_id is not None: config.venta_cuenta_caja_id = config_in.venta_cuenta_caja_id
        
        # Soporte
        if config_in.soporte_tipo_documento_id is not None: config.soporte_tipo_documento_id = config_in.soporte_tipo_documento_id
        if config_in.soporte_cuenta_gasto_id is not None: config.soporte_cuenta_gasto_id = config_in.soporte_cuenta_gasto_id
        if config_in.soporte_cuenta_caja_id is not None: config.soporte_cuenta_caja_id = config_in.soporte_cuenta_caja_id
        
        if config_in.is_active is not None: config.is_active = config_in.is_active
    else:
        # Create
        config = EmpresaConfigBuzon(
            empresa_id=current_user.empresa_id,
            email_addr=config_in.email_addr,
            password_app=config_in.password_app,
            # Compras
            tipo_documento_id=config_in.tipo_documento_id,
            cuenta_gasto_id=config_in.cuenta_gasto_id,
            cuenta_caja_id=config_in.cuenta_caja_id,
            # Ventas
            venta_tipo_documento_id=config_in.venta_tipo_documento_id,
            venta_cuenta_ingreso_id=config_in.venta_cuenta_ingreso_id,
            venta_cuenta_caja_id=config_in.venta_cuenta_caja_id,
            # Soporte
            soporte_tipo_documento_id=config_in.soporte_tipo_documento_id,
            soporte_cuenta_gasto_id=config_in.soporte_cuenta_gasto_id,
            soporte_cuenta_caja_id=config_in.soporte_cuenta_caja_id,
            
            is_active=config_in.is_active
        )
        db.add(config)
        
    db.commit()
    db.refresh(config)
    return config

