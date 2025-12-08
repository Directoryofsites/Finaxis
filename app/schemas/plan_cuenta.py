from pydantic import BaseModel, Field
from typing import Optional, List, Annotated

# --- NUEVO SCHEMA DE ENTRADA ---
# Este schema representa los datos que el usuario realmente envía desde el formulario de creación.
# Notar que no incluye 'empresa_id' ni 'nivel', ya que se calculan en el backend.
class PlanCuentaInput(BaseModel):
    codigo: Annotated[str, Field(max_length=20)]
    nombre: Annotated[str, Field(max_length=255)]
    permite_movimiento: bool = False
    funcion_especial: Optional[Annotated[str, Field(max_length=50)]] = None
    cuenta_padre_id: Optional[int] = None

# --- SCHEMAS PARA IMPORTACIÓN INTELIGENTE ---
class ImportarCuentaInput(BaseModel):
    codigo: str
    nombre: str
    # Opcionales para el input crudo
    nivel: Optional[int] = None
    permite_movimiento: Optional[bool] = None
    funcion_especial: Optional[str] = None

class AnalisisImportacionItem(BaseModel):
    codigo: str
    nombre: str
    nivel_calculado: int
    es_nueva: bool
    razon_rechazo: Optional[str] = None # Si es duplicada o inválida
    permite_movimiento: bool
    padre_codigo_sugerido: Optional[str] = None

class AnalisisImportacionResponse(BaseModel):
    cuentas_analizadas: List[AnalisisImportacionItem]
    total_nuevas: int
    total_existentes: int

class ImportarLoteRequest(BaseModel):
    cuentas: List[ImportarCuentaInput]

# --- SCHEMAS EXISTENTES ---
class PlanCuentaBase(BaseModel):
    codigo: Annotated[str, Field(max_length=20)]
    nombre: Annotated[str, Field(max_length=255)]
    nivel: int
    permite_movimiento: bool = False
    funcion_especial: Optional[Annotated[str, Field(max_length=50)]] = None
    clase_cuenta: Optional[Annotated[str, Field(max_length=50)]] = None
    cuenta_padre_id: Optional[int] = None

class PlanCuentaCreate(PlanCuentaBase):
    empresa_id: int

class PlanCuentaUpdate(BaseModel):
    nombre: Optional[Annotated[str, Field(max_length=255)]] = None
    permite_movimiento: Optional[bool] = None
    funcion_especial: Optional[Annotated[str, Field(max_length=50)]] = None
    clase_cuenta: Optional[Annotated[str, Field(max_length=50)]] = None
    cuenta_padre_id: Optional[int] = None

class PlanCuenta(PlanCuentaBase):
    id: int
    empresa_id: int
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    children: List['PlanCuenta'] = []

    class Config:
        from_attributes = True

class PlanCuentaSimple(BaseModel):
    id: int
    codigo: str
    nombre: str
    permite_movimiento: Optional[bool] = None
    saldo: Optional[float] = 0.0

    class Config:
        from_attributes = True
        
class CuentaDepurable(BaseModel):
    id: int
    codigo: str
    nombre: str
    nivel: int

class AnalisisDepuracionResponse(BaseModel):
    cuentas_a_eliminar: List[CuentaDepurable]
    cuentas_a_conservar_conteo: int
    mensaje: str

class EjecucionDepuracionRequest(BaseModel):
    ids_a_eliminar: List[int]