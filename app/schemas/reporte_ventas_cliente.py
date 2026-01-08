from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from decimal import Decimal

# --- FILTROS ---
class ReporteVentasClienteFiltros(BaseModel):
    fecha_inicio: date
    fecha_fin: date
    tercero_ids: Optional[List[int]] = None       # Filtro de Clientes
    producto_ids: Optional[List[int]] = None      # Filtro de Productos Específicos
    grupo_ids: Optional[List[int]] = None         # Filtro de Grupos de Inventario
    tipo_documento_ids: Optional[List[int]] = None # Filtro Tipo Doc (ej. Solo FV)
    clientes_expandidos: Optional[List[int]] = []  # IDs de clientes expandidos en UI para el PDF WYSIWYG

# --- DETALLES (Drill-down) ---

class VentaClienteDetalleProducto(BaseModel):
    producto_id: int
    producto_codigo: str
    producto_nombre: str
    cantidad: float
    total_venta: float
    total_costo: float
    utilidad: float
    margen: float

class VentaClienteDetalleDocumento(BaseModel):
    documento_id: int
    documento_ref: str # Tipo - Numero
    fecha: date
    total_venta: float
    total_costo: float
    utilidad: float
    margen: float

# --- ITEM PRINCIPAL (Resumen por Cliente) ---
class VentaClienteItem(BaseModel):
    tercero_id: int
    tercero_nombre: str
    tercero_identificacion: str
    
    # Métricas de Rentabilidad
    total_venta: float = Field(default=0.0)
    total_costo: float = Field(default=0.0)
    total_utilidad: float = Field(default=0.0)
    margen_porcentaje: float = Field(default=0.0)
    
    cantidad_items: float = Field(default=0.0) # Total unidades vendidas
    conteo_documentos: int = Field(default=0)  # Cuántas facturas
    
    # Detalles (opcionales, se cargan si se piden)
    detalle_productos: List[VentaClienteDetalleProducto] = []
    detalle_documentos: List[VentaClienteDetalleDocumento] = []

    class Config:
        from_attributes = True

# --- RESPUESTA GLOBAL ---
class ReporteVentasClienteResponse(BaseModel):
    items: List[VentaClienteItem] = []
    
    # Totales Globales
    gran_total_venta: float = 0.0
    gran_total_costo: float = 0.0
    gran_total_utilidad: float = 0.0
    margen_global_porcentaje: float = 0.0

    class Config:
        from_attributes = True
