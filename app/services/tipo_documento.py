from sqlalchemy.orm import Session
from typing import List
from fastapi import HTTPException, status

# Tus importaciones de modelos y schemas
from ..models import tipo_documento as models
from ..schemas import tipo_documento as schemas
from ..models.documento import Documento
from ..models.plantilla_maestra import PlantillaMaestra

def _validar_cuentas_existentes(db: Session, tipo_documento: schemas.TipoDocumentoCreate | schemas.TipoDocumentoUpdate):
    from .plan_cuenta import get_cuenta
    cuenta_ids = [
        tipo_documento.cuenta_debito_cxc_id,
        tipo_documento.cuenta_credito_cxc_id,
        tipo_documento.cuenta_debito_cxp_id,
        tipo_documento.cuenta_credito_cxp_id
    ]
    for cuenta_id in cuenta_ids:
        if cuenta_id and not get_cuenta(db, cuenta_id=cuenta_id, empresa_id=tipo_documento.empresa_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"La cuenta con ID {cuenta_id} no fue encontrada en el plan de cuentas de la empresa."
            )

def get_tipo_documento(db: Session, tipo_documento_id: int):
    return db.query(models.TipoDocumento).filter(models.TipoDocumento.id == tipo_documento_id).first()

def get_tipo_documento_by_codigo(db: Session, codigo: str, empresa_id: int):
    return db.query(models.TipoDocumento).filter(
        models.TipoDocumento.codigo == codigo,
        models.TipoDocumento.empresa_id == empresa_id
    ).first()

# ##################################################################
# ########### INICIO DE LA CORRECCIÓN DEFINITIVA ###########
# ##################################################################
def get_tipos_documento(db: Session, empresa_id: int, skip: int = 0, limit: int = 100):
    """
    [CORRECCIÓN DE NOMENCLATURA] Obtiene una lista COMPLETA de tipos de documento para una empresa.
    Esta función fue renombrada a la versión corta 'get_tipos_documento' para estandarización.
    """
    return db.query(models.TipoDocumento).filter(
        models.TipoDocumento.empresa_id == empresa_id
    ).order_by(models.TipoDocumento.nombre).offset(skip).limit(limit).all()
# ##################################################################
# ########### FIN DE LA CORRECCIÓN DEFINITIVA ###########
# ##################################################################

def create_tipo_documento(db: Session, tipo_documento: schemas.TipoDocumentoCreate, user_id: int):
    _validar_cuentas_existentes(db, tipo_documento)
    
    # Auto-completar flags críticos. Prioridad 1: Función Especial (dropdown UI). Prioridad 2: Código clásico.
    datos = tipo_documento.model_dump()
    cod_upper = datos.get('codigo', '').upper()
    func_esp = (datos.get('funcion_especial') or '').lower()
    
    # 1. Evaluación estricta por función elegida en el UI
    if func_esp in ('cxp_proveedor', 'documento_soporte', 'pago_proveedor'):
        datos['es_compra'] = True
    elif func_esp in ('cartera_cliente', 'rc_cliente', 'factura_venta'):
        datos['es_venta'] = True
    else:
        # 2. Fallback heurístico si no eligieron función especial
        if cod_upper in ('FC', 'OC', 'RC', 'REC', 'NCC', 'DVC', 'DEVP') and not datos.get('es_compra'):
            datos['es_compra'] = True
        if cod_upper in ('FV', 'FE', 'NCV', 'NDV', 'REM', 'COT') and not datos.get('es_venta'):
            datos['es_venta'] = True
        
    db_tipo_documento = models.TipoDocumento(
        **datos,
        created_by=user_id,
        updated_by=user_id
    )
    db.add(db_tipo_documento)
    db.commit()
    db.refresh(db_tipo_documento)
    return db_tipo_documento

def update_tipo_documento(db: Session, tipo_documento_id: int, tipo_documento: schemas.TipoDocumentoUpdate, user_id: int):
    db_tipo_doc = get_tipo_documento(db, tipo_documento_id)
    if not db_tipo_doc:
        return None
    
    update_data = tipo_documento.model_dump(exclude_unset=True)
    # Para validar, necesitamos una estructura completa, así que combinamos los datos existentes con los nuevos.
    datos_completos_para_validacion = schemas.TipoDocumentoCreate(
        **(db_tipo_doc.__dict__ | update_data)
    )
    _validar_cuentas_existentes(db, datos_completos_para_validacion)
    
    for key, value in update_data.items():
        setattr(db_tipo_doc, key, value)
        
    # Auto-completar flags críticos tras la actualización. Prioridad 1: Función Especial. Prioridad 2: Código.
    cod_upper = (db_tipo_doc.codigo or '').upper()
    func_esp = (db_tipo_doc.funcion_especial or '').lower()
    
    if func_esp in ('cxp_proveedor', 'documento_soporte', 'pago_proveedor'):
        db_tipo_doc.es_compra = True
    elif func_esp in ('cartera_cliente', 'rc_cliente', 'factura_venta'):
        db_tipo_doc.es_venta = True
    else:
        if cod_upper in ('FC', 'OC', 'RC', 'REC', 'NCC', 'DVC', 'DEVP'):
            db_tipo_doc.es_compra = True
        if cod_upper in ('FV', 'FE', 'NCV', 'NDV', 'REM', 'COT'):
            db_tipo_doc.es_venta = True
    
    db_tipo_doc.updated_by = user_id
    db.add(db_tipo_doc)
    db.commit()
    db.refresh(db_tipo_doc)
    return db_tipo_doc

def get_siguiente_numero_documento(db: Session, tipo_documento_id: int):
    tipo_doc = db.query(models.TipoDocumento.consecutivo_actual, models.TipoDocumento.numeracion_manual).filter(models.TipoDocumento.id == tipo_documento_id).first()
    if not tipo_doc:
        return None
    
    siguiente = (tipo_doc.consecutivo_actual or 0) + 1
    return schemas.SiguienteNumero(
        siguiente_numero=siguiente,
        es_manual=tipo_doc.numeracion_manual
    )

def delete_tipo_documento(db: Session, tipo_documento_id: int, empresa_id: int):
    has_docs = db.query(Documento).filter(Documento.tipo_documento_id == tipo_documento_id).first()
    if has_docs:
        return "Este tipo de documento no se puede eliminar porque está siendo utilizado por documentos existentes."
    
    has_templates = db.query(PlantillaMaestra).filter(PlantillaMaestra.tipo_documento_id_sugerido == tipo_documento_id).first()
    if has_templates:
        return "Este tipo de documento no se puede eliminar porque está siendo utilizado por plantillas."
    
    db_tipo_doc = db.query(models.TipoDocumento).filter(
        models.TipoDocumento.id == tipo_documento_id,
        models.TipoDocumento.empresa_id == empresa_id
    ).first()
    
    if not db_tipo_doc:
        return None
    
    db.delete(db_tipo_doc)
    db.commit()
    return True