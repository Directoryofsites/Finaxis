# app/schemas/usuario.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, TYPE_CHECKING

# --- NUEVOS SCHEMAS PARA ROLES Y PERMISOS ---
class Permiso(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    class Config:
        from_attributes = True

class Rol(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    permisos: List[Permiso] = []
    class Config:
        from_attributes = True
# --- FIN DE NUEVOS SCHEMAS ---

class UserCreateInCompany(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    nombre_completo: Optional[str] = None
    # CAMBIO: Ya no usamos 'rol' como texto. Pedimos una lista de IDs de roles.
    roles_ids: List[int] = Field(..., min_length=1)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    nombre_completo: Optional[str] = None
    roles_ids: Optional[List[int]] = None

class UserBasic(BaseModel):
    id: int
    email: str
    nombre_completo: Optional[str] = None
    empresa_id: Optional[int] = None
    
    # CAMBIO: Devolvemos la lista completa de objetos de Rol asignados.
    roles: List[Rol] = []

    class Config:
        from_attributes = True

class User(UserBasic):
    
    # --- INCLUIR DETALLES EMPRESA (Para Frontend Control) ---
    if TYPE_CHECKING:
        from .empresa import EmpresaBase
    empresa: Optional['EmpresaBase'] = None
    # --------------------------------------------------------

    class Config:
        from_attributes = True

# --- Schemas existentes sin cambios ---
class UserPasswordUpdate(BaseModel):
    nuevaPassword: str

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetPayload(BaseModel):
    token: str
    nueva_password: str

class SoporteUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="La contraseña del nuevo usuario de soporte")
    nombre_completo: Optional[str] = None

class UserDeleteResponse(BaseModel):
    message: str