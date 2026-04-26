from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from app.models.propiedad_horizontal.modulo_contribucion import PHModuloContribucion
from app.models.propiedad_horizontal.unidad import PHTorre
from app.schemas.propiedad_horizontal.modulo_contribucion import PHModuloContribucionCreate, PHModuloContribucionUpdate
from app.utils.sorting import natural_sort_key

def _modulo_to_dict(m):
    """Convierte un PHModuloContribucion a dict incluyendo torres_ids."""
    return {
        "id": m.id,
        "empresa_id": m.empresa_id,
        "nombre": m.nombre,
        "descripcion": m.descripcion,
        "tipo_distribucion": m.tipo_distribucion,
        "torres_ids": [t.id for t in m.torres] if m.torres else []
    }

def get_modulos(db: Session, empresa_id: int):
    modulos = db.query(PHModuloContribucion)\
        .options(joinedload(PHModuloContribucion.torres))\
        .filter(PHModuloContribucion.empresa_id == empresa_id).all()
    
    results = [_modulo_to_dict(m) for m in modulos]
    results.sort(key=lambda x: natural_sort_key(x['nombre']))
    return results

def create_modulo(db: Session, modulo: PHModuloContribucionCreate, empresa_id: int):
    torres_ids = modulo.torres_ids or []
    data = modulo.dict(exclude={"torres_ids"})
    db_modulo = PHModuloContribucion(**data, empresa_id=empresa_id)
    
    if torres_ids:
        torres = db.query(PHTorre).filter(PHTorre.id.in_(torres_ids), PHTorre.empresa_id == empresa_id).all()
        db_modulo.torres = torres
    
    db.add(db_modulo)
    db.commit()
    db.refresh(db_modulo)
    # Recargar con torres
    db.refresh(db_modulo)
    return _modulo_to_dict(db_modulo)

def update_modulo(db: Session, modulo_id: int, modulo_update: PHModuloContribucionUpdate, empresa_id: int):
    db_modulo = db.query(PHModuloContribucion)\
        .options(joinedload(PHModuloContribucion.torres))\
        .filter(PHModuloContribucion.id == modulo_id, PHModuloContribucion.empresa_id == empresa_id).first()
    if not db_modulo:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")
    
    # Actualizar campos básicos
    db_modulo.nombre = modulo_update.nombre
    db_modulo.descripcion = modulo_update.descripcion
    db_modulo.tipo_distribucion = modulo_update.tipo_distribucion
    
    # Actualizar torres asignadas
    torres_ids = modulo_update.torres_ids or []
    if torres_ids:
        torres = db.query(PHTorre).filter(PHTorre.id.in_(torres_ids), PHTorre.empresa_id == empresa_id).all()
        db_modulo.torres = torres
    else:
        db_modulo.torres = []
    
    db.commit()
    db.refresh(db_modulo)
    return _modulo_to_dict(db_modulo)

def delete_modulo(db: Session, modulo_id: int, empresa_id: int):
    db_modulo = db.query(PHModuloContribucion).filter(PHModuloContribucion.id == modulo_id, PHModuloContribucion.empresa_id == empresa_id).first()
    if not db_modulo:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")
    
    db.delete(db_modulo)
    db.commit()
    return {"message": "Módulo eliminado exitosamente"}
