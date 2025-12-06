from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class CompraItemCreate(BaseModel):
    """ Define un ítem (una línea) dentro de la factura de compra. """
    producto_id: int
    cantidad: float = Field(..., gt=0)
    costo_unitario: float = Field(..., ge=0)

class CompraCreate(BaseModel):
    """ Define la estructura completa para crear una nueva factura de compra. """
    tipo_documento_id: int
    beneficiario_id: int # En este caso, el proveedor
    fecha: date
    
    items: List[CompraItemCreate]
    bodega_id: int

    # --- INICIO: CAMPO AÑADIDO ---
    numero: Optional[str] = None # Para la numeración manual
    # --- FIN: CAMPO AÑADIDO ---

    # Campos opcionales
    centro_costo_id: Optional[int] = None
    fecha_vencimiento: Optional[date] = None