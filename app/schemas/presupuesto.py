from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

class PresupuestoBitacoraBase(BaseModel):
    valor_anterior: Decimal
    valor_nuevo: Decimal
    motivo: Optional[str] = None

class PresupuestoBitacoraCreate(PresupuestoBitacoraBase):
    detalle_id: int
    usuario_id: int

class PresupuestoBitacora(PresupuestoBitacoraBase):
    id: int
    detalle_id: int
    usuario_id: int
    fecha_hora: datetime

    class Config:
        from_attributes = True

class PresupuestoDetalleBase(BaseModel):
    codigo_cuenta: str
    mes: int
    valor_automatico: Decimal = Decimal('0.00')
    valor_editado: Optional[Decimal] = None
    valor_vigente: Decimal

class PresupuestoDetalleCreate(PresupuestoDetalleBase):
    cabecera_id: int

class PresupuestoDetalleUpdate(BaseModel):
    nuevo_valor: Decimal
    motivo: Optional[str] = None

class PresupuestoDetalle(PresupuestoDetalleBase):
    id: int
    cabecera_id: int
    fecha_edicion: Optional[datetime] = None
    bitacora: List[PresupuestoBitacora] = []

    class Config:
        from_attributes = True

class PresupuestoCabeceraBase(BaseModel):
    anio: int
    estado: str = "borrador"

class PresupuestoCabeceraCreate(PresupuestoCabeceraBase):
    empresa_id: int

class PresupuestoCabecera(PresupuestoCabeceraBase):
    id: int
    empresa_id: int
    fecha_creacion: datetime
    detalles: List[PresupuestoDetalle] = []

    class Config:
        from_attributes = True

# Schemas for reporting and bulk entry
class BudgetEntryRequest(BaseModel):
    anio: int
    codigo_cuenta: str
    valor_anual: Decimal

class IndividualMonthEdit(BaseModel):
    mes: int
    nuevo_valor: Decimal
    motivo: Optional[str] = None

class BatchBudgetEdit(BaseModel):
    cabecera_id: int
    ediciones: List[IndividualMonthEdit]
