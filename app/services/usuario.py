# app/services/usuario.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from fastapi import HTTPException, status
from typing import List


# --- INICIO: IMPORTACIÓN CORREGIDA ---
# Importamos los MÓDULOS que contienen las clases que necesitamos.
from app.models import (
    usuario as models_usuario, 
    permiso as models_permiso,
    documento as models_doc
)
# --- FIN: IMPORTACIÓN CORREGIDA ---

from app.schemas import usuario as schemas_usuario

from app.core.hashing import get_password_hash

def get_user_by_email(db: Session, email: str):
    return db.query(models_usuario.Usuario).options(
        joinedload(models_usuario.Usuario.roles)
    ).filter(models_usuario.Usuario.email == email).first()

def get_user_by_id(db: Session, usuario_id: int):
    return db.query(models_usuario.Usuario).filter(models_usuario.Usuario.id == usuario_id).first()

def get_users_by_company(db: Session, empresa_id: int):
    return db.query(models_usuario.Usuario).filter(models_usuario.Usuario.empresa_id == empresa_id).all()

def create_user_in_company(db: Session, user_data: schemas_usuario.UserCreateInCompany, empresa_id: int):
    hashed_password = get_password_hash(user_data.password)
    
    roles = db.query(models_permiso.Rol).filter(models_permiso.Rol.id.in_(user_data.roles_ids)).all()
    if len(roles) != len(user_data.roles_ids):
        raise HTTPException(status_code=404, detail="Uno o más roles no fueron encontrados.")

    db_user = models_usuario.Usuario(
        email=user_data.email,
        # --- CORRECCIÓN APLICADA AQUÍ ---
        password_hash=hashed_password,
        nombre_completo=user_data.nombre_completo,
        empresa_id=empresa_id,
        roles=roles
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_password(db: Session, user: models_usuario.Usuario, new_password: str):
    hashed_password = get_password_hash(new_password)
    # --- CORRECCIÓN APLICADA AQUÍ ---
    user.password_hash = hashed_password
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_soporte_users(db: Session) -> List[models_usuario.Usuario]:
    return db.query(models_usuario.Usuario).filter(models_usuario.Usuario.empresa_id == None).all()

def create_soporte_user(db: Session, user_data: schemas_usuario.SoporteUserCreate):
    hashed_password = get_password_hash(user_data.password)
    
    # Asignar rol de soporte por defecto
    soporte_role = db.query(models_permiso.Rol).filter(models_permiso.Rol.nombre == 'soporte').first()
    if not soporte_role:
        raise HTTPException(status_code=500, detail="El rol 'soporte' no está definido en la base de datos.")

    db_user = models_usuario.Usuario(
        email=user_data.email,
        # --- CORRECCIÓN APLICADA AQUÍ ---
        password_hash=hashed_password,
        nombre_completo=user_data.nombre_completo,
        empresa_id=None,
        roles=[soporte_role]
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- INICIO: FUNCIÓN DELETE CON REFERENCIAS CORREGIDAS ---
def delete_usuario(db: Session, usuario_id: int):
    """
    Elimina un usuario de la base de datos, solo si no tiene historial transaccional.
    """
    usuario = db.query(models_usuario.Usuario).filter(models_usuario.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

    # Chequeo de documentos creados
    # Usamos models_doc.Documento porque Documento está DENTRO del módulo documento.
    docs_creados_count = db.query(func.count(models_doc.Documento.id)).filter(
        models_doc.Documento.usuario_creador_id == usuario_id
    ).scalar()

    if docs_creados_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se puede borrar. El usuario es autor de {docs_creados_count} documento(s) y el rastro de auditoría debe preservarse."
        )

    # Chequeo de documentos eliminados (también es parte del historial)
    # Usamos models_doc.DocumentoEliminado porque DocumentoEliminado está DENTRO del módulo documento.
    docs_eliminados_count = db.query(func.count(models_doc.DocumentoEliminado.id)).filter(
        models_doc.DocumentoEliminado.usuario_eliminacion_id == usuario_id
    ).scalar()
    
    if docs_eliminados_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se puede borrar. El usuario eliminó {docs_eliminados_count} documento(s) y el rastro de auditoría debe preservarse."
        )

    db.delete(usuario)
    db.commit()

    return {"message": "Usuario eliminado con éxito."}
# --- FIN: FUNCIÓN DELETE CON REFERENCIAS CORREGIDAS ---