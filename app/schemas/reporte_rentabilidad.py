# app/schemas/reporte_rentabilidad.py (VERSIÓN CON RENOMBRAMIENTO A TRAZABILIDAD COMPLETA)

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from decimal import Decimal

# --- ESQUEMAS PARA TRAZABILIDAD ---
class TopDocumentoTrazabilidad(BaseModel):
    documento_id: int
    documento_ref: str
    fecha: date
    utilidad_bruta_valor: Decimal
    
    class Config:
        json_encoders = {Decimal: str}

class RentabilidadProductoItem(BaseModel):
    producto_id: int
    producto_codigo: str
    producto_nombre: str
    fecha_inicio_periodo: date
    fecha_fin_periodo: date
    total_venta: float = Field(default=0.0)
    total_costo: float = Field(default=0.0)
    total_utilidad: float = Field(default=0.0)
    margen_rentabilidad_porcentaje: float = Field(default=0.0)
    
    # --- CAMPO RENOMBRADO: TRAZABILIDAD COMPLETA ---
    trazabilidad_documentos: List[TopDocumentoTrazabilidad] = Field(default_factory=list)

    class Config:
        from_attributes = True

class RentabilidadTotales(BaseModel):
    total_venta_general: float = Field(default=0.0)
    total_costo_general: float = Field(default=0.0)
    total_utilidad_general: float = Field(default=0.0)
    margen_general_porcentaje: float = Field(default=0.0)

class RentabilidadProductoResponse(BaseModel):
    items: List[RentabilidadProductoItem] = []
    totales: RentabilidadTotales

    class Config:
        from_attributes = True

class RentabilidadProductoFiltros(BaseModel):
    # --- FILTROS DE PRODUCTO Y TIEMPO (EXISTENTES) ---
    grupo_ids: Optional[List[int]] = None
    producto_id: Optional[int] = None 
    producto_ids: Optional[List[int]] = None 
    fecha_inicio: date
    fecha_fin: date
    
    # --- NUEVOS FILTROS DE INTELIGENCIA DE NEGOCIO ---
    tercero_ids: Optional[List[int]] = None       # Nuevo: Filtrar por Cliente/Tercero 
    lista_precio_ids: Optional[List[int]] = None  # Nuevo: Filtrar por Lista de Precios 
    margen_minimo_porcentaje: Optional[float] = None # Nuevo: 'Mostrar solo margen > X%' 
    mostrar_solo_perdidas: Optional[bool] = False    # Nuevo: 'Mostrar solo pérdidas'