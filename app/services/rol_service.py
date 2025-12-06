# app/services/rol_service.py
from sqlalchemy.orm import Session
from typing import List
from app.models import permiso as models_permiso

def get_roles(db: Session) -> List[models_permiso.Rol]:
    """
    Devuelve una lista de todos los roles disponibles en el sistema.
    """
    return db.query(models_permiso.Rol).order_by(models_permiso.Rol.nombre).all()