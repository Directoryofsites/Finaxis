from typing import List, Optional
from pydantic import BaseModel, Field

class PermisoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class Permiso(PermisoBase):
    id: int

    class Config:
        from_attributes = True

class RolBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class RolCreate(RolBase):
    permisos_ids: List[int] = []

class RolUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    permisos_ids: Optional[List[int]] = None

class Rol(RolBase):
    id: int
    empresa_id: Optional[int] = None
    permisos: List[Permiso] = []

    class Config:
        from_attributes = True
