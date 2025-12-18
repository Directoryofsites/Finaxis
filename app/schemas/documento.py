from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict, Union
from datetime import date, datetime
from decimal import Decimal
from .aplicacion_pago import AplicacionPagoCreate

# --- INICIO: NUEVO SCHEMA DE VISTA (VERSIÓN CONSOLIDADA) ---
# Este es nuestro nuevo "Contrato de Vista". Define la forma exacta de los datos
# que el frontend necesita para mostrar el detalle de productos en una factura.

class DetalleProductoVendido(BaseModel):
    # --- Datos de Venta (Existentes) ---
    producto_id: int
    nombre_producto: str
    cantidad: float
    precio_unitario: float = Field(..., alias="vrUnitario")
    total_linea: float = Field(..., alias="totalLinea")

    # --- NUEVOS CAMPOS DE RENTABILIDAD ---
    costo_unitario: float = Field(..., alias="costoUnitario")
    costo_total: float = Field(..., alias="costoTotal")
    utilidad_bruta: float = Field(..., alias="utilidadBruta")
    margen_rentabilidad: float = Field(..., alias="margenRentabilidad")

    class Config:
        from_attributes = True
        populate_by_name = True
        
# --- FIN: NUEVO SCHEMA DE VISTA ---


# --- Esquemas para los Movimientos (sin cambios) ---
class MovimientoContableBase(BaseModel):
    cuenta_id: int
    centro_costo_id: Optional[int] = None
    concepto: Optional[str] = None
    debito: Decimal = Field(default=0, ge=0)
    credito: Decimal = Field(default=0, ge=0)
    producto_id: Optional[int] = None
    cantidad: Optional[float] = None

class MovimientoContableCreate(MovimientoContableBase):
    pass

class MovimientoContable(MovimientoContableBase):
    id: int
    documento_id: int
    producto_codigo: Optional[str] = None
    producto_nombre: Optional[str] = None
    class Config:
        from_attributes = True

# --- Esquemas para el Documento ---
class DocumentoBase(BaseModel):
    fecha: date
    tipo_documento_id: int
    numero: Optional[int] = None
    beneficiario_id: Optional[int] = None
    centro_costo_id: Optional[int] = None
    fecha_vencimiento: Optional[date] = None
    unidad_ph_id: Optional[int] = None # Added for PH Module

class DocumentoCreate(DocumentoBase):
    empresa_id: Optional[int] = None
    movimientos: List[MovimientoContableCreate]
    aplicaciones: Optional[List[AplicacionPagoCreate]] = None

# --- INICIO: MODIFICACIÓN CRÍTICA EN EL SCHEMA 'Documento' ---
class Documento(DocumentoBase):
    id: int
    empresa_id: int
    anulado: bool
    estado: str
    usuario_creador_id: Optional[int] = None
    
    # En lugar de solo los movimientos crudos, ahora exponemos nuestro nuevo contrato.
    detalle_productos: Optional[List[DetalleProductoVendido]] = []
    
    # Mantenemos los movimientos para otros usos, pero la vista principal usará el de arriba.
    movimientos: List[MovimientoContable] = []

    class Config:
        from_attributes = True
# --- FIN: MODIFICACIÓN CRÍTICA EN EL SCHEMA 'Documento' ---


# El resto de los schemas no necesitan cambios
class DocumentoAnulacion(BaseModel):
    razon: str = Field(min_length=5, max_length=500)

class DocumentoUpdate(DocumentoBase):
    movimientos: List[MovimientoContableCreate]
    aplicaciones: Optional[List[AplicacionPagoCreate]] = None

class DocumentoEnLista(BaseModel):
    id: int
    fecha: date
    numero: int
    anulado: bool
    tipo_documento_nombre: str
    tercero_nombre: Optional[str] = None
    total_debito: Decimal
    class Config:
        from_attributes = True

class ListaDocumentosResponse(BaseModel):
    total: int
    documentos: List[DocumentoEnLista]

class DocumentoFiltros(BaseModel):
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    tipo_documento_id: Optional[int] = None
    tercero_id: Optional[int] = None
    estado: Optional[str] = None
    numero: Optional[str] = None
    concepto: Optional[str] = None

class DocumentoGestionFiltros(BaseModel):
    tipoEntidad: str
    estadoDocumento: Optional[str] = None
    incluirAnulados: Optional[bool] = False
    fechaInicio: Optional[date] = None
    fechaFin: Optional[date] = None
    tipoDocIds: Optional[List[int]] = None # Antes tipoDocId
    numero: Optional[str] = None
    terceroIds: Optional[List[int]] = None # Antes terceroId
    cuentaIds: Optional[List[int]] = None # Antes cuentaId
    centroCostoIds: Optional[List[int]] = None # Antes centroCostoId
    productoIds: Optional[List[int]] = None # NUEVO: Filtro por Productos
    conceptoKeyword: Optional[str] = None
    valorOperador: Optional[str] = None
    valorMonto: Optional[Decimal] = None
    traerTodo: bool = False
    terceroKeyword: Optional[str] = None
    esCliente: Optional[bool] = None
    esProveedor: Optional[bool] = None
    cuentaCodigoKeyword: Optional[str] = None
    cuentaNivel: Optional[int] = None
    permiteMovimiento: Optional[bool] = None
    pagina: int = Field(1, ge=1)
    limite: int = Field(50, ge=1, le=100)

class DocumentoGestionResult(BaseModel):
    id: int
    fecha: date
    tipo_documento: str
    numero: int
    beneficiario: Optional[str] = None
    total: Decimal
    anulado: bool
    estado: str
    class Config:
        from_attributes = True

class DocumentoAccionMasivaPayload(BaseModel):
    documentoIds: List[int]
    razon: str = Field(min_length=5)

class SuperInformeResponse(BaseModel):
    total_registros: int
    total_paginas: int
    pagina_actual: int
    resultados: List[Dict[str, Any]]

class DocumentoAnuladoResult(BaseModel):
    id: int
    fecha: date
    tipo_documento: str
    numero: int
    beneficiario: Optional[str] = None
    total: Decimal
    class Config:
        from_attributes = True

class AuditoriaConsecutivoItem(BaseModel):
    estado: str
    numero: int
    fecha_documento: Optional[date] = None
    fecha_operacion: Optional[datetime] = None
    beneficiario_nombre: Optional[str] = None
    total_documento: Optional[Decimal] = None
    usuario_operacion: Optional[str] = None
    razon_operacion: Optional[str] = None
    class Config:
        from_attributes = True

class AuditoriaConsecutivoGap(BaseModel):
    estado: str = Field("HUECO", literal=True)
    numero_faltante_inicio: int
    numero_faltante_fin: int
    cantidad_faltante: int

AuditoriaConsecutivoRow = Union[AuditoriaConsecutivoItem, AuditoriaConsecutivoGap]

class AuditoriaConsecutivosResponse(BaseModel):
    tipo_documento_nombre: str
    ultimo_consecutivo_registrado: int
    total_documentos_encontrados: int
    total_huecos_encontrados: int
    resultados: List[AuditoriaConsecutivoRow]

class PapeleraItem(BaseModel):
    id: int
    id_original: int
    numero: str
    fecha: date
    fecha_eliminacion: datetime
    usuario_eliminacion: Optional[str] = "N/A"
    tipo_documento_nombre: str
    valor_documento: Decimal
    class Config:
        from_attributes = True