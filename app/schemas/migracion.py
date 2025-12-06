from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date

# --- Esquemas para la Petición de EXPORTACIÓN (CORREGIDOS) ---

class ExportPaquetesMaestros(BaseModel):
    plan_cuentas: bool = False
    terceros: bool = False
    centros_costo: bool = False
    tipos_documento: bool = False
    # --- INICIO DE LA MODIFICACIÓN ---
    bodegas: bool = False
    grupos_inventario: bool = False
    tasas_impuesto: bool = False
    productos: bool = False
    # --- FIN DE LA MODIFICACIÓN ---

class ExportPaquetesConfiguraciones(BaseModel):
    plantillas_documentos: bool = False
    libreria_conceptos: bool = False

class ExportPaquetes(BaseModel):
    """ Define qué paquetes de datos se incluirán en la exportación. """
    maestros: ExportPaquetesMaestros
    transacciones: bool = False
    configuraciones: ExportPaquetesConfiguraciones

# --- Schema de Exportación Corregido ---
# Se elimina la anidación de 'filtros' y se añaden todos los campos del formulario.
# Se quita 'empresaId', ya que ahora se obtiene del token de seguridad.
class ExportRequest(BaseModel):
    """ El cuerpo completo de la petición de exportación, con estructura aplanada. """
    paquetes: ExportPaquetes

    # Filtros aplanados, todos opcionales para coincidir con el frontend
    tipoDocId: Optional[int] = None
    terceroId: Optional[int] = None
    fechaInicio: Optional[date] = None
    fechaFin: Optional[date] = None
    numero: Optional[str] = None
    cuentaId: Optional[int] = None
    centroCostoId: Optional[int] = None
    conceptoKeyword: Optional[str] = None
    valorOperador: Optional[str] = None
    valorMonto: Optional[float] = None


# --- ESQUEMAS PARA ANÁLISIS Y RESTAURACIÓN (Sin cambios) ---

class AnalysisRequest(BaseModel):
    """ Define el cuerpo de la petición para analizar un backup. """
    backupData: Dict[str, Any]
    targetEmpresaId: int
    bypass_signature: bool = False

class AnalysisSummaryItem(BaseModel):
    """ Define el resumen para un tipo de dato (ej. terceros). """
    total: int
    a_crear: int
    coincidencias: int

class AnalysisConflicts(BaseModel):
    """ Define la estructura de los conflictos encontrados. """
    documentos: List[str]
    maestros_faltantes: List[str]

class AnalysisReport(BaseModel):
    """ Define el reporte completo que devolverá el endpoint de análisis. """
    summary: Dict[str, AnalysisSummaryItem]
    conflicts: AnalysisConflicts
    sourceEmpresaId: Optional[int] = None
    targetEmpresaId: int
    integrity_valid: bool = True

# --- NUEVOS ESQUEMAS PARA LA VALIDACIÓN DE RESTAURACIÓN ---

class BackupDocumentoItem(BaseModel):
    """ Define la estructura de un documento en el backup. """
    id: int
    tipo_documento_id: int
    numero: int  # <-- CORREGIDO
    fecha: Optional[date] = None
    fecha_vencimiento: Optional[date] = None
    beneficiario_id: Optional[int] = None
    centro_costo_id: Optional[int] = None
    estado: Optional[str] = 'ACTIVO'
    anulado: Optional[bool] = False

class BackupDocumentoEliminadoItem(BaseModel):
    """ Define la estructura de un documento eliminado en el backup. """
    id_original: int
    tipo_documento_id: int
    numero: int  # <-- CORREGIDO
    fecha: Optional[date] = None
    log_eliminacion_id: Optional[int] = None
    fecha_vencimiento: Optional[date] = None
    beneficiario_id: Optional[int] = None
    centro_costo_id: Optional[int] = None
    usuario_creador_id: Optional[int] = None
    usuario_eliminacion_id: Optional[int] = None