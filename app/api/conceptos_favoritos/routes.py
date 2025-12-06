# app/api/conceptos_favoritos/routes.py (REEMPLAZO COMPLETO Y CORREGIDO)

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# FIX CRÍTICO 1: Importamos el servicio correcto (concepto_favorito)
from app.services import concepto_favorito as service 
# FIX CRÍTICO 2: Importamos el schema que acabamos de corregir
from app.schemas import concepto_favorito as schemas_fav

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Usuario as models_usuario

router = APIRouter(
    prefix="/conceptos-favoritos", # FIX: Ajustamos el prefijo para ser claro
    tags=["Conceptos Favoritos"]
)

# --- CREAR CONCEPTO FAVORITO ---
@router.post(
    "/",
    # FIX: response_model usa el Schema corregido (ConceptoFavorito)
    response_model=schemas_fav.ConceptoFavorito,
    status_code=status.HTTP_201_CREATED
)
def create_concepto_favorito_endpoint(
    # FIX: El input usa el Schema base corregido (ConceptoFavoritoBase)
    concepto_input: schemas_fav.ConceptoFavoritoBase,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    # Creamos el objeto ConceptoFavoritoCreate que el servicio espera
    concepto_a_crear = schemas_fav.ConceptoFavoritoCreate(
        descripcion=concepto_input.descripcion,
        centro_costo_id=concepto_input.centro_costo_id,
        empresa_id=current_user.empresa_id, # Inyectamos ID de empresa
        created_by=current_user.id,
        updated_by=current_user.id
    )
    
    # FIX: Llamada al servicio corregido (create_concepto_favorito)
    return service.create_concepto_favorito(db=db, concepto=concepto_a_crear, user_id=current_user.id)


# --- OBTENER CONCEPTOS FAVORITOS ---
@router.get(
    "/", 
    # FIX: response_model usa la lista del Schema corregido (List[ConceptoFavorito])
    response_model=List[schemas_fav.ConceptoFavorito]
)
def read_conceptos_favoritos(
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    # FIX: Llamada al servicio corregido (get_conceptos_by_empresa)
    return service.get_conceptos_by_empresa(db=db, empresa_id=current_user.empresa_id)


# --- ACTUALIZAR CONCEPTO FAVORITO ---
@router.put(
    "/{concepto_id}", 
    # FIX: response_model usa el Schema corregido (ConceptoFavorito)
    response_model=schemas_fav.ConceptoFavorito
)
def update_concepto_favorito_endpoint(
    concepto_id: int,
    # FIX: La actualización usa el esquema de actualización corregido (ConceptoFavoritoUpdate)
    concepto_update: schemas_fav.ConceptoFavoritoUpdate,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    # FIX: Llamada al servicio corregido (update_concepto_favorito)
    db_concepto = service.update_concepto_favorito(
        db,
        concepto_id=concepto_id,
        concepto_update=concepto_update,
        empresa_id=current_user.empresa_id,
        user_id=current_user.id
    )
    if db_concepto is None:
        raise HTTPException(status_code=404, detail="El concepto favorito no fue encontrado o no pertenece a la empresa.")
    return db_concepto


# --- ELIMINAR CONCEPTOS FAVORITOS ---
@router.delete("/", status_code=status.HTTP_200_OK)
def delete_conceptos_favoritos_endpoint(
    conceptos_a_borrar: schemas_fav.ConceptosDelete,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    # FIX: Llamada al servicio corregido (delete_conceptos_favoritos)
    count = service.delete_conceptos_favoritos(
        db=db,
        ids=conceptos_a_borrar.ids,
        empresa_id=current_user.empresa_id
    )
            
    if count == 0:
        raise HTTPException(status_code=404, detail="No se encontraron conceptos favoritos con los IDs proporcionados para esta empresa.")
        
    return {"detail": f"{count} concepto(s) favorito(s) eliminado(s) exitosamente."}