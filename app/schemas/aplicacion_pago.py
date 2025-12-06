from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

# Esquema base con los campos que se envían para crear una aplicación
class AplicacionPagoCreate(BaseModel):
    documento_factura_id: int
    valor_aplicado: Decimal

# Esquema para devolver los datos de una aplicación desde la API
class AplicacionPago(BaseModel):
    id: int
    documento_factura_id: int
    documento_pago_id: int
    valor_aplicado: Decimal
    fecha_aplicacion: datetime
    empresa_id: int

    class Config:
        from_attributes = True