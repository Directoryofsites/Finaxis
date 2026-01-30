from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class EstadoEscenario(str, Enum):
    BORRADOR = "BORRADOR"
    APROBADO = "APROBADO"
    CERRADO = "CERRADO"

class TipoSector(str, Enum):
    PRIVADO = "PRIVADO"
    PUBLICO = "PUBLICO"

class MetodoProyeccion(str, Enum):
    MANUAL = "MANUAL"
    PROMEDIO_HISTORICO = "PROMEDIO_HISTORICO"
    EJECUCION_ANTERIOR = "EJECUCION_ANTERIOR"
    VALOR_FIJO = "VALOR_FIJO"
    INCREMENTO_PORCENTUAL = "INCREMENTO_PORCENTUAL"

# --- ITEMS ---
class PresupuestoItemBase(BaseModel):
    cuenta_id: int
    metodo_proyeccion: MetodoProyeccion = MetodoProyeccion.MANUAL
    base_calculo: Optional[str] = None
    factor_ajuste: float = 0
    variable_aplicada: Optional[str] = None
    
    mes_01: float = 0
    mes_02: float = 0
    mes_03: float = 0
    mes_04: float = 0
    mes_05: float = 0
    mes_06: float = 0
    mes_07: float = 0
    mes_08: float = 0
    mes_09: float = 0
    mes_10: float = 0
    mes_11: float = 0
    mes_12: float = 0
    
    valor_total: float = 0
    observacion: Optional[str] = None

class PresupuestoItemCreate(PresupuestoItemBase):
    pass

class PresupuestoItemUpdate(PresupuestoItemBase):
    cuenta_id: Optional[int] = None # Opcional en update

class PlanCuentaInfo(BaseModel):
    id: int
    codigo: str
    nombre: str
    class Config:
        orm_mode = True

class PresupuestoItem(PresupuestoItemBase):
    id: int
    escenario_id: int
    cuenta: Optional[PlanCuentaInfo] = None
    
    class Config:
        orm_mode = True

# --- ESCENARIOS ---
class EscenarioBase(BaseModel):
    nombre: str
    anio: int
    estado: EstadoEscenario = EstadoEscenario.BORRADOR
    tipo_sector: TipoSector = TipoSector.PRIVADO
    variables_globales: Optional[Dict] = {}

class EscenarioCreate(EscenarioBase):
    pass

class EscenarioUpdate(BaseModel):
    nombre: Optional[str] = None
    estado: Optional[EstadoEscenario] = None
    variables_globales: Optional[Dict] = None

class Escenario(EscenarioBase):
    id: int
    empresa_id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    created_by: Optional[int]
    
    # Podríamos incluir los items o no, depende del view
    # items: List[PresupuestoItem] = []

    class Config:
        orm_mode = True

class EscenarioConItems(Escenario):
    items: List[PresupuestoItem] = []

# --- EJECUCIÓN (REPORTES) ---

class EjecucionMes(BaseModel):
    presupuestado: float = 0
    ejecutado: float = 0
    variacion: float = 0
    porcentaje_ejecucion: float = 0

class EjecucionItem(BaseModel):
    cuenta_id: int
    codigo: str
    nombre: str
    
    # Datos por mes (01..12) del año fiscal
    enero: EjecucionMes
    febrero: EjecucionMes
    marzo: EjecucionMes
    abril: EjecucionMes
    mayo: EjecucionMes
    junio: EjecucionMes
    julio: EjecucionMes
    agosto: EjecucionMes
    septiembre: EjecucionMes
    octubre: EjecucionMes
    noviembre: EjecucionMes
    diciembre: EjecucionMes
    
    total_anual: EjecucionMes

class ReporteEjecucion(BaseModel):
    escenario: Escenario
    items: List[EjecucionItem]
