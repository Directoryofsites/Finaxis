from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class IndicadorBase(BaseModel):
    salario_minimo: Optional[float] = 0
    auxilio_transporte: Optional[float] = 0
    uvt: Optional[float] = 0
    trm: Optional[float] = 0
    euro: Optional[float] = 0
    tasa_usura: Optional[float] = 0
    fecha_sincronizacion: Optional[datetime] = None

class IndicadorUpdate(IndicadorBase):
    pass

class IndicadorResponse(IndicadorBase):
    id: int
    vigencia: int
    updated_at: Optional[datetime]
    sancion_minima: Optional[float] = 0 # Computed property hint

    class Config:
        from_attributes = True
