from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class FacturaItemCreate(BaseModel):
    """ Define un ítem (una línea) dentro de la factura. """
    producto_id: int
    cantidad: float = Field(..., gt=0) # gt=0 asegura que la cantidad sea mayor a cero
    precio_unitario: float = Field(..., ge=0) # ge=0 asegura que el precio no sea negativo
    descuento_tasa: Optional[float] = Field(default=0.0, ge=0, le=100) # Nueva

class FacturaCreate(BaseModel):
    """ Define la estructura completa para crear una nueva factura. """
    tipo_documento_id: int
    beneficiario_id: int
    fecha: date
    
    # --- INICIO DE LA MODIFICACIÓN ---
    # Se añade el campo para la condición de pago
    condicion_pago: str = Field(..., pattern="^(Contado|Crédito)$") # Acepta solo "Contado" o "Crédito"
    # --- FIN DE LA MODIFICACIÓN ---

    bodega_id: Optional[int] = None
    
    # --- NUEVOS CAMPOS DE DESCUENTO Y CARGOS ---
    descuento_global_valor: Optional[float] = Field(default=0.0, ge=0)
    cargos_globales_valor: Optional[float] = Field(default=0.0, ge=0)
    # -------------------------------------------

    # Una factura se compone de una lista de ítems
    items: List[FacturaItemCreate]

    # Campos opcionales
    centro_costo_id: Optional[int] = None
    fecha_vencimiento: Optional[date] = None
    remision_id: Optional[int] = None
    cotizacion_id: Optional[int] = None

    # --- NOTAS CREDITO / DEBITO ---
    documento_referencia_id: Optional[int] = None
    observaciones: Optional[str] = None
    discrepancy_response_code: Optional[int] = None
    discrepancy_response_description: Optional[str] = None
    # ------------------------------