# app/schemas/empresa.py
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, TYPE_CHECKING
from datetime import date

# --- INICIO: IMPORTACIÓN CORREGIDA ---
# Importamos el schema de User correcto para evitar duplicación y errores.
if TYPE_CHECKING:
    from .usuario import User
    from .usuario import UserBasic
# --- FIN: IMPORTACIÓN CORREGIDA ---

# --- ESQUEMA INTERNO PARA DATOS DE USUARIO EN LA CREACIÓN ---
class UsuarioData(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

# --- ESQUEMA PRINCIPAL PARA LA CREACIÓN DE EMPRESA CON USUARIOS ---
class EmpresaConUsuariosCreate(BaseModel):
    razon_social: str = Field(..., min_length=3)
    nit: str = Field(..., min_length=5, max_length=20)
    fecha_inicio_operaciones: date
    
    # Campos opcionales desde el inicio
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    email: Optional[str] = None
    logo_url: Optional[str] = None
    
    # --- MODO DE OPERACIÓN (Control de Licencia/Auditoría) ---
    modo_operacion: Optional[str] = 'STANDARD' # STANDARD, AUDITORIA_READONLY
    
    # --- ROL INICIAL MANUAL (Opcional, si no se envía se auto-detecta) ---
    rol_inicial_id: Optional[int] = None
    # ---------------------------------------------------------

    usuarios: List[UsuarioData]

    @validator('usuarios')
    def debe_haber_al_menos_un_usuario(cls, v):
        if not v:
            raise ValueError('Se debe proporcionar al menos un usuario administrador.')
        return v

# --- ESQUEMA PARA LA ACTUALIZACIÓN DE DATOS DE LA EMPRESA ---
class EmpresaUpdate(BaseModel):
    razon_social: Optional[str] = Field(None, min_length=3)
    nit: Optional[str] = Field(None, min_length=5, max_length=20)
    fecha_inicio_operaciones: Optional[date] = None
    
    # --- NUEVOS CAMPOS EDITABLES ---
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    logo_url: Optional[str] = None

class EmpresaLimiteUpdate(BaseModel):
    limite_registros: Optional[int] = Field(None, ge=0)

# --- ESQUEMAS DE RESPUESTA ---
class EmpresaBase(BaseModel):
    razon_social: str
    nit: str
    fecha_inicio_operaciones: Optional[date] = None
    limite_registros: Optional[int] = None
    
    # --- NUEVOS CAMPOS DE LECTURA ---
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    logo_url: Optional[str] = None

class Empresa(EmpresaBase):
    id: int

    class Config:
        from_attributes = True

# --- INICIO: NUEVO ESQUEMA PARA EL PANEL DE MANDO ---
# Este es el esquema que representa una Empresa junto con su lista de Usuarios.
class EmpresaConUsuarios(Empresa):
    usuarios: List['UserBasic'] = []
# --- FIN: NUEVO ESQUEMA ---

# ... al final del archivo ...

class CupoAdicionalCreate(BaseModel):
    anio: int
    mes: int
    cantidad_adicional: int