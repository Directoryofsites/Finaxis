from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from app.models.nomina import PeriodoPago, TipoContrato, EstadoEmpleado

# --- TIPO DE NOMINA ---

class TipoNominaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    periodo_pago: PeriodoPago = PeriodoPago.MENSUAL

class TipoNominaCreate(TipoNominaBase):
    pass

class TipoNominaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    periodo_pago: Optional[PeriodoPago] = None
    
class TipoNominaResponse(TipoNominaBase):
    id: int
    empresa_id: int

    class Config:
        from_attributes = True

# --- EMPLEADO ---

class EmpleadoCreate(BaseModel):
    nombres: str
    apellidos: str
    numero_documento: str
    salario_base: float
    fecha_ingreso: date
    tiene_auxilio: bool = True
    tercero_id: Optional[int] = None
    tipo_nomina_id: Optional[int] = None

class EmpleadoResponse(EmpleadoCreate):
    id: int
    class Config:
        from_attributes = True

# --- LIQUIDACION ---

class LiquidarRequest(BaseModel):
    empleado_id: int
    dias_trabajados: int = 30
    horas_extras: float = 0

    comisiones: float = 0
    otros_devengados: float = 0
    otras_deducciones: float = 0

    
class GuardarNominaRequest(BaseModel):
    empleado_id: int
    anio: int
    mes: int
    dias_trabajados: int = 30
    horas_extras: float = 0

    comisiones: float = 0
    otros_devengados: float = 0
    otras_deducciones: float = 0


# --- CONFIGURACION PUC ---

class ConfigNominaSchema(BaseModel):
    tipo_nomina_id: Optional[int] = None
    tipo_documento_id: Optional[int] = None
    cuenta_sueldo_id: Optional[int] = None
    cuenta_auxilio_transporte_id: Optional[int] = None
    cuenta_horas_extras_id: Optional[int] = None
    cuenta_comisiones_id: Optional[int] = None
    cuenta_salarios_por_pagar_id: Optional[int] = None
    cuenta_aporte_salud_id: Optional[int] = None
    cuenta_aporte_pension_id: Optional[int] = None
    cuenta_fondo_solidaridad_id: Optional[int] = None
    cuenta_otros_devengados_id: Optional[int] = None
    cuenta_otras_deducciones_id: Optional[int] = None
    
    
    class Config:
        from_attributes = True
