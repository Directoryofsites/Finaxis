# app/services/concepto_favorito.py (REEMPLAZO COMPLETO Y CORREGIDO)

from sqlalchemy.orm import Session
from typing import List, Optional

# Importamos el modelo correcto
from ..models import concepto_favorito as models
# Importamos el schema que acabamos de corregir
from ..schemas import concepto_favorito as schemas

def get_conceptos_by_empresa(db: Session, empresa_id: int):
    """Obtiene todos los conceptos favoritos de una empresa, ordenados por descripción."""
    return db.query(models.ConceptoFavorito).filter(
        models.ConceptoFavorito.empresa_id == empresa_id
    ).order_by(models.ConceptoFavorito.descripcion).all()

# FIX CRÍTICO: El input ahora usa el Schema de Creación correcto (ConceptoFavoritoCreate)
def create_concepto_favorito(db: Session, concepto: schemas.ConceptoFavoritoCreate, user_id: int):
    """Crea un nuevo concepto favorito, mapeando los campos correctos del modelo."""
    
    # Mapeo explícito de los campos necesarios desde el Schema al Modelo
    db_concepto = models.ConceptoFavorito(
        empresa_id=concepto.empresa_id,
        descripcion=concepto.descripcion,
        centro_costo_id=concepto.centro_costo_id, # Campo opcional
        created_by=user_id,
        updated_by=user_id
    )
    
    db.add(db_concepto)
    db.commit()
    db.refresh(db_concepto)
    return db_concepto

# FIX DE FIRMA: El input ahora usa el Schema de Actualización correcto (ConceptoFavoritoUpdate)
def update_concepto_favorito(
    db: Session, concepto_id: int, concepto_update: schemas.ConceptoFavoritoUpdate, empresa_id: int, user_id: int
):
    """Actualiza un concepto favorito existente."""
    db_concepto = db.query(models.ConceptoFavorito).filter(
        models.ConceptoFavorito.id == concepto_id,
        models.ConceptoFavorito.empresa_id == empresa_id
    ).first()
    if not db_concepto:
        return None
    
    # Usamos model_dump para actualizar solo los campos provistos (exclude_unset=True)
    update_data = concepto_update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_concepto, key, value)
    
    db_concepto.updated_by = user_id
    db.commit()
    db.refresh(db_concepto)
    return db_concepto

# FIX DE FIRMA: El input ahora usa el Schema de Eliminación correcto (ConceptosDelete)
def delete_conceptos_favoritos(db: Session, ids: List[int], empresa_id: int) -> int:
    """Elimina uno o más conceptos favoritos de forma segura."""
    if not ids:
        return 0
    conceptos_a_borrar = db.query(models.ConceptoFavorito).filter(
        models.ConceptoFavorito.id.in_(ids),
        models.ConceptoFavorito.empresa_id == empresa_id
    ).all()
    if not conceptos_a_borrar:
        return 0
    
    for concepto in conceptos_a_borrar:
        db.delete(concepto)
    
    db.commit()
    return len(conceptos_a_borrar)