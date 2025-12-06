# app/api/listas_precio/routes.py (Versión CORREGIDA Y COMPLETA)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# Importaciones necesarias
from app.core.database import get_db
from app.core.security import get_current_user # Asumiendo seguridad estándar
# Opcional: podrías definir permisos específicos con has_permission
# from app.core.security import has_permission

from app.models import usuario as models_usuario
# Importar schemas y servicios necesarios
from app.schemas import inventario as schemas_inventario
from app.services import inventario as service_inventario

router = APIRouter()

# ===============================================
# Endpoints para Listas de Precios (Se MANTIENEN)
# ===============================================

@router.post(
    "/listas-precio", # Ruta relativa al prefijo en main.py
    response_model=schemas_inventario.ListaPrecio,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva Lista de Precios"
    # Añadir dependencia de permiso si se requiere
)
def create_lista_precio_route(
    lista_precio: schemas_inventario.ListaPrecioCreate,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """Crea una nueva lista de precios para la empresa del usuario actual."""
    return service_inventario.create_lista_precio(db=db, lista_precio=lista_precio, empresa_id=current_user.empresa_id)

@router.get(
    "/listas-precio", # Ruta relativa al prefijo en main.py
    response_model=List[schemas_inventario.ListaPrecio],
    summary="Obtener todas las Listas de Precios de la empresa"
    # Añadir dependencia de permiso si se requiere
)
def read_listas_precio_route(
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """Obtiene todas las listas de precios asociadas a la empresa del usuario actual."""
    return service_inventario.get_listas_precio_by_empresa(db=db, empresa_id=current_user.empresa_id)

@router.put(
    "/listas-precio/{lista_id}", # Ruta relativa al prefijo en main.py
    response_model=schemas_inventario.ListaPrecio,
    summary="Actualizar una Lista de Precios"
    # Añadir dependencia de permiso si se requiere
)
def update_lista_precio_route(
    lista_id: int,
    lista_update: schemas_inventario.ListaPrecioUpdate,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """Actualiza el nombre de una lista de precios existente."""
    db_lista = service_inventario.update_lista_precio(db, lista_id=lista_id, lista_update=lista_update, empresa_id=current_user.empresa_id)
    if db_lista is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lista de precios no encontrada.")
    return db_lista

@router.delete(
    "/listas-precio/{lista_id}", # Ruta relativa al prefijo en main.py
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una Lista de Precios"
    # Añadir dependencia de permiso si se requiere
)
def delete_lista_precio_route(
    lista_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """
    Elimina una lista de precios si no está asignada a ninguna regla de precio por grupo.
    (La validación la hace el servicio).
    """
    # El servicio ahora puede lanzar HTTPException 409 si está en uso
    service_inventario.delete_lista_precio(db=db, lista_id=lista_id, empresa_id=current_user.empresa_id)
    return None # 204 No Content

# ==============================================================
# --- INICIO: NUEVOS Endpoints para Reglas de Precio por Grupo ---
# ==============================================================

@router.post(
    "/grupos/{grupo_id}/reglas-precio", # Ruta anidada bajo grupos
    response_model=schemas_inventario.ReglaPrecioGrupo,
    status_code=status.HTTP_200_OK, # OK porque puede crear o actualizar
    summary="Crear o Actualizar una Regla de Precio para un Grupo/Lista"
    # Añadir dependencia de permiso si se requiere: , dependencies=[Depends(has_permission("inventario:configurar"))]
)
def create_or_update_regla_precio_grupo_route(
    grupo_id: int,
    regla_data: schemas_inventario.ReglaPrecioGrupoCreate, # Recibe lista_precio_id y porcentaje
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """
    Crea una nueva regla de precio (porcentaje) para una combinación de
    Grupo de Inventario y Lista de Precios. Si ya existe una regla para
    esa combinación, actualiza el porcentaje.
    """
    # El servicio valida pertenencia de grupo y lista a la empresa
    return service_inventario.create_or_update_regla_precio_grupo(
        db=db,
        regla_data=regla_data,
        grupo_id=grupo_id,
        empresa_id=current_user.empresa_id
    )

@router.get(
    "/grupos/{grupo_id}/reglas-precio", # Ruta anidada bajo grupos
    response_model=List[schemas_inventario.ReglaPrecioGrupo],
    summary="Obtener las Reglas de Precio de un Grupo"
    # Añadir dependencia de permiso si se requiere
)
def read_reglas_precio_by_grupo_route(
    grupo_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """
    Obtiene la lista de reglas de precio (porcentaje por lista)
    definidas para un Grupo de Inventario específico.
    """
    # El servicio valida pertenencia del grupo
    return service_inventario.get_reglas_precio_by_grupo(
        db=db,
        grupo_id=grupo_id,
        empresa_id=current_user.empresa_id
    )

@router.delete(
    "/reglas-precio/{regla_id}", # Ruta específica para borrar por ID de regla
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una Regla de Precio"
    # Añadir dependencia de permiso si se requiere
)
def delete_regla_precio_grupo_route(
    regla_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """Elimina una regla de precio específica."""
    # El servicio valida pertenencia a la empresa
    service_inventario.delete_regla_precio_grupo(
        db=db,
        regla_id=regla_id,
        empresa_id=current_user.empresa_id
    )
    return None # 204 No Content

# ==========================================================
# --- FIN: NUEVOS Endpoints para Reglas de Precio por Grupo ---
# ==========================================================

# ==========================================================
# --- INICIO: NUEVOS Endpoints para Definiciones de Caracteristicas ---
# ==========================================================

@router.post(
    "/grupos/{grupo_id}/caracteristicas-definicion", # Ruta anidada bajo grupos
    response_model=schemas_inventario.CaracteristicaDefinicion,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva Definición de Característica para un Grupo"
    # Añadir dependencia de permiso si se requiere
)
def create_caracteristica_definicion_route(
    grupo_id: int,
    definicion_data: schemas_inventario.CaracteristicaDefinicionCreate,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """
    Crea una nueva categoría de característica (ej: 'Color', 'Talla', 'Unidad Medida')
    para un Grupo de Inventario específico.
    """
    return service_inventario.create_caracteristica_definicion(
        db=db,
        definicion_data=definicion_data,
        grupo_id=grupo_id,
        empresa_id=current_user.empresa_id
    )

@router.get(
    "/grupos/{grupo_id}/caracteristicas-definicion", # Ruta anidada bajo grupos
    response_model=List[schemas_inventario.CaracteristicaDefinicion],
    summary="Obtener las Definiciones de Características de un Grupo"
    # Añadir dependencia de permiso si se requiere
)
def read_caracteristicas_definicion_by_grupo_route(
    grupo_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """
    Obtiene la lista de características definidas para un Grupo de Inventario específico.
    Útil para construir formularios dinámicos al crear/editar productos.
    """
    return service_inventario.get_caracteristicas_definicion_by_grupo(
        db=db,
        grupo_id=grupo_id,
        empresa_id=current_user.empresa_id
    )

@router.put(
    "/caracteristicas-definicion/{definicion_id}", # Ruta específica por ID de definición
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
    updated_definicion = service_inventario.update_caracteristica_definicion(
        db=db,
        definicion_id=definicion_id,
        definicion_update=definicion_update,
        empresa_id=current_user.empresa_id
    )
    # El servicio ahora lanza excepción 404 si no se encuentra
    return updated_definicion


@router.delete(
    "/caracteristicas-definicion/{definicion_id}", # Ruta específica por ID de definición
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
    service_inventario.delete_caracteristica_definicion(
        db=db,
        definicion_id=definicion_id,
        empresa_id=current_user.empresa_id
    )
    return None # 204 No Content

# ==========================================================
# --- FIN: NUEVOS Endpoints para Definiciones de Caracteristicas ---
# ==========================================================