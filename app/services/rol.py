from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import permiso as models
from app.schemas import permiso as schemas

# --- PERMISOS ---
def get_all_permisos(db: Session) -> List[models.Permiso]:
    """Retorna todos los permisos disponibles en el sistema."""
    return db.query(models.Permiso).all()

# --- ROLES ---
def get_roles_by_empresa(db: Session, empresa_id: int) -> List[models.Rol]:
    """
    Retorna roles globales (empresa_id IS NULL) Y roles de la empresa dada.
    """
    return db.query(models.Rol).filter(
        or_(
            models.Rol.empresa_id == None,
            models.Rol.empresa_id == empresa_id
        )
    ).all()

def get_rol_by_id(db: Session, rol_id: int) -> Optional[models.Rol]:
    return db.query(models.Rol).filter(models.Rol.id == rol_id).first()

def create_rol(db: Session, rol_data: schemas.RolCreate, empresa_id: int) -> models.Rol:
    """Crea un rol personalizado para una empresa."""
    db_rol = models.Rol(
        nombre=rol_data.nombre,
        descripcion=rol_data.descripcion,
        empresa_id=empresa_id
    )
    
    # Asignar permisos
    if rol_data.permisos_ids:
        permisos = db.query(models.Permiso).filter(models.Permiso.id.in_(rol_data.permisos_ids)).all()
        db_rol.permisos = permisos
        
    db.add(db_rol)
    db.commit()
    db.refresh(db_rol)
    return db_rol

def update_rol(db: Session, rol: models.Rol, rol_update: schemas.RolUpdate) -> models.Rol:
    """Actualiza un rol existente."""
    if rol_update.nombre is not None:
        rol.nombre = rol_update.nombre
    if rol_update.descripcion is not None:
        rol.descripcion = rol_update.descripcion
        
    if rol_update.permisos_ids is not None:
        permisos = db.query(models.Permiso).filter(models.Permiso.id.in_(rol_update.permisos_ids)).all()
        rol.permisos = permisos
        
    db.commit()
    db.refresh(rol)
    return rol

def delete_rol(db: Session, rol: models.Rol):
    """Elimina un rol."""
    # SQLAlchemy maneja la eliminación de la tabla de asociación automáticamente si está configurado cascade,
    # pero por defecto 'secondary' no hace cascade delete. 
    # Sin embargo, simplemente quitando el rol, la asociación desaparece.
    db.delete(rol)
    db.commit()
