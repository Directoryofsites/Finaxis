from typing import Optional, List
from pydantic import BaseModel

class PHModuloContribucionBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    tipo_distribucion: str = "COEFICIENTE" # COEFICIENTE, IGUALITARIO

class PHModuloContribucionCreate(PHModuloContribucionBase):
    torres_ids: Optional[List[int]] = []  # IDs de torres vinculadas a este módulo

class PHModuloContribucionUpdate(PHModuloContribucionBase):
    torres_ids: Optional[List[int]] = []  # IDs de torres vinculadas a este módulo

class PHModuloContribucionResponse(PHModuloContribucionBase):
    id: int
    empresa_id: int
    torres_ids: List[int] = []  # IDs de las torres vinculadas

    class Config:
        from_attributes = True
