from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services import rol as service
from app.schemas import permiso as schemas
from app.models import usuario as models_usuario
from app.core.security import get_current_user, has_permission

router = APIRouter(prefix="/roles", tags=["Roles y Permisos"])

# --- PERMISOS ---
@router.get("/permisos", response_model=List[schemas.Permiso])
def read_permisos(
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """Lista todos los permisos disponibles en el sistema."""
    return service.get_all_permisos(db)

# --- ROLES ---
@router.get("/", response_model=List[schemas.Rol])
def read_roles(
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("empresa:usuarios_roles"))
):
    """Lista roles globales y roles de la empresa actual."""
    empresa_id = current_user.empresa_id
    if not empresa_id:
        # Si es usuario de soporte o sin empresa, retornamos vacío o solo globales?
        # Por ahora asumimos uso dentro de empresa.
        # Retornamos solo globales (empresa_id=None) por seguridad default
        return service.get_roles_by_empresa(db, None)
        
    return service.get_roles_by_empresa(db, empresa_id)

@router.post("/", response_model=schemas.Rol)
def create_rol(
    rol_data: schemas.RolCreate,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("empresa:usuarios_roles"))
):
    """Crea un nuevo rol personalizado para la empresa."""
    if not current_user.empresa_id:
         raise HTTPException(status_code=400, detail="Solo usuarios de una empresa pueden crear roles")
    
    # Validar nombre único en la empresa (opcional, DB lo hace pero mejor aquí también)
    # Dejamos que el service/DB maneje el error de constraint por ahora.
    return service.create_rol(db, rol_data, current_user.empresa_id)

@router.put("/{rol_id}", response_model=schemas.Rol)
def update_rol(
    rol_id: int,
    rol_update: schemas.RolUpdate,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("empresa:usuarios_roles"))
):
    """Actualiza un rol existente."""
    rol = service.get_rol_by_id(db, rol_id)
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    # Seguridad: Solo editar roles PROPIOS de la empresa
    if rol.empresa_id != current_user.empresa_id:
        raise HTTPException(status_code=403, detail="No tiene permiso para editar este rol (Puede ser un rol del sistema)")
        
    return service.update_rol(db, rol, rol_update)

@router.delete("/{rol_id}")
def delete_rol(
    rol_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("empresa:usuarios_roles"))
):
    """Elimina un rol personalizado."""
    rol = service.get_rol_by_id(db, rol_id)
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    if rol.empresa_id != current_user.empresa_id:
        raise HTTPException(status_code=403, detail="No tiene permiso para eliminar este rol (Puede ser un rol del sistema)")
        
    service.delete_rol(db, rol)
    return {"message": "Rol eliminado exitosamente"}