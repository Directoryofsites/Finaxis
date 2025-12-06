from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from decimal import Decimal # Importar Decimal para precisión financiera

# =================================================================================
# === ESQUEMAS PARA REPORTE DE FACTURACIÓN (EXISTENTE) ===
# =================================================================================

class ReporteFacturacionFiltros(BaseModel):
    fecha_inicio: date
    fecha_fin: date
    tercero_id: Optional[int] = None
    centro_costo_id: Optional[int] = None
    # Añadimos un campo para el tipo de reporte: 'ventas' o 'compras'
    tipo_reporte: str

class ReporteFacturacionItem(BaseModel):
    # Datos del Documento
    documento_id: int
    fecha: date
    documento_ref: str
    tercero_nombre: str
    
    # Datos del Producto
    producto_codigo: str
    producto_nombre: str
    cantidad: float
    
    # Valores (dependerá si es venta o compra)
    valor_unitario: float
    valor_total_linea: float
    
    # Rentabilidad (solo para ventas)
    costo_unitario: Optional[float] = None
    costo_total_linea: Optional[float] = None
    utilidad_bruta_valor: Optional[float] = None
    utilidad_bruta_porcentaje: Optional[float] = None

class ReporteFacturacionKPIs(BaseModel):
    total_valor: float  # Total facturado o comprado
    total_base: float
    total_impuestos: float
    numero_facturas: int
    promedio_por_factura: float
    
    # Rentabilidad (solo para ventas)
    total_costo: Optional[float] = None
    utilidad_bruta_valor_total: Optional[float] = None
    utilidad_bruta_porcentaje_promedio: Optional[float] = None

class ReporteFacturacionResponse(BaseModel):
    data: List[ReporteFacturacionItem]
    kpis: ReporteFacturacionKPIs

# --- ESQUEMA FALTANTE PARA LEGACY JWT ---
class PDFTokenResponse(BaseModel):
    url_pdf: str

# =================================================================================
# === NUEVOS ESQUEMAS PARA RENTABILIDAD POR DOCUMENTO (IMPLEMENTACIÓN) ===
# =================================================================================

class ReporteRentabilidadDocumentoFiltros(BaseModel):
    """Esquema de filtros para obtener la rentabilidad de un solo documento. Acepta el CÓDIGO."""
    # FIX CLAVE: Cambiado de tipo_documento_id: int a tipo_documento_codigo: str
    tipo_documento_codigo: str 
    numero_documento: str # Se usa str para ser flexible con prefijos o formatos de número

class ReporteRentabilidadDocumentoItem(BaseModel):
    """Detalle línea por línea de la rentabilidad dentro de un documento."""
    # Información básica de la línea
    linea_documento_id: int
    
    # Datos del Producto
    producto_codigo: str
    producto_nombre: str
    
    # Métricas de la línea
    cantidad: Decimal
    valor_venta_unitario: Decimal
    valor_venta_total: Decimal
    costo_unitario: Decimal
    costo_total: Decimal
    
    # Rentabilidad
    utilidad_bruta_valor: Decimal
    utilidad_bruta_porcentaje: Decimal

    class Config:
        """Configuración para usar la clase Decimal de Python."""
        json_encoders = {Decimal: str}

class ReporteRentabilidadDocumentoTotales(BaseModel):
    """Totales acumulados del documento."""
    total_venta: Decimal
    total_costo: Decimal
    total_utilidad_bruta_valor: Decimal
    total_utilidad_bruta_porcentaje: Decimal

    class Config:
        """Configuración para usar la clase Decimal de Python."""
        json_encoders = {Decimal: str}

class ReporteRentabilidadDocumentoResponse(BaseModel):
    """Estructura de la respuesta del reporte de rentabilidad por documento."""
    documento_id: int
    documento_ref: str
    fecha: date
    tercero_nombre: str
    # --- NUEVO CAMPO AGREGADO ---
    tercero_nit: Optional[str] = None 
    # ----------------------------
    
    detalle: List[ReporteRentabilidadDocumentoItem]
    totales: ReporteRentabilidadDocumentoTotales

    class Config:
        """Configuración para usar la clase Decimal de Python."""
        json_encoders = {Decimal: str}