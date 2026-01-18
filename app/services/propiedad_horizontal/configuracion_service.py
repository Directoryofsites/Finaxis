from sqlalchemy.orm import Session
from app.models.propiedad_horizontal import PHConfiguracion
from app.schemas.propiedad_horizontal import configuracion as schemas
from typing import List, Optional

# --- CONFIGURACION ---
def get_configuracion(db: Session, empresa_id: int):
    config = db.query(PHConfiguracion).filter(PHConfiguracion.empresa_id == empresa_id).first()
    if not config:
        # Auto-create default configuration if not exists
        config = PHConfiguracion(empresa_id=empresa_id)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

def update_configuracion(db: Session, empresa_id: int, config_update: schemas.PHConfiguracionUpdate):
    config = get_configuracion(db, empresa_id)
    
    config.interes_mora_mensual = config_update.interes_mora_mensual
    config.dia_corte = config_update.dia_corte
    config.dia_limite_pago = config_update.dia_limite_pago
    config.dia_limite_pronto_pago = config_update.dia_limite_pronto_pago
    config.descuento_pronto_pago = config_update.descuento_pronto_pago
    config.mensaje_factura = config_update.mensaje_factura
    config.tipo_documento_factura_id = config_update.tipo_documento_factura_id
    config.tipo_documento_recibo_id = config_update.tipo_documento_recibo_id
    config.tipo_documento_mora_id = config_update.tipo_documento_mora_id # Nuevo
    config.cuenta_ingreso_intereses_id = config_update.cuenta_ingreso_intereses_id
    config.cuenta_cartera_id = config_update.cuenta_cartera_id
    config.cuenta_caja_id = config_update.cuenta_caja_id
    config.interes_mora_habilitado = config_update.interes_mora_habilitado
    config.tipo_negocio = config_update.tipo_negocio # Nueva asignacion
    
    db.commit()
    db.refresh(config)
    return config


