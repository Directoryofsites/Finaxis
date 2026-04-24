from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
from app.models.propiedad_horizontal import PHConfiguracion
from app.schemas.propiedad_horizontal import configuracion as schemas
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

# --- CONFIGURACION ---
def get_configuracion(db: Session, empresa_id: int):
    try:
        config = (
            db.query(PHConfiguracion)
            .options(
                joinedload(PHConfiguracion.tipo_documento_factura),
                joinedload(PHConfiguracion.tipo_documento_recibo),
                joinedload(PHConfiguracion.tipo_documento_mora),
                joinedload(PHConfiguracion.tipo_documento_cruce),
                joinedload(PHConfiguracion.cuenta_cartera),
                joinedload(PHConfiguracion.cuenta_caja),
                joinedload(PHConfiguracion.cuenta_ingreso_intereses),
                joinedload(PHConfiguracion.cuenta_anticipos),
                joinedload(PHConfiguracion.cuenta_descuento),
            )
            .filter(PHConfiguracion.empresa_id == empresa_id)
            .first()
        )
    except Exception as e:
        # Column missing in DB (migration pending) — fallback to raw query with only safe columns
        logger.error(f"get_configuracion ORM error (likely missing column): {e}")
        db.rollback()
        try:
            _ensure_configuracion_columns(db)
        except Exception as me:
            logger.error(f"Auto-fix migration failed: {me}")
            db.rollback()
        # Re-try with minimal select
        try:
            config = (
                db.query(PHConfiguracion)
                .filter(PHConfiguracion.empresa_id == empresa_id)
                .first()
            )
        except Exception:
            db.rollback()
            config = None

    if not config:
        # Auto-create default configuration if not exists
        config = PHConfiguracion(empresa_id=empresa_id)
        db.add(config)
        try:
            db.commit()
            db.refresh(config)
        except Exception as ce:
            logger.error(f"Error creando config por defecto: {ce}")
            db.rollback()
    return config

def _ensure_configuracion_columns(db: Session):
    """Emergency migration: add any missing columns to ph_configuracion."""
    cols_to_add = [
        ("cuenta_anticipos_id", "INTEGER"),
        ("tipo_documento_cruce_id", "INTEGER"),
        ("cuenta_descuento_id", "INTEGER"),
        ("tipo_documento_mora_id", "INTEGER"),
        ("tipo_negocio", "VARCHAR(50) DEFAULT 'PH_RESIDENCIAL'"),
        ("interes_mora_habilitado", "BOOLEAN DEFAULT TRUE"),
        ("descuento_pronto_pago_habilitado", "BOOLEAN DEFAULT TRUE"),
    ]
    for col, col_type in cols_to_add:
        try:
            db.execute(text(f"ALTER TABLE ph_configuracion ADD COLUMN IF NOT EXISTS {col} {col_type}"))
            db.commit()
            logger.info(f"Emergency migration: added {col} to ph_configuracion")
        except Exception as e:
            db.rollback()
            logger.warning(f"Emergency migration skip {col}: {e}")

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
    config.tipo_documento_cruce_id = config_update.tipo_documento_cruce_id # Cruce Anticipos
    config.cuenta_ingreso_intereses_id = config_update.cuenta_ingreso_intereses_id
    config.cuenta_cartera_id = config_update.cuenta_cartera_id
    config.cuenta_caja_id = config_update.cuenta_caja_id
    config.cuenta_anticipos_id = config_update.cuenta_anticipos_id # Pasivo 2805
    config.cuenta_descuento_id = config_update.cuenta_descuento_id # Menor valor 4175
    config.interes_mora_habilitado = config_update.interes_mora_habilitado
    config.descuento_pronto_pago_habilitado = config_update.descuento_pronto_pago_habilitado
    config.tipo_negocio = config_update.tipo_negocio # Nueva asignacion
    
    db.commit()
    db.refresh(config)
    return config


