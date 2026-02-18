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
    
    # --- PLANTILLA DE INDUSTRIA (Clonación) ---
    template_category: Optional[str] = None # RETAIL, SERVICIOS, PH (Legacy/Frontend string)
    template_id: Optional[int] = None # Precise ID selection (New)
    # ---------------------------------------------------------

    usuarios: List[UsuarioData] = []

    # Se elimina validación obligatoria de usuario para permitir creación por contador/holding
    # sin usuarios internos iniciales.

# --- ESQUEMA PARA LA EXTRACCIÓN DE PLANTILLA ---
class TemplateExtraction(BaseModel):
    name: Optional[str] = None
    category: str = "PERSONALIZADO" # Default category


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

    # --- PLANTILLAS ---
    is_template: Optional[bool] = None
    template_category: Optional[str] = None
    
    # --- MODO EXPRESS / LITE ---
    is_lite_mode: Optional[bool] = None
    saldo_facturas_venta: Optional[int] = None
    saldo_documentos_soporte: Optional[int] = None
    saldo_notas_credito: Optional[int] = None

class EmpresaLimiteUpdate(BaseModel):
    limite_registros: Optional[int] = Field(None, ge=0)
    saldo_facturas_venta: Optional[int] = None
    saldo_documentos_soporte: Optional[int] = None

# --- ESQUEMAS DE RESPUESTA ---
class EmpresaBase(BaseModel):
    razon_social: str
    nit: str
    fecha_inicio_operaciones: Optional[date] = None
    limite_registros: Optional[int] = None
    limite_registros_mensual: Optional[int] = None # Exposed for portal
    consumo_actual: Optional[int] = 0 # Calculated field
    
    # --- NUEVOS CAMPOS DE LECTURA ---
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    logo_url: Optional[str] = None
    
    # --- PLANTILLAS ---
    is_template: Optional[bool] = None
    template_category: Optional[str] = None

    # --- MODO EXPRESS ---
    is_lite_mode: Optional[bool] = False
    saldo_facturas_venta: Optional[int] = 0
    saldo_documentos_soporte: Optional[int] = 0
    is_lite_mode: Optional[bool] = False
    saldo_facturas_venta: Optional[int] = 0
    saldo_documentos_soporte: Optional[int] = 0
    fecha_vencimiento_plan: Optional[date] = None

    class Config:
        from_attributes = True

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