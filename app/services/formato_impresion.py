from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import Optional

from ..models import formato_impresion as models
from ..schemas import formato_impresion as schemas

def get_formato_by_id(db: Session, formato_id: int, empresa_id: int):
    """Obtiene una plantilla de impresión por su ID."""
    return db.query(models.FormatoImpresion).filter(
        models.FormatoImpresion.id == formato_id,
        models.FormatoImpresion.empresa_id == empresa_id
    ).first()

def get_formatos_by_empresa(db: Session, empresa_id: int, tipo_documento_id: Optional[int] = None):
    """
    Obtiene todas las plantillas de impresión de una empresa.
    Opcionalmente, filtra por un tipo de documento específico.
    """
    query = db.query(models.FormatoImpresion).filter(
        models.FormatoImpresion.empresa_id == empresa_id
    )

    # Si se proporciona un tipo_documento_id, añadimos el filtro a la consulta.
    if tipo_documento_id is not None:
        query = query.filter(models.FormatoImpresion.tipo_documento_id == tipo_documento_id)

    return query.order_by(models.FormatoImpresion.nombre).all()

def create_formato(db: Session, formato: schemas.FormatoImpresionCreate, user_id: int):
    """Crea una nueva plantilla de impresión."""
    db_formato = models.FormatoImpresion(
        **formato.model_dump(),
        creado_por_usuario_id=user_id
    )
    db.add(db_formato)
    db.commit()
    db.refresh(db_formato)
    return db_formato

def update_formato(db: Session, formato_id: int, formato_update: schemas.FormatoImpresionUpdate, empresa_id: int):
    """Actualiza una plantilla de impresión existente."""
    db_formato = get_formato_by_id(db, formato_id=formato_id, empresa_id=empresa_id)
    if not db_formato:
        return None

    update_data = formato_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_formato, key, value)

    db.commit()
    db.refresh(db_formato)
    return db_formato

def delete_formato(db: Session, formato_id: int, empresa_id: int):
    """Elimina una plantilla de impresión."""
    db_formato = get_formato_by_id(db, formato_id=formato_id, empresa_id=empresa_id)
    if not db_formato:
        return None

    db.delete(db_formato)
    db.commit()
    return db_formato