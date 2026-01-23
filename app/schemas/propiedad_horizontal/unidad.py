from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal

# ... (Previous Schemas)

class PHTorreBase(BaseModel):
    nombre: str = Field(..., max_length=50)
    descripcion: Optional[str] = Field(None, max_length=200)

class PHTorreCreate(PHTorreBase):
    pass

class PHTorre(PHTorreBase):
    id: int
    empresa_id: int

    class Config:
        orm_mode = True

class PHVehiculoBase(BaseModel):
    placa: str = Field(..., max_length=20)
    tipo: str = "AUTOMOVIL" # MOTO, BICICLETA
    marca: Optional[str] = None
    color: Optional[str] = None
    propietario_nombre: Optional[str] = None

class PHVehiculoCreate(PHVehiculoBase):
    pass

class PHVehiculo(PHVehiculoBase):
    id: int
    unidad_id: int
    class Config:
        orm_mode = True

class PHMascotaBase(BaseModel):
    nombre: str = Field(..., max_length=50)
    especie: str = "PERRO" # GATO, OTRO
    raza: Optional[str] = None
    vacunas_al_dia: bool = False

class PHMascotaCreate(PHMascotaBase):
    pass

class PHMascota(PHMascotaBase):
    id: int
    unidad_id: int
    class Config:
        orm_mode = True

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
    vehiculos: List[PHVehiculoCreate] = []
    mascotas: List[PHMascotaCreate] = []
    modulos_ids: Optional[List[int]] = None

from app.schemas.propiedad_horizontal.modulo_contribucion import PHModuloContribucionResponse

class PHUnidad(PHUnidadBase):
    id: int
    empresa_id: int
    vehiculos: List[PHVehiculo] = []
    mascotas: List[PHMascota] = []
    modulos_contribucion: List[PHModuloContribucionResponse] = []
    torre_nombre: Optional[str] = None
    propietario_nombre: Optional[str] = None
    
    class Config:
        orm_mode = True

# --- NEW SCHEMA FOR MASS UPDATE ---
class PHUnidadMassUpdateModules(BaseModel):
    unidades_ids: List[int]
    add_modules_ids: List[int] = []
    remove_modules_ids: List[int] = []
