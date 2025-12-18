from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.propiedad_horizontal.modulo_contribucion import PHModuloContribucion
from app.schemas.propiedad_horizontal.modulo_contribucion import PHModuloContribucionCreate, PHModuloContribucionUpdate

def get_modulos(db: Session, empresa_id: int):
    return db.query(PHModuloContribucion).filter(PHModuloContribucion.empresa_id == empresa_id).all()

def create_modulo(db: Session, modulo: PHModuloContribucionCreate, empresa_id: int):
    db_modulo = PHModuloContribucion(**modulo.dict(), empresa_id=empresa_id)
    db.add(db_modulo)
    db.commit()
    db.refresh(db_modulo)
    return db_modulo

def update_modulo(db: Session, modulo_id: int, modulo_update: PHModuloContribucionUpdate, empresa_id: int):
    db_modulo = db.query(PHModuloContribucion).filter(PHModuloContribucion.id == modulo_id, PHModuloContribucion.empresa_id == empresa_id).first()
    if not db_modulo:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")
    
    for key, value in modulo_update.dict(exclude_unset=True).items():
        setattr(db_modulo, key, value)
    
    db.commit()
    db.refresh(db_modulo)
    return db_modulo

def delete_modulo(db: Session, modulo_id: int, empresa_id: int):
    db_modulo = db.query(PHModuloContribucion).filter(PHModuloContribucion.id == modulo_id, PHModuloContribucion.empresa_id == empresa_id).first()
    if not db_modulo:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")
    
    db.delete(db_modulo)
    db.commit()
    return {"message": "Módulo eliminado exitosamente"}
