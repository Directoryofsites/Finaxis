from sqlalchemy.orm import Session
from app.models.import_template import ImportTemplate
from app.schemas.import_template import ImportTemplateCreate, ImportTemplateUpdate
from typing import List, Optional

def get_templates(db: Session, empresa_id: int) -> List[ImportTemplate]:
    return db.query(ImportTemplate).filter(ImportTemplate.empresa_id == empresa_id).all()

def get_template(db: Session, template_id: int, empresa_id: int) -> Optional[ImportTemplate]:
    return db.query(ImportTemplate).filter(
        ImportTemplate.id == template_id, 
        ImportTemplate.empresa_id == empresa_id
    ).first()

def create_template(db: Session, template: ImportTemplateCreate, empresa_id: int) -> ImportTemplate:
    db_obj = ImportTemplate(
        empresa_id=empresa_id,
        nombre=template.nombre,
        descripcion=template.descripcion,
        mapping_config=template.mapping_config
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_template(db: Session, template_id: int, template: ImportTemplateUpdate, empresa_id: int) -> Optional[ImportTemplate]:
    db_obj = get_template(db, template_id, empresa_id)
    if not db_obj:
        return None
    
    update_data = template.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_obj, key, value)
        
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_template(db: Session, template_id: int, empresa_id: int) -> bool:
    db_obj = get_template(db, template_id, empresa_id)
    if not db_obj:
        return False
        
    db.delete(db_obj)
    db.commit()
    return True
