# app/schemas/reportes_inventario.py

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any 
from datetime import date, datetime
from enum import Enum 

# ========== Schemas Existentes ==========

class ReporteInventarioFiltros(BaseModel):
    fecha_inicio: date
    fecha_fin: date
    bodega_id: Optional[int] = None
    grupo_id: Optional[int] = None

class ReporteInventarioItem(BaseModel):
    producto_id: int
    producto_codigo: str
    producto_nombre: str
    saldo_inicial_cantidad: float
    saldo_inicial_valor: float
    entradas_cantidad: float
    entradas_valor: float
    salidas_cantidad: float
    salidas_valor: float
    saldo_final_cantidad: float
    saldo_final_valor: float
    model_config = ConfigDict(from_attributes=True)

class ReporteInventarioResponse(BaseModel):
    items: List[ReporteInventarioItem]
    totales: dict
    model_config = ConfigDict(from_attributes=True)

class KardexItem(BaseModel):
    id: int
    fecha: datetime
    documento_ref: Optional[str] = "N/A"
    tipo_movimiento: str
    bodega_nombre: Optional[str] = None
    entrada_cantidad: Optional[float] = None
    entrada_costo_unit: Optional[float] = None
    salida_cantidad: Optional[float] = None
    salida_costo_unit: Optional[float] = None
    salida_costo_total: Optional[float] = None
    saldo_cantidad: float
    saldo_costo_promedio: float
    saldo_valor_total: float
    model_config = ConfigDict(from_attributes=True)

class KardexTotales(BaseModel):
    """Totales consolidados para el reporte Kardex."""
    saldo_inicial_cantidad: float = 0.0
    saldo_inicial_valor: float = 0.0
    total_entradas_cantidad: float = 0.0
    total_entradas_valor: float = 0.0
    total_salidas_cantidad: float = 0.0
    total_salidas_valor: float = 0.0
    saldo_final_cantidad: float = 0.0
    saldo_final_valor: float = 0.0
    bodega_nombre: Optional[str] = None 
    
    model_config = ConfigDict(from_attributes=True)

class KardexResponse(BaseModel):
    items: List[KardexItem]
    producto_nombre: str
    producto_codigo: str
    totales: "KardexTotales" 
    model_config = ConfigDict(from_attributes=True)

class KardexFiltrosPDF(BaseModel):
    producto_id: int
    fecha_inicio: date
    fecha_fin: date
    bodega_id: Optional[int] = None

# --- Schemas para el Reporte Analítico (CORREGIDO) ---
class ReporteAnaliticoFiltros(BaseModel):
    fecha_inicio: date
    fecha_fin: date
    
    # FIX: Se mantienen los singulares por retrocompatibilidad, pero se añaden los plurales
    bodega_id: Optional[int] = None
    grupo_id: Optional[int] = None
    
    # FIX CRÍTICO: Soporte para listas (requerido por el servicio)
    bodega_ids: Optional[List[int]] = None
    grupo_ids: Optional[List[int]] = None
    
    producto_id: Optional[int] = None
    # FIX: Añadimos producto_ids para consistencia
    producto_ids: Optional[List[int]] = None
    
    vista_por_valor: bool = False
    search_term: Optional[str] = None
    # FIX: Soporte para el nuevo nombre del filtro de búsqueda
    search_term_prod: Optional[str] = None

class ReporteAnaliticoItem(BaseModel):
    producto_id: int
    producto_codigo: str
    producto_nombre: str
    
    saldo_inicial_cantidad: float
    saldo_inicial_valor: float
    
    total_entradas_cantidad: Optional[float] = 0.0
    total_salidas_cantidad: Optional[float] = 0.0
    total_entradas_valor: Optional[float] = 0.0
    total_salidas_valor: Optional[float] = 0.0
    
    saldo_final_cantidad: float
    saldo_final_valor: float
    model_config = ConfigDict(from_attributes=True)

class ReporteAnaliticoResponse(BaseModel):
    items: List[ReporteAnaliticoItem]
    totales: dict
    model_config = ConfigDict(from_attributes=True)

