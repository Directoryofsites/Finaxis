from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from typing import Literal
from datetime import date, datetime

class BusquedaInversaRequest(BaseModel):
    tipoBusqueda: str
    empresaId: int
    valor1: str
    valor2: Optional[str] = None

class BusquedaInversaResponse(BaseModel):
    id: int

class InspectorUniversalRequest(BaseModel):
    idToInspect: int

class InspectorUniversalResult(BaseModel):
    tabla_origen: str
    datos: Dict[str, Any]

# --- INICIO: SCHEMA ACTUALIZADO ---
class ConteoResult(BaseModel):
    empresa_id: int
    nombre_empresa: str
    nit: Optional[str] = None # Nuevo campo NIT
    total_registros: int
    limite_registros: Optional[int] = None
    bolsa_excedente_total: int = 0
    recargas_disponibles: int = 0
# --- FIN: SCHEMA ACTUALIZADO ---

class TiposDocumentoRequest(BaseModel):
    empresaId: int

class BusquedaUniversalFiltros(BaseModel):
    empresaId: int
    tipoDocId: int
    numero: str
    fechaInicio: Optional[date] = None
    fechaFin: Optional[date] = None

class BusquedaUniversalResult(BaseModel):
    id: int
    tipo_documento_id: int
    numero: int
    fecha: date
    estado: str
    detalle: str

class ErradicacionRequest(BaseModel):
    documentoIds: List[int]
    logIds: List[int]
    empresaId: int

# --- INICIO DE CAMBIOS ---

# Se añade 'usuarios' a la lista de entidades permitidas
TipoEntidadLiteral = Literal[
    'usuarios',
    'terceros', 
    'plan_cuentas', 
    'centros_costo', 
    'tipos_documento', 
    'plantillas_maestras', 
    'conceptos_favoritos'
]

class InspeccionRequest(BaseModel):
    empresa_id: int
    tipo_entidad: TipoEntidadLiteral

class Dependencia(BaseModel):
    tipo: str
    descripcion: str

class EntidadInspeccionada(BaseModel):
    id: int
    descripcion_principal: str
    descripcion_secundaria: Optional[str] = None
    email: Optional[str] = None # Se añade el campo email
    dependencias: List[Dependencia]

class ErradicacionMaestrosRequest(BaseModel):
    empresa_id: int
    tipo_entidad: TipoEntidadLiteral
    ids_a_erradicar: List[int]

# --- FIN DE CAMBIOS ---

# --- INICIO: BLOQUE CORREGIDO Y ALINEADO CON EL SERVICIO ---
# FIX CRÍTICO: Se añade 'inventario' al literal.
TipoEntidadUniversal = Literal[
    'movimientos_documentos',
    'auditoria_papelera',
    'plantillas_documentos',
    'conceptos_favoritos',
    'terceros',
    'plan_cuentas',
    'centros_costo',
    'tipos_documento',
    'formatos_impresion', 
    'inventario' # <--- FIX INYECTADO AQUÍ
]
# --- FIN: BLOQUE CORREGIDO ---

class ErradicacionUniversalRequest(BaseModel):
    empresa_id: int = Field(..., description="ID de la empresa a la que se aplicará la erradicación.")
    entidades_a_erradicar: List[TipoEntidadUniversal] = Field(..., description="Lista de los tipos de entidades a erradicar de la empresa.")
    confirmacion: bool = Field(..., description="Confirmación explícita del usuario.")

    # --- INICIO: NUEVOS SCHEMAS PARA MAESTROS DE SOPORTE ---

class SoporteEmpresa(BaseModel):
    """Define la estructura de una empresa para las listas de soporte."""
    id: int
    razon_social: str
    nit: str
    fecha_inicio_operaciones: Optional[date] = None # <--- LÍNEA AÑADIDA

    class Config:
        from_attributes = True

class MaestrosSoporteResponse(BaseModel):
    """Define la respuesta que contiene toda la data maestra para el panel de soporte."""
    empresas: List[SoporteEmpresa]

# --- FIN: NUEVOS SCHEMAS ---

# --- ESQUEMAS PARA EL NUEVO ERRADICADOR INTELIGENTE ---

class AnalisisErradicacionRequest(BaseModel):
    """
    Schema para la solicitud de análisis de dependencias.
    El frontend envía la lista de entidades que el usuario seleccionó.
    """
    empresa_id: int
    entidades_seleccionadas: List[str] # Usamos str por ahora para flexibilidad

class PasoEjecucion(BaseModel):
    """
    Define un único paso dentro del plan de erradicación.
    """
    paso: int
    titulo: str
    descripcion: str
    total_afectado: int

class PlanDeEjecucionResponse(BaseModel):
    """
    Schema para la respuesta del backend con el plan de ejecución completo.
    """
    plan: List[PasoEjecucion]
    entidades_a_erradicar: List[str] # La lista completa que se procesará

# --- INICIO: SCHEMAS PARA AUDITORÍA DE CONSECUTIVOS ---

class AuditoriaConsecutivosRequest(BaseModel):
    """
    Define los filtros para la herramienta de auditoría de consecutivos.
    Usado principalmente por el panel de soporte para seleccionar una empresa.
    """
    empresa_id: Optional[int] = None

class ConsecutivoInfo(BaseModel):
    """
    Define la estructura de datos de respuesta para un único tipo de documento
    en la auditoría de consecutivos.
    """
    tipo_documento_id: int
    nombre: str
    codigo: str
    consecutivo_actual_db: Optional[int] = None
    ultimo_numero_usado: Optional[int] = None
    total_documentos: int
    
    # Campos mejorados para resolver el bug y la nueva funcionalidad
    fecha_ultimo_uso: Optional[datetime] = None # Corresponde a la fecha de creación/operación
    fecha_doc_ultimo_uso: Optional[date] = None   # Corresponde a la fecha transaccional del documento
    
    class Config:
        from_attributes = True

# --- FIN: SCHEMAS PARA AUDITORÍA DE CONSECUTIVOS ---