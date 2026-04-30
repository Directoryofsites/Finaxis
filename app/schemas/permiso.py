from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum

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


# ============================================================
# SCHEMAS PARA EXCEPCIONES DE PERMISOS POR USUARIO
# ============================================================

class TipoExcepcion(str, Enum):
    CONCEDIDO = "CONCEDIDO"   # El rol NO lo tiene pero el admin se lo dio
    REVOCADO   = "REVOCADO"   # El rol SÍ lo tiene pero el admin se lo quitó

class ExcepcionPermisoUpsert(BaseModel):
    """Payload para crear o actualizar una excepción sobre un permiso específico."""
    permiso_id: int
    permitido: bool  # True = CONCEDER, False = REVOCAR

class ExcepcionPermisoBatch(BaseModel):
    """Payload para guardar varias excepciones a la vez."""
    excepciones: List[ExcepcionPermisoUpsert]

class ExcepcionPermisoResponse(BaseModel):
    """Representa una excepción activa sobre un usuario."""
    permiso_id: int
    permiso_nombre: str
    permiso_descripcion: Optional[str] = None
    tipo: TipoExcepcion  # CONCEDIDO o REVOCADO

    class Config:
        from_attributes = True

class PermisoConEstado(BaseModel):
    """
    Vista enriquecida de un permiso para la pantalla de edición de usuario.
    Muestra el estado real del permiso considerando rol + excepción.
    """
    id: int
    nombre: str
    descripcion: Optional[str] = None
    tiene_por_rol: bool              # ¿Lo hereda de su rol?
    tiene_excepcion: bool            # ¿Hay una excepción configurada?
    excepcion_permitido: Optional[bool] = None  # None = sin excepción, True/False = acción
    estado_efectivo: bool            # Resultado final: ¿puede o no puede?

    class Config:
        from_attributes = True
