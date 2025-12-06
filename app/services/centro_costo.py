from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.models import centro_costo as models
from app.schemas import centro_costo as schemas

# --- INICIO: NUEVAS IMPORTACIONES PARA VALIDACIÓN DE DEPENDENCIAS ---
from app.models.documento import Documento
# --- FIN: NUEVAS IMPORTACIONES ---


# --- INICIO: FUNCIÓN DE VALIDACIÓN CORREGIDA ---
def _validar_y_calcular_jerarquia(db: Session, centro_costo: schemas.CentroCostoInput, empresa_id: int):
    nivel = 1
    if centro_costo.centro_costo_padre_id:
        padre = db.query(models.CentroCosto).filter(
            models.CentroCosto.id == centro_costo.centro_costo_padre_id,
            models.CentroCosto.empresa_id == empresa_id
        ).first()
        if not padre:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El centro de costo padre no existe.")
        
        # --- LÍNEA CORREGIDA ---
        # La regla correcta: un padre NO DEBE permitir movimiento para poder tener hijos.
        if padre.permite_movimiento: # Si es True, es una cuenta y no puede ser padre.
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un centro de costo de tipo 'Cuenta' (que permite movimiento) no puede tener sub-niveles."
            )
        nivel = padre.nivel + 1
    return nivel
# --- FIN: FUNCIÓN DE VALIDACIÓN CORREGIDA ---

def create_centro_costo(db: Session, centro_costo: schemas.CentroCostoInput, empresa_id: int, user_id: int):
    nivel = _validar_y_calcular_jerarquia(db, centro_costo, empresa_id)
    
    db_centro_costo = models.CentroCosto(
        **centro_costo.model_dump(),
        empresa_id=empresa_id,
        nivel=nivel,
        created_by=user_id,
        updated_by=user_id
    )
    db.add(db_centro_costo)
    db.commit()
    db.refresh(db_centro_costo)
    return db_centro_costo

def get_centros_costo_flat(db: Session, empresa_id: int) -> List[models.CentroCosto]:
    return db.query(models.CentroCosto).filter(
        models.CentroCosto.empresa_id == empresa_id
    ).order_by(models.CentroCosto.codigo).all()

def update_centro_costo(db: Session, centro_costo_id: int, centro_costo_update: schemas.CentroCostoUpdateInput, empresa_id: int, user_id: int):
    db_centro_costo = db.query(models.CentroCosto).filter(
        models.CentroCosto.id == centro_costo_id,
        models.CentroCosto.empresa_id == empresa_id
    ).first()

    if not db_centro_costo:
        return None

    update_data = centro_costo_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_centro_costo, key, value)
    
    db_centro_costo.updated_by = user_id
    db.commit()
    db.refresh(db_centro_costo)
    return db_centro_costo

def delete_centro_costo(db: Session, centro_costo_id: int, empresa_id: int):
    db_centro_costo = db.query(models.CentroCosto).options(
        joinedload(models.CentroCosto.hijos),
        joinedload(models.CentroCosto.movimientos),
        joinedload(models.CentroCosto.plantillas_maestras_sugeridas)
    ).filter(
        models.CentroCosto.id == centro_costo_id,
        models.CentroCosto.empresa_id == empresa_id
    ).first()

    if not db_centro_costo:
        return None 
    
    if db_centro_costo.hijos:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se puede eliminar. El centro de costo '{db_centro_costo.nombre}' tiene {len(db_centro_costo.hijos)} sub-niveles asociados."
        )

    if db_centro_costo.movimientos:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se puede eliminar. El centro de costo está en uso en {len(db_centro_costo.movimientos)} movimientos contables."
        )

    documento_asociado = db.query(Documento).filter(Documento.centro_costo_id == centro_costo_id).first()
    if documento_asociado:
         raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se puede eliminar. El centro de costo está asociado al encabezado del documento '{documento_asociado.tipo_documento.codigo}-{documento_asociado.numero}'."
        )

    if db_centro_costo.plantillas_maestras_sugeridas:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se puede eliminar. Es usado como sugerencia en {len(db_centro_costo.plantillas_maestras_sugeridas)} plantillas."
        )

    db.delete(db_centro_costo)
    db.commit()
    return True

def get_descendant_ids_inclusive(db: Session, empresa_id: int, centro_costo_id: int) -> List[int]:
    todos_los_cc = db.query(models.CentroCosto).filter(models.CentroCosto.empresa_id == empresa_id).all()
    cc_map = {cc.id: cc for cc in todos_los_cc}
    if centro_costo_id not in cc_map:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El centro de costo de inicio con ID {centro_costo_id} no fue encontrado en esta empresa."
        )
    descendientes_ids = set()
    cola = [centro_costo_id]
    while cola:
        id_actual = cola.pop(0)
        if id_actual in descendientes_ids:
            continue
        descendientes_ids.add(id_actual)
        hijos = [cc.id for cc in todos_los_cc if cc.centro_costo_padre_id == id_actual]
        cola.extend(hijos)
    return list(descendientes_ids)