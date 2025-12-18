from typing import Optional, List
from pydantic import BaseModel

class PHModuloContribucionBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    tipo_distribucion: str = "COEFICIENTE" # COEFICIENTE, IGUALITARIO

class PHModuloContribucionCreate(PHModuloContribucionBase):
    pass

class PHModuloContribucionUpdate(PHModuloContribucionBase):
    pass

class PHModuloContribucionResponse(PHModuloContribucionBase):
    id: int
    empresa_id: int

    class Config:
        orm_mode = True
