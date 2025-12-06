from pydantic import BaseModel
from datetime import date
from decimal import Decimal

class FacturaPendiente(BaseModel):
    id: int
    numero: int
    fecha: date
    valor_total: float
    saldo_pendiente: float

    class Config:
        from_attributes = True