from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime

class CotizacionDetalleBase(BaseModel):
    producto_id: int
    cantidad: float
    precio_unitario: float

class CotizacionDetalleCreate(CotizacionDetalleBase):
    pass

class CotizacionDetalle(CotizacionDetalleBase):
    id: int
    cantidad_facturada: float = 0
    
    # Datos enriquecidos para vista
    producto_nombre: Optional[str] = None 
    producto_codigo: Optional[str] = None

    class Config:
        from_attributes = True

class CotizacionBase(BaseModel):
    fecha: date
    fecha_vencimiento: Optional[date] = None
    tercero_id: int
    bodega_id: Optional[int] = None # Opcional en cotización
    observaciones: Optional[str] = None

class CotizacionCreate(CotizacionBase):
    detalles: List[CotizacionDetalleCreate]

class CotizacionUpdate(CotizacionBase):
    pass

class Cotizacion(CotizacionBase):
    id: int
    numero: int
    estado: str
    usuario_id: Optional[int]
    total_estimado: float = 0.0
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    # Relaciones para respuesta
    tercero_nombre: Optional[str] = None
    bodega_nombre: Optional[str] = None
    
    detalles: List[CotizacionDetalle] = []

    class Config:
        from_attributes = True

class CotizacionResponse(BaseModel):
    total: int
    cotizaciones: List[Cotizacion]
