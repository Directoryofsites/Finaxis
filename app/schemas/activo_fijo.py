from typing import Optional, List
from datetime import date
from pydantic import BaseModel
from decimal import Decimal
from .tercero import Tercero
from .centro_costo import CentroCosto
from enum import Enum

# --- ENUMS REPLICADOS ---
class MetodoDepreciacion(str, Enum):
    LINEA_RECTA = "LINEA_RECTA"
    REDUCCION_SALDOS = "REDUCCION_SALDOS"
    UNIDADES_PRODUCCION = "UNIDADES_PRODUCCION"
    NO_DEPRECIAR = "NO_DEPRECIAR"

class EstadoActivo(str, Enum):
    ACTIVO = "ACTIVO"
    EN_MANTENIMIENTO = "EN_MANTENIMIENTO"
    BAJA_PENDIENTE = "BAJA_PENDIENTE"
    BAJA_DEFINITIVA = "BAJA_DEFINITIVA"
    TOT_DEPRECIADO = "TOT_DEPRECIADO"

# --- CATEGORIAS ---
class ActivoCategoriaBase(BaseModel):
    nombre: str
    vida_util_niif_meses: int
    vida_util_fiscal_meses: int
    metodo_depreciacion: MetodoDepreciacion
    cuenta_activo_id: Optional[int] = None
    cuenta_gasto_depreciacion_id: Optional[int] = None
    cuenta_depreciacion_acumulada_id: Optional[int] = None

class ActivoCategoriaCreate(ActivoCategoriaBase):
    pass

class ActivoCategoria(ActivoCategoriaBase):
    id: int
    empresa_id: int

    class Config:
        from_attributes = True

# --- ACTIVOS FIJOS ---
class ActivoFijoBase(BaseModel):
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    serial: Optional[str] = None
    modelo: Optional[str] = None
    marca: Optional[str] = None
    categoria_id: int
    
    ubicacion: Optional[str] = None
    responsable_id: Optional[int] = None
    centro_costo_id: Optional[int] = None
    
    fecha_compra: date
    fecha_inicio_uso: Optional[date] = None
    proveedor_id: Optional[int] = None
    numero_factura: Optional[str] = None
    
    costo_adquisicion: Decimal
    valor_residual: Decimal = Decimal(0)
    
    estado: EstadoActivo = EstadoActivo.ACTIVO

class ActivoFijoCreate(ActivoFijoBase):
    pass

class ActivoFijoUpdate(BaseModel):
    nombre: Optional[str] = None
    ubicacion: Optional[str] = None
    responsable_id: Optional[int] = None
    estado: Optional[EstadoActivo] = None
    # No permitimos cambiar costos o fechas contables fácilmente en un Update simple

class ActivoFijo(ActivoFijoBase):
    id: int
    empresa_id: int
    depreciacion_acumulada_niif: Decimal
    depreciacion_acumulada_fiscal: Decimal
    
    categoria: Optional[ActivoCategoria] = None
    responsable: Optional[Tercero] = None
    proveedor: Optional[Tercero] = None
    # centro_costo: Optional[CentroCosto] = None # Descomentar si se requiere expandir

    class Config:
        from_attributes = True

# --- NOVEDADES ---
class ActivoNovedadBase(BaseModel):
    tipo: str
    fecha: date
    valor: Decimal
    observacion: Optional[str] = None
    detalles: Optional[dict] = None

class ActivoNovedad(ActivoNovedadBase):
    id: int
    activo_id: int
    created_by: Optional[int] = None

    class Config:
        from_attributes = True