# ========== NUEVOS Schemas para el Super Informe de Inventarios ==========

class VistaSuperInformeEnum(str, Enum):
    """Define las posibles vistas del Super Informe."""
    MOVIMIENTOS = "MOVIMIENTOS"
    ESTADO_GENERAL = "ESTADO_GENERAL"
    RENTABILIDAD = "RENTABILIDAD"

class SuperInformeFiltros(BaseModel):
    """Schema completo para los filtros del Super Informe de Inventarios."""
    vista_reporte: VistaSuperInformeEnum = VistaSuperInformeEnum.ESTADO_GENERAL

    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    bodega_ids: Optional[List[int]] = None
    grupo_ids: Optional[List[int]] = None
    producto_ids: Optional[List[int]] = None
    tercero_id: Optional[int] = None 
    cuenta_id: Optional[int] = None 
    centro_costo_id: Optional[int] = None 
    search_term_doc: Optional[str] = None 
    search_term_prod: Optional[str] = None 

    lista_precio_id: Optional[int] = None
    caracteristicas: Optional[Dict[str, str]] = None
    filtro_topes: Optional[str] = None
    es_servicio: Optional[bool] = None 

    valor_operador: Optional[str] = Field(None, pattern="^(mayor|menor|igual)$")
    valor_monto: Optional[float] = None

    pagina: int = Field(1, ge=1)
    traerTodo: bool = False

    vista_por_valor: bool = False


# --- Schemas para los Items de Respuesta (según la vista) ---

class SuperInformeItemMovimiento(BaseModel):
    movimiento_id: int
    fecha: datetime
    documento_ref: Optional[str] = None
    tipo_documento_codigo: Optional[str] = None
    tercero_nombre: Optional[str] = None
    bodega_nombre: str
    producto_codigo: str
    producto_nombre: str
    tipo_movimiento: str 
    cantidad: float
    costo_unitario: float
    costo_total: float
    model_config = ConfigDict(from_attributes=True)

SuperInformeItemEstado = ReporteAnaliticoItem

from ..schemas.reporte_rentabilidad import RentabilidadProductoItem as SuperInformeItemRentabilidad

# --- Schema para la Paginación ---
class SuperInformePaginacion(BaseModel):
    total_registros: int
    total_paginas: int
    pagina_actual: int

# --- Schema para la Respuesta General ---
class SuperInformeResponse(BaseModel):
    items: List[Any] 
    totales: Optional[Dict[str, float]] = None
    paginacion: SuperInformePaginacion
    vista_reporte: VistaSuperInformeEnum 

    model_config = ConfigDict(from_attributes=True)

# ========== NUEVO SCHEMA PARA URL FIRMADA ==========
class PDFTokenResponse(BaseModel):
    token: str = Field(..., description="Token JWT firmado que contiene los filtros del reporte.")
    
# ========== NUEVOS SCHEMAS PARA REPORTE DE TOPES ==========

class ReporteTopesFiltros(BaseModel):
    fecha_corte: date = Field(..., description="Fecha hasta la cual se calcula el stock (saldo).")
    bodega_ids: Optional[List[int]] = Field(None, description="Lista de bodegas a incluir en el cálculo.")
    grupo_ids: Optional[List[int]] = None
    tipo_alerta: str = Field("MINIMO", pattern="^(MINIMO|MAXIMO|TODOS)$") 

class ReporteTopesItem(BaseModel):
    producto_id: int
    producto_codigo: str
    producto_nombre: str
    stock_minimo: float
    stock_maximo: float
    saldo_actual: float
    bodega_nombre: str
    estado_tope: str
    diferencia: float = Field(..., description="Cantidad que falta o sobra para llegar al tope.")
    model_config = ConfigDict(from_attributes=True)

class ReporteTopesResponse(BaseModel):
    items: List[ReporteTopesItem]
    totales_topes: Dict[str, int] = Field(..., description="Conteo total de productos en cada estado.")

# Finalizar forward references
KardexResponse.model_rebuild()