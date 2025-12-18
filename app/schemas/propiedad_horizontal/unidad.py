from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal
from .modulo_contribucion import PHModuloContribucionResponse

# --- TORRES ---
class PHTorreBase(BaseModel):
    nombre: str = Field(..., max_length=50)
    descripcion: Optional[str] = Field(None, max_length=200)

class PHTorreCreate(PHTorreBase):
    pass

class PHTorre(PHTorreBase):
    id: int
    empresa_id: int

    class Config:
        from_attributes = True

# --- VEHICULOS ---
class PHVehiculoBase(BaseModel):
    placa: str = Field(..., max_length=20)
    tipo: Optional[str] = "Carro"
    marca: Optional[str] = None
    color: Optional[str] = None
    propietario_nombre: Optional[str] = None

class PHVehiculoCreate(PHVehiculoBase):
    pass

class PHVehiculo(PHVehiculoBase):
    id: int
    unidad_id: int
    class Config:
        from_attributes = True

# --- MASCOTAS ---
class PHMascotaBase(BaseModel):
    nombre: str = Field(..., max_length=50)
    especie: str = Field(..., max_length=30)
    raza: Optional[str] = None
    vacunas_al_dia: bool = False

class PHMascotaCreate(PHMascotaBase):
    pass

class PHMascota(PHMascotaBase):
    id: int
    unidad_id: int
    class Config:
        from_attributes = True

# --- UNIDADES ---
class PHUnidadBase(BaseModel):
    codigo: str = Field(..., max_length=50, title="Número de Apto/Casa")
    tipo: str = "RESIDENCIAL" 
    torre_id: Optional[int] = None
    matricula_inmobiliaria: Optional[str] = None
    area_privada: Optional[Decimal] = 0
    coeficiente: Decimal = Field(..., ge=0, le=100, description="Coeficiente de copropiedad (0-100 o 0-1)")
    
    propietario_principal_id: Optional[int] = None
    residente_actual_id: Optional[int] = None
    
    activo: bool = True
    observaciones: Optional[str] = None

class PHUnidadCreate(PHUnidadBase):
    vehiculos: Optional[List[PHVehiculoCreate]] = []
    mascotas: Optional[List[PHMascotaCreate]] = []
    modulos_ids: Optional[List[int]] = []

class PHUnidadUpdate(PHUnidadBase):
    modulos_ids: Optional[List[int]] = []

class PHUnidad(PHUnidadBase):
    id: int
    empresa_id: int
    
    # Nested info
    torre_nombre: Optional[str] = None # Calculated or joined
    mascotas: List[PHMascota] = []
    vehiculos: List[PHVehiculo] = []
    propietario_nombre: Optional[str] = None
    modulos_contribucion: List["PHModuloContribucionResponse"] = []

    class Config:
        from_attributes = True
