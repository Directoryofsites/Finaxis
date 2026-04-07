# app/schemas/gestion_ventas.py

from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class GestionVentasFiltros(BaseModel):
    """Define los filtros para el reporte de gestión de ventas."""
    fecha_inicio: date
    fecha_fin: date
    cliente_id: Optional[int] = None
    estado: Optional[str] = None # 'Pagada', 'Pendiente', 'Vencida', 'Anulada'

class GestionVentasItem(BaseModel):
    """Define la estructura de una fila (una factura) en el reporte."""
    id: int
    fecha: date
    tipo_documento: str
    numero: int
    beneficiario_nombre: str
    fecha_vencimiento: Optional[date]
    estado: str
    total: float
    saldo_pendiente: float
    
    class Config:
        from_attributes = True

class GestionVentasKPIs(BaseModel):
    """Define la estructura para los indicadores clave de rendimiento."""
    total_facturado: float
    total_utilidad: float
    margen_promedio: float
    cantidad_facturas: int
    ticket_promedio: float
    total_cobrado: float
    saldo_pendiente: float
    cartera_vencida: float

class ChartDataPoint(BaseModel):
    """Punto de datos para gráficas (ej: ventas por día)."""
    label: str
    value: float

class GestionVentasGraficos(BaseModel):
    """Estructura para los datos de gráficas del dashboard."""
    ventas_por_dia: List[ChartDataPoint]
    top_clientes: List[ChartDataPoint]
    top_productos: List[ChartDataPoint]

class GestionVentasResponse(BaseModel):
    """El objeto completo de respuesta de la API."""
    kpis: GestionVentasKPIs
    graficos: GestionVentasGraficos
    items: List[GestionVentasItem]

# --- INICIO DE NUEVAS CLASES PARA EL PDF ---

class GestionVentasPDFPayload(BaseModel):
    """
    Define el payload que se codificará en el token JWT para la impresión del PDF.
    Contiene los filtros y el ID de la empresa para seguridad.
    """
    filtros: GestionVentasFiltros
    emp_id: int
    user_id: int

class GestionVentasSignedURLResponse(BaseModel):
    """
    Define la respuesta que el servidor enviará al frontend con la URL firmada.
    """
    signed_url: str

# --- FIN DE NUEVAS CLASES PARA EL PDF ---