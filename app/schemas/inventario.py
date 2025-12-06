# app/schemas/inventario.py (VERSIÓN CORREGIDA: VISIBILIDAD CUENTAS IMPUESTOS + FIX GRUPO_IDS)

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import date, datetime

# ========== Schemas para Bodegas (sin cambios) ==========
class BodegaBase(BaseModel):
    nombre: str

class BodegaCreate(BodegaBase):
    pass

class BodegaUpdate(BodegaBase):
    nombre: Optional[str] = None

class Bodega(BodegaBase):
    id: int
    empresa_id: int
    model_config = ConfigDict(from_attributes=True)


# ========== Schemas para Grupos de Inventario (Adaptados) ==========
class GrupoInventarioBase(BaseModel):
    nombre: str
    cuenta_inventario_id: Optional[int] = None
    cuenta_ingreso_id: Optional[int] = None
    cuenta_costo_venta_id: Optional[int] = None
    cuenta_ajuste_faltante_id: Optional[int] = None
    cuenta_ajuste_sobrante_id: Optional[int] = None

class GrupoInventarioCreate(GrupoInventarioBase):
    pass

class GrupoInventarioUpdate(GrupoInventarioBase):
    nombre: Optional[str] = None
    cuenta_inventario_id: Optional[int] = None
    cuenta_ingreso_id: Optional[int] = None
    cuenta_costo_venta_id: Optional[int] = None
    cuenta_ajuste_faltante_id: Optional[int] = None
    cuenta_ajuste_sobrante_id: Optional[int] = None

class GrupoInventarioSimple(BaseModel):
    id: int
    nombre: str
    model_config = ConfigDict(from_attributes=True)

# --- Schemas para Definiciones de Características ---
class CaracteristicaDefinicionBase(BaseModel):
    nombre: str = Field(..., max_length=100)
    es_unidad_medida: Optional[bool] = False

class CaracteristicaDefinicionCreate(CaracteristicaDefinicionBase):
    pass

class CaracteristicaDefinicionUpdate(CaracteristicaDefinicionBase):
    nombre: Optional[str] = Field(None, max_length=100)
    es_unidad_medida: Optional[bool] = None

class CaracteristicaDefinicion(CaracteristicaDefinicionBase):
    id: int
    grupo_inventario_id: int
    model_config = ConfigDict(from_attributes=True)

# --- Schemas para Reglas de Precio por Grupo ---
class ReglaPrecioGrupoBase(BaseModel):
    lista_precio_id: int
    porcentaje_incremento: float = Field(default=0.0)

class ReglaPrecioGrupoCreate(ReglaPrecioGrupoBase):
    pass

class ReglaPrecioGrupoUpdate(ReglaPrecioGrupoBase):
    lista_precio_id: Optional[int] = None
    porcentaje_incremento: Optional[float] = None

# Forward reference para ListaPrecio dentro de ReglaPrecioGrupo
class ListaPrecio(BaseModel): # Definición mínima para el forward reference
    id: int
    nombre: str
    model_config = ConfigDict(from_attributes=True)

class ReglaPrecioGrupo(ReglaPrecioGrupoBase):
    id: int
    grupo_inventario_id: int
    lista_precio: ListaPrecio # Incluir datos de la lista
    model_config = ConfigDict(from_attributes=True)

# --- Schema completo para GrupoInventario (incluyendo relaciones) ---
class GrupoInventario(GrupoInventarioBase):
    id: int
    empresa_id: int
    caracteristicas_definidas: List[CaracteristicaDefinicion] = []
    reglas_precio: List[ReglaPrecioGrupo] = []
    model_config = ConfigDict(from_attributes=True)


# --- Schemas para Valores de Características por Producto ---
class CaracteristicaValorProductoBase(BaseModel):
    definicion_id: int
    valor: Optional[str] = Field(None, max_length=255)

class CaracteristicaValorProductoCreate(CaracteristicaValorProductoBase):
    pass

class CaracteristicaValorProductoUpdate(CaracteristicaValorProductoBase):
    pass # No se actualiza individualmente

class CaracteristicaValorProducto(CaracteristicaValorProductoBase):
    id: int
    producto_id: int
    definicion: CaracteristicaDefinicion # Incluir la definición
    model_config = ConfigDict(from_attributes=True)


# --- Schemas para Listas de Precios ---
class ListaPrecioBase(BaseModel):
    nombre: str = Field(..., max_length=100)

class ListaPrecioCreate(ListaPrecioBase):
    pass

class ListaPrecioUpdate(ListaPrecioBase):
    nombre: Optional[str] = Field(None, max_length=100)

# Re-definición completa de ListaPrecio aquí para evitar problemas de orden
class ListaPrecio(ListaPrecioBase):
    id: int
    empresa_id: int
    model_config = ConfigDict(from_attributes=True)


# ========== Schemas para Tasas de Impuesto (CORREGIDO) ==========
class TasaImpuestoBase(BaseModel):
    nombre: str
    tasa: float = Field(..., ge=0, le=1)
    # --- CORRECCIÓN: Campos de cuenta agregados para visibilidad y guardado ---
    cuenta_id: Optional[int] = None # Cuenta IVA Generado
    cuenta_iva_descontable_id: Optional[int] = None # Cuenta IVA Descontable

