from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services import rol as service
from app.schemas import permiso as schemas
from app.models import usuario as models_usuario
from app.core.security import get_current_user, has_permission, get_user_permissions

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
    empresa_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """
    Lista roles.
    - Si es usuario normal: devuelve roles de SU empresa.
    - Si es usuario soporte (y pasa empresa_id): devuelve roles de ESA empresa.
    """
    
    # 1. Verificar si es usuario soporte
    is_soporte = any(role.nombre == 'soporte' for role in current_user.roles)

    # 2. Verificar permisos estándar si NO es soporte o si NO está actuando como soporte
    if not is_soporte:
        # Check manual de permiso (ya que quitamos el Depends en la firma)
        user_permissions = get_user_permissions(current_user)
        if "empresa:usuarios_roles" not in user_permissions:
             raise HTTPException(status_code=403, detail="Acceso denegado: se requiere el permiso 'empresa:usuarios_roles'")
        
        # Usuario normal: SIEMPRE restringido a su propia empresa
        target_empresa_id = current_user.empresa_id
    else:
        # Es soporte:
        # Si envía empresa_id, usamos ese.
        # Si no envía, comportamiento default (null o su propia empresa si tuviera)
        target_empresa_id = empresa_id if empresa_id else current_user.empresa_id

    if not target_empresa_id and not is_soporte:
         # Caso raro: usuario sin empresa y sin permiso soporte
         return service.get_roles_by_empresa(db, None)

    return service.get_roles_by_empresa(db, target_empresa_id)


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