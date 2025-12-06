from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime

class RemisionDetalleBase(BaseModel):
    producto_id: int
    cantidad_solicitada: float
    precio_unitario: float

class RemisionDetalleCreate(RemisionDetalleBase):
    pass

class RemisionDetalle(RemisionDetalleBase):
    id: int
    cantidad_facturada: float = 0
    cantidad_pendiente: float
    
    # Datos enriquecidos para vista (nombre producto)
    producto_nombre: Optional[str] = None 
    producto_codigo: Optional[str] = None

    class Config:
        from_attributes = True

class RemisionBase(BaseModel):
    fecha: date
    fecha_vencimiento: Optional[date] = None
    tercero_id: int
    bodega_id: int
    observaciones: Optional[str] = None

class RemisionCreate(RemisionBase):
    detalles: List[RemisionDetalleCreate]

class RemisionUpdate(BaseModel):
    observaciones: Optional[str] = None
    fecha_vencimiento: Optional[date] = None
    # Solo editable en BOM (Borrador), se podrían editar detalles via lógica especial

class Remision(RemisionBase):
    id: int
    numero: int
    estado: str
    usuario_id: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    # Relaciones para respuesta
    tercero_nombre: Optional[str] = None
    bodega_nombre: Optional[str] = None
    
    detalles: List[RemisionDetalle] = []

    class Config:
        from_attributes = True

class RemisionResponse(BaseModel):
    total: int
    remisiones: List[Remision]