class TasaImpuestoCreate(TasaImpuestoBase):
    pass

class TasaImpuestoUpdate(TasaImpuestoBase):
    nombre: Optional[str] = None
    tasa: Optional[float] = Field(None, ge=0, le=1)
    # --- CORRECCIÓN: Campos agregados para permitir actualización ---
    cuenta_id: Optional[int] = None
    cuenta_iva_descontable_id: Optional[int] = None

class TasaImpuesto(TasaImpuestoBase):
    id: int
    empresa_id: int
    model_config = ConfigDict(from_attributes=True)


# ========== Schemas para Productos (Adaptados) ==========

class ProductoBase(BaseModel):
    codigo: str = Field(..., max_length=50)
    nombre: str = Field(..., max_length=255)
    es_servicio: bool = False
    grupo_id: Optional[int] = None
    impuesto_iva_id: Optional[int] = None
    precio_base_manual: Optional[float] = Field(None, ge=0)
    stock_minimo: Optional[float] = Field(0.0, ge=0)
    stock_maximo: Optional[float] = Field(0.0, ge=0)
    # >>> FIX CRÍTICO 1/2: Añadir metodo_costeo al schema para garantizar que se envíe
    metodo_costeo: str = Field('promedio_ponderado', max_length=50)
    # <<< FIN FIX CRÍTICO


class ProductoCreate(ProductoBase):
    costo_inicial: Optional[float] = Field(0.0, ge=0)
    stock_inicial: Optional[float] = Field(0.0, ge=0)
    bodega_id_inicial: Optional[int] = None
    valores_caracteristicas: List[CaracteristicaValorProductoCreate] = []

class ProductoUpdate(ProductoBase):
    codigo: Optional[str] = Field(None, max_length=50)
    nombre: Optional[str] = Field(None, max_length=255)
    es_servicio: Optional[bool] = None
    grupo_id: Optional[int] = None
    impuesto_iva_id: Optional[int] = None
    precio_base_manual: Optional[float] = Field(None, ge=0)
    stock_minimo: Optional[float] = Field(None, ge=0)
    stock_maximo: Optional[float] = Field(None, ge=0)
    valores_caracteristicas: Optional[List[CaracteristicaValorProductoCreate]] = None

# --- Schema para Stock por Bodega ---
class StockBodegaBase(BaseModel):
    producto_id: int
    bodega_id: int
    stock_actual: float

class StockBodega(StockBodegaBase):
    id: int
    bodega: Optional[Bodega] = None
    model_config = ConfigDict(from_attributes=True)

# --- Schema para lectura detallada de Producto ---
class Producto(ProductoBase):
    id: int
    empresa_id: int
    costo_promedio: float
    fecha_creacion: datetime
    grupo_inventario: Optional[GrupoInventarioSimple] = None
    impuesto_iva: Optional[TasaImpuesto] = None
    valores_caracteristicas: List[CaracteristicaValorProducto] = []
    stocks_bodega: List[StockBodega] = []
    stock_total_calculado: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)


# --- Schema para Autocompletar Producto ---
class ProductoAutocompleteItem(BaseModel):
    id: int
    codigo: str
    nombre: str
    es_servicio: bool
    costo_promedio: float
    stock_actual: float # Stock total, no por bodega
    precio_base_manual: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)


class ProductoSimple(BaseModel):
    id: int
    codigo: str
    nombre: str
    model_config = ConfigDict(from_attributes=True)


# --- Schema para Filtros de Búsqueda de Productos (FIX CRÍTICO) ---
class ProductoFiltros(BaseModel):
    # FIX CRÍTICO: Eliminamos grupo_id singular y lo reemplazamos por grupo_ids plural
    grupo_ids: Optional[List[int]] = None # <--- Acepta múltiples IDs de grupo
    bodega_ids: Optional[List[int]] = None
    search_term: Optional[str] = None
    producto_id: Optional[int] = None
    # >>> FIX CRÍTICO 2/2: Eliminamos model_config(extra='ignore') para simplificar la validación
    # Esto a veces soluciona problemas de Pydantic con Optional en ciertos entornos
    # model_config = ConfigDict(extra='ignore') 
    # <<< FIN FIX CRÍTICO


# ========== Schemas para Ajuste de Inventario (sin cambios) ==========
class AjusteInventarioItemCreate(BaseModel):
    producto_id: int
    diferencia: float
    costo_promedio: float # Se envía desde el frontend para auditoría

class AjusteInventarioCreate(BaseModel):
    fecha: date
    concepto: str
    bodega_id: int
    items: List[AjusteInventarioItemCreate]

# --- INICIO NUEVO SCHEMA ---
class PrecioVentaCalculado(BaseModel):
    """Schema simple para devolver el precio de venta calculado."""
    precio_calculado: float
# --- FIN NUEVO SCHEMA ---