from pydantic import BaseModel
from typing import Optional

# Esquema para recibir los datos al crear un cierre
class PeriodoCreate(BaseModel):
    ano: int
    mes: int

# Esquema para devolver la información de un período cerrado
class PeriodoResponse(BaseModel):
    id: int
    empresa_id: int
    ano: int
    mes: int
    cerrado_por_usuario_id: Optional[int] = None # Puede ser nulo si el dato es antiguo

    class Config:
        from_attributes = True