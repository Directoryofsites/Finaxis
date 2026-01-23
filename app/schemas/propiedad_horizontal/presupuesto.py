from pydantic import BaseModel
from typing import Optional, List

# Schema Base
class PHPresupuestoBase(BaseModel):
    cuenta_id: int
    mes_01: Optional[float] = 0
    mes_02: Optional[float] = 0
    mes_03: Optional[float] = 0
    mes_04: Optional[float] = 0
    mes_05: Optional[float] = 0
    mes_06: Optional[float] = 0
    mes_07: Optional[float] = 0
    mes_08: Optional[float] = 0
    mes_09: Optional[float] = 0
    mes_10: Optional[float] = 0
    mes_11: Optional[float] = 0
    mes_12: Optional[float] = 0
    valor_anual: Optional[float] = 0

class PHPresupuestoCreate(PHPresupuestoBase):
    anio: int

class PHPresupuestoUpdate(PHPresupuestoBase):
    pass

class PHPresupuestoResponse(PHPresupuestoBase):
    id: int
    empresa_id: int
    anio: int
    cuenta_nombre: Optional[str] = None
    cuenta_codigo: Optional[str] = None

    class Config:
        from_attributes = True

# Para guardado masivo (Grid)
class PHPresupuestoMasivo(BaseModel):
    anio: int
    items: List[PHPresupuestoBase]

# Para Reporte de Ejecución
class EjecucionItem(BaseModel):
    cuenta_id: int
    cuenta_codigo: str
    cuenta_nombre: str
    presupuestado: float
    ejecutado: float
    variacion_absoluta: float
    cumplimiento_porcentaje: float

class EjecucionPresupuestalResponse(BaseModel):
    anio: int
    mes_corte: int # 1..12, 13=Anual
    items: List[EjecucionItem]
    total_presupuestado: float
    total_ejecutado: float
    total_variacion: float
