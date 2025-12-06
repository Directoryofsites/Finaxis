from pydantic import BaseModel, Field
from typing import Optional, List

class CentroCostoInput(BaseModel):
    codigo: str = Field(max_length=50)
    nombre: str = Field(max_length=255)
    permite_movimiento: bool = True
    centro_costo_padre_id: Optional[int] = None

class CentroCostoUpdateInput(BaseModel):
    nombre: Optional[str] = Field(None, max_length=255)
    permite_movimiento: Optional[bool] = None

class CentroCosto(BaseModel):
    id: int
    codigo: str
    nombre: str
    nivel: int
    permite_movimiento: bool
    centro_costo_padre_id: Optional[int] = None
    hijos: List['CentroCosto'] = []

    class Config:
        from_attributes = True

CentroCosto.model_rebuild()