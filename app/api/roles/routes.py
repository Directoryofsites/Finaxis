# app/api/roles/routes.py
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import rol as schemas_rol  # CORRECCIÓN: Importamos el nuevo schema de rol
from app.services import rol_service
from app.core.security import get_current_user
# Importamos el schema de Usuario solo para la dependencia de seguridad
from app.schemas import usuario as schemas_usuario

router = APIRouter(prefix="/roles", tags=["Roles y Permisos"])

@router.get("/", response_model=List[schemas_rol.Rol]) # CORRECCIÓN: Usamos el response_model correcto
def read_roles(
    db: Session = Depends(get_db),
    current_user: schemas_usuario.User = Depends(get_current_user) # Protegemos la ruta
):
    """
    Obtiene una lista de todos los roles disponibles para asignar a usuarios.
    """
    return rol_service.get_roles(db=db)