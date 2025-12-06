from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class FacturaItemCreate(BaseModel):
    """ Define un ítem (una línea) dentro de la factura. """
    producto_id: int
    cantidad: float = Field(..., gt=0) # gt=0 asegura que la cantidad sea mayor a cero
    precio_unitario: float = Field(..., ge=0) # ge=0 asegura que el precio no sea negativo

class FacturaCreate(BaseModel):
    """ Define la estructura completa para crear una nueva factura. """
    tipo_documento_id: int
    beneficiario_id: int
    fecha: date
    
    # --- INICIO DE LA MODIFICACIÓN ---
    # Se añade el campo para la condición de pago
    condicion_pago: str = Field(..., pattern="^(Contado|Crédito)$") # Acepta solo "Contado" o "Crédito"
    # --- FIN DE LA MODIFICACIÓN ---

    bodega_id: int

    # Una factura se compone de una lista de ítems
    items: List[FacturaItemCreate]

    # Campos opcionales
    centro_costo_id: Optional[int] = None
    fecha_vencimiento: Optional[date] = None