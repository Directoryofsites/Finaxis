# app/services/favoritos.py (VERSIÓN CORREGIDA Y FORZADA A LÍMITE 16)

from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from typing import List, Optional

# Nota: Asumo que los modelos se llaman 'usuario_favorito' y 'usuario'
from ..models import usuario_favorito as models_favorito 
from ..models import usuario as models_usuario
from ..schemas import usuario_favorito as schemas_favorito

# FIX 1: Límite de botones CENTRALIZADO: Aumentado de 12 a 16
# (Se mantiene para la documentación, pero no se usa en la validación crítica)
MAX_FAVORITOS = 16 

def get_favoritos_by_user_id(db: Session, user_id: int) -> List[models_favorito.UsuarioFavorito]:
    """Obtiene todos los accesos rápidos definidos por un usuario ordenados por el campo 'orden'."""
    return db.query(models_favorito.UsuarioFavorito).filter(
        models_favorito.UsuarioFavorito.usuario_id == user_id
    ).order_by(models_favorito.UsuarioFavorito.orden).all()

def create_favorito(db: Session, favorito: schemas_favorito.UsuarioFavoritoCreate, user_id: int) -> models_favorito.UsuarioFavorito:
    """Crea un nuevo acceso rápido para un usuario, aplicando validaciones."""
    
    # FIX CRÍTICO: Forzamos el límite a 16 aquí para garantizar que el Backend lo vea.
    LIMITE_DEFINITIVO = 16
    conteo_actual = db.query(func.count(models_favorito.UsuarioFavorito.id)).filter(
        models_favorito.UsuarioFavorito.usuario_id == user_id
    ).scalar()
    
    if conteo_actual >= LIMITE_DEFINITIVO:
        # FIX: Mensaje de error actualizado
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Límite alcanzado: Un usuario solo puede tener {LIMITE_DEFINITIVO} accesos rápidos."
        )

    # 2. Validar unicidad de orden (el orden debe ser único por usuario)
    favorito_existente = db.query(models_favorito.UsuarioFavorito).filter(
        models_favorito.UsuarioFavorito.usuario_id == user_id,
        models_favorito.UsuarioFavorito.orden == favorito.orden
    ).first()
    
    if favorito_existente:
         raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un acceso rápido en la posición {favorito.orden}. Por favor, elija otra."
        )

    db_favorito = models_favorito.UsuarioFavorito(
        **favorito.model_dump(),
        usuario_id=user_id
    )
    
    db.add(db_favorito)
    db.commit()
    db.refresh(db_favorito)
    return db_favorito

def update_favorito(db: Session, favorito_id: int, favorito_update: schemas_favorito.UsuarioFavoritoUpdate, user_id: int) -> Optional[models_favorito.UsuarioFavorito]:
    """Actualiza un acceso rápido existente, aplicando validaciones."""
    db_favorito = db.query(models_favorito.UsuarioFavorito).filter(
        models_favorito.UsuarioFavorito.id == favorito_id,
        models_favorito.UsuarioFavorito.usuario_id == user_id
    ).first()

    if not db_favorito:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acceso rápido no encontrado o no pertenece al usuario.")

    update_data = favorito_update.model_dump(exclude_unset=True)
    
    # Validar si el 'orden' está cambiando y si el nuevo orden ya existe
    if 'orden' in update_data and update_data['orden'] != db_favorito.orden:
        orden_existente = db.query(models_favorito.UsuarioFavorito).filter(
            models_favorito.UsuarioFavorito.usuario_id == user_id,
            models_favorito.UsuarioFavorito.orden == update_data['orden'],
            models_favorito.UsuarioFavorito.id != favorito_id
        ).first()
        
        if orden_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe otro favorito en la posición {update_data['orden']}."
            )

    for key, value in update_data.items():
        setattr(db_favorito, key, value)

    db.commit()
    db.refresh(db_favorito)
    return db_favorito

def delete_favorito(db: Session, favorito_id: int, user_id: int):
    """Elimina un acceso rápido si pertenece al usuario."""
    db_favorito = db.query(models_favorito.UsuarioFavorito).filter(
        models_favorito.UsuarioFavorito.id == favorito_id,
        models_favorito.UsuarioFavorito.usuario_id == user_id
    ).first()

    if not db_favorito:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acceso rápido no encontrado o no pertenece al usuario.")

    db.delete(db_favorito)
    db.commit()