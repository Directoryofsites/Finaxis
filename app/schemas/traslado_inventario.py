# app/schemas/traslado_inventario.py (Nuevo)

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date

# --- 1. Item del Traslado ---
class TrasladoItemCreate(BaseModel):
    producto_id: int = Field(..., description="ID del producto a trasladar.")
    cantidad: float = Field(..., gt=0, description="Cantidad a mover (debe ser > 0).")
    
    class Config:
        json_schema_extra = {
            "example": {
                "producto_id": 101,
                "cantidad": 5.0
            }
        }

# --- 2. Cabecera del Traslado ---
class TrasladoInventarioCreate(BaseModel):
    tipo_documento_id: int = Field(..., description="ID del Tipo de Documento 'TR'.")
    bodega_origen_id: int = Field(..., description="Bodega de donde sale el stock.")
    bodega_destino_id: int = Field(..., description="Bodega a donde entra el stock.")
    fecha: date = Field(default_factory=date.today, description="Fecha de la transacción.")
    observaciones: Optional[str] = Field(None, max_length=255, description="Observaciones del traslado.")
    items: List[TrasladoItemCreate] = Field(..., description="Lista de productos a trasladar.")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tipo_documento_id": 5,
                "bodega_origen_id": 1,
                "bodega_destino_id": 2,
                "fecha": "2025-10-29",
                "observaciones": "Traslado interno por reorganización de almacén.",
                "items": [
                    {"producto_id": 101, "cantidad": 5.0},
                    {"producto_id": 102, "cantidad": 10.0}
                ]
            }
        }

# --- 3. Respuesta (Reutiliza el Documento creado) ---
class TrasladoInventarioResponse(BaseModel):
    id: int
    numero: int
    fecha: date
    bodega_origen_id: Optional[int] = None
    bodega_destino_id: Optional[int] = None
    observaciones: Optional[str] = None
    
    class Config:
        from_attributes = True
