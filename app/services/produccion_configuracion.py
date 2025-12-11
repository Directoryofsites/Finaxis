from sqlalchemy.orm import Session
from app.models.configuracion_produccion import ConfiguracionProduccion
from app.schemas.produccion import ConfigProduccionCreate

def get_configuracion(db: Session, empresa_id: int):
    return db.query(ConfiguracionProduccion).filter(ConfiguracionProduccion.empresa_id == empresa_id).first()

def save_configuracion(db: Session, config_data: ConfigProduccionCreate, empresa_id: int):
    db_config = get_configuracion(db, empresa_id)
    if not db_config:
        db_config = ConfiguracionProduccion(empresa_id=empresa_id)
        db.add(db_config)
    
    if config_data.tipo_documento_orden_id is not None:
        db_config.tipo_documento_orden_id = config_data.tipo_documento_orden_id
    if config_data.tipo_documento_anulacion_id is not None:
        db_config.tipo_documento_anulacion_id = config_data.tipo_documento_anulacion_id
    if config_data.tipo_documento_consumo_id is not None:
        db_config.tipo_documento_consumo_id = config_data.tipo_documento_consumo_id
    if config_data.tipo_documento_entrada_pt_id is not None:
        db_config.tipo_documento_entrada_pt_id = config_data.tipo_documento_entrada_pt_id
    
    db.commit()
    db.refresh(db_config)
    return db_config
