# app/api/caracteristicas/routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user # O has_permission si defines permisos específicos
from app.models import usuario as models_usuario
from app.schemas import inventario as schemas_inventario # Usamos los schemas definidos allí
from app.services import inventario as service_inventario

router = APIRouter()

# Prefijo base para estas rutas (ej: /api/grupos/{grupo_id}/caracteristicas) será definido en main.py o aquí

@router.post(
    "/grupos/{grupo_id}/caracteristicas",
    response_model=schemas_inventario.CaracteristicaDefinicion,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva Definición de Característica para un Grupo"
    # Añadir dependencia de permiso si se requiere: , dependencies=[Depends(has_permission("inventario:configurar"))]
)
def create_caracteristica_definicion_route(
    grupo_id: int,
    definicion_data: schemas_inventario.CaracteristicaDefinicionCreate,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """
    Crea una nueva categoría de característica (ej: 'Color', 'Talla')
    para un Grupo de Inventario específico.
    """
    # El servicio ya valida que el grupo pertenezca a la empresa del usuario
    return service_inventario.create_caracteristica_definicion(
        db=db,
        definicion_data=definicion_data,
        grupo_id=grupo_id,
        empresa_id=current_user.empresa_id
    )

@router.get(
    "/grupos/{grupo_id}/caracteristicas",
    response_model=List[schemas_inventario.CaracteristicaDefinicion],
    summary="Obtener las Definiciones de Características de un Grupo"
    # Añadir dependencia de permiso si se requiere
)
def read_caracteristicas_definicion_by_grupo(
    grupo_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """
    Obtiene la lista de características definidas para un Grupo de Inventario específico.
    Útil para construir formularios dinámicos al crear/editar productos.
    """
    # El servicio valida pertenencia del grupo
    return service_inventario.get_caracteristicas_definicion_by_grupo(
        db=db,
        grupo_id=grupo_id,
        empresa_id=current_user.empresa_id
    )

@router.put(
    "/caracteristicas-definicion/{definicion_id}",
    response_model=schemas_inventario.CaracteristicaDefinicion,
    summary="Actualizar una Definición de Característica"
    # Añadir dependencia de permiso si se requiere
)
def update_caracteristica_definicion_route(
    definicion_id: int,
    definicion_update: schemas_inventario.CaracteristicaDefinicionUpdate,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """Actualiza los detalles de una definición de característica existente."""
    # El servicio valida pertenencia a la empresa
    updated_definicion = service_inventario.update_caracteristica_definicion(
        db=db,
        definicion_id=definicion_id,
        definicion_update=definicion_update,
        empresa_id=current_user.empresa_id
    )
    if updated_definicion is None: # El servicio ahora lanza excepción, pero mantenemos por si acaso
        raise HTTPException(status_code=404, detail="Definición de característica no encontrada.")
    return updated_definicion


@router.delete(
    "/caracteristicas-definicion/{definicion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una Definición de Característica"
    # Añadir dependencia de permiso si se requiere
)
def delete_caracteristica_definicion_route(
    definicion_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """
    Elimina una definición de característica.
    Los valores asociados a productos se eliminarán en cascada por la BD.
    """
    # El servicio valida pertenencia a la empresa
    service_inventario.delete_caracteristica_definicion(
        db=db,
        definicion_id=definicion_id,
        empresa_id=current_user.empresa_id
    )
    return None # 204 No Content