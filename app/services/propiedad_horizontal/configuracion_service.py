from sqlalchemy.orm import Session
from app.models.propiedad_horizontal import PHConfiguracion, PHConcepto
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
    
    db.commit()
    db.refresh(config)
    return config

# --- CONCEPTOS ---
def get_conceptos(db: Session, empresa_id: int):
    return db.query(PHConcepto).filter(PHConcepto.empresa_id == empresa_id).all()

def crear_concepto(db: Session, concepto: schemas.PHConceptoCreate, empresa_id: int):
    db_concepto = PHConcepto(
        empresa_id=empresa_id,
        nombre=concepto.nombre,
        codigo_contable=concepto.codigo_contable,
        tipo_calculo=concepto.tipo_calculo,
        valor_defecto=concepto.valor_defecto,
        activo=concepto.activo,
        # Facturación
        tipo_documento_id=concepto.tipo_documento_id,
        cuenta_cartera_id=concepto.cuenta_cartera_id,
        # Recaudo
        tipo_documento_recibo_id=concepto.tipo_documento_recibo_id,
        cuenta_caja_id=concepto.cuenta_caja_id
    )
    db.add(db_concepto)
    db.commit()
    db.refresh(db_concepto)
    return db_concepto

def update_concepto(db: Session, concepto_id: int, concepto_update: schemas.PHConceptoUpdate, empresa_id: int):
    db_concepto = db.query(PHConcepto).filter(PHConcepto.id == concepto_id, PHConcepto.empresa_id == empresa_id).first()
    if not db_concepto:
        return None
        
    if concepto_update.nombre is not None: db_concepto.nombre = concepto_update.nombre
    if concepto_update.codigo_contable is not None: db_concepto.codigo_contable = concepto_update.codigo_contable
    if concepto_update.tipo_calculo is not None: db_concepto.tipo_calculo = concepto_update.tipo_calculo
    if concepto_update.valor_defecto is not None: db_concepto.valor_defecto = concepto_update.valor_defecto
    if concepto_update.activo is not None: db_concepto.activo = concepto_update.activo
    
    # Update Nullable specific fields (Check if they are in the update payload - Pydantic exclude_unset=True in frontend call? 
    # Or just update always? If we use None as "No Change", we can't un-set.
    # Hack: Assume if key is present in update we use it. But here we access attribute.
    # For now, let's allow updating if value is passed. To clear, frontend might need to pass explicit null?
    # Pydantic schema: Optional[int] = None. 
    # Let's just update them. 
    if concepto_update.tipo_documento_id is not None: db_concepto.tipo_documento_id = concepto_update.tipo_documento_id
    if concepto_update.cuenta_cartera_id is not None: db_concepto.cuenta_cartera_id = concepto_update.cuenta_cartera_id
    if concepto_update.tipo_documento_recibo_id is not None: db_concepto.tipo_documento_recibo_id = concepto_update.tipo_documento_recibo_id
    if concepto_update.cuenta_caja_id is not None: db_concepto.cuenta_caja_id = concepto_update.cuenta_caja_id
    
    db.commit()
    db.refresh(db_concepto)
    return db_concepto

def delete_concepto(db: Session, concepto_id: int, empresa_id: int):
    db_concepto = db.query(PHConcepto).filter(PHConcepto.id == concepto_id, PHConcepto.empresa_id == empresa_id).first()
    if not db_concepto:
        return False
    db.delete(db_concepto)
    db.commit()
    return True
