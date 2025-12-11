from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel, Field
from .inventario import ProductoResponse, ProductoSimple, Bodega as BodegaResponse # Importar esquemas

# --- Recetas ---

class RecetaDetalleBase(BaseModel):
    insumo_id: int
    cantidad: float

class RecetaDetalleCreate(RecetaDetalleBase):
    pass

class RecetaDetalleResponse(RecetaDetalleBase):
    id: int
    insumo: Optional[ProductoSimple] = None # Usar esquema ligero

    class Config:
        orm_mode = True

# --- Recursos de Receta (MOD/CIF) ---

class RecetaRecursoBase(BaseModel):
    descripcion: str
    tipo: str # MOD o CIF
    costo_estimado: float
    cuenta_contable_id: Optional[int] = None

class RecetaRecursoCreate(RecetaRecursoBase):
    pass

class RecetaRecursoResponse(RecetaRecursoBase):
    id: int
    
    class Config:
        orm_mode = True

class RecetaBase(BaseModel):
    producto_id: int
    nombre: str
    descripcion: Optional[str] = None
    cantidad_base: float = 1.0
    activa: bool = True

class RecetaCreate(RecetaBase):
    detalles: List[RecetaDetalleCreate]
    recursos: Optional[List[RecetaRecursoCreate]] = []

class RecetaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    cantidad_base: Optional[float] = None
    activa: Optional[bool] = None
    detalles: Optional[List[RecetaDetalleCreate]] = None
    recursos: Optional[List[RecetaRecursoCreate]] = None

class RecetaResponse(RecetaBase):
    id: int
    empresa_id: int
    fecha_creacion: datetime
    detalles: List[RecetaDetalleResponse] = []
    recursos: List[RecetaRecursoResponse] = []
    producto: Optional[ProductoSimple] = None # Usar esquema ligero para el PT también

    class Config:
        orm_mode = True

class RecetaSimple(RecetaBase):
    """Schema ligero de Receta sin detalles ni recursos, para listados."""
    id: int
    empresa_id: int
    fecha_creacion: datetime
    producto: Optional[ProductoSimple] = None # Usar esquema ligero

    class Config:
        orm_mode = True

# --- Ordenes de Producción ---

class OrdenProduccionInsumoResponse(BaseModel):
    id: int
    insumo_id: int
    bodega_origen_id: int
    cantidad: float
    costo_unitario_historico: float
    costo_total: float
    fecha_despacho: datetime
    insumo: Optional[ProductoSimple] = None # Usar esquema ligero
    bodega_origen: Optional[BodegaResponse] = None

    class Config:
        orm_mode = True

class OrdenProduccionRecursoCreate(BaseModel):
    descripcion: str
    tipo: str # MOD o CIF
    valor: float

class OrdenProduccionRecursoResponse(OrdenProduccionRecursoCreate):
    id: int
    fecha_registro: datetime

    class Config:
        orm_mode = True

class OrdenProduccionBase(BaseModel):
    producto_id: int
    bodega_destino_id: int
    cantidad_planeada: float
    receta_id: Optional[int] = None
    fecha_inicio: Optional[date] = None
    observaciones: Optional[str] = None

class OrdenProduccionCreate(OrdenProduccionBase):
    pass

class OrdenProduccionUpdate(BaseModel):
    cantidad_planeada: Optional[float] = None
    bodega_destino_id: Optional[int] = None
    fecha_fin: Optional[date] = None
    estado: Optional[str] = None
    observaciones: Optional[str] = None

class OrdenProduccionResponse(OrdenProduccionBase):
    id: int
    empresa_id: int
    numero_orden: str
    estado: str
    cantidad_real: Optional[float] = 0.0
    fecha_fin: Optional[date] = None
    fecha_creacion: datetime
    
    costo_total_mp: float
    costo_total_mod: float
    costo_total_cif: float
    costo_unitario_final: float

    producto: Optional[ProductoSimple] = None # Usar esquema ligero
    bodega_destino: Optional[BodegaResponse] = None # BodegaResponse es ligero (solo id, nombre)
    receta: Optional[RecetaSimple] = None # Usar esquema ligero
    
    insumos: List[OrdenProduccionInsumoResponse] = []
    recursos: List[OrdenProduccionRecursoResponse] = []

    class Config:
        orm_mode = True

class OrdenProduccionDetalleResponse(OrdenProduccionResponse):
    """Schema detallado para ver una orden individual (incluye ingredientes de receta)."""
    receta: Optional[RecetaResponse] = None # Usar esquema completo

    class Config:
        orm_mode = True

# --- Configuracion (Lifecycle) ---

class ConfigProduccionBase(BaseModel):
    tipo_documento_orden_id: Optional[int] = None
    tipo_documento_anulacion_id: Optional[int] = None
    tipo_documento_consumo_id: Optional[int] = None
    tipo_documento_entrada_pt_id: Optional[int] = None

class ConfigProduccionCreate(ConfigProduccionBase):
    pass

class ConfigProduccionResponse(ConfigProduccionBase):
    id: int
    empresa_id: int

    class Config:
        orm_mode = True
