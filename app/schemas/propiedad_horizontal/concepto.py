from typing import Optional, List
from pydantic import BaseModel
from decimal import Decimal
from app.schemas.plan_cuenta import PlanCuenta
from .modulo_contribucion import PHModuloContribucionResponse

class PHConceptoBase(BaseModel):
    nombre: str
    cuenta_ingreso_id: int
    cuenta_cxc_id: Optional[int] = None
    cuenta_interes_id: Optional[int] = None
    cuenta_caja_id: Optional[int] = None
    usa_coeficiente: bool = False
    es_fijo: bool = True
    valor_defecto: Decimal = 0

class PHConceptoCreate(PHConceptoBase):
    modulos_ids: Optional[List[int]] = []

class PHConceptoUpdate(PHConceptoBase):
    nombre: Optional[str] = None
    cuenta_ingreso_id: Optional[int] = None
    cuenta_caja_id: Optional[int] = None
    modulos_ids: Optional[List[int]] = []

class PHConcepto(PHConceptoBase):
    id: int
    empresa_id: int
    activo: bool
    
    cuenta_ingreso: Optional[PlanCuenta] = None
    cuenta_cxc: Optional[PlanCuenta] = None
    cuenta_interes: Optional[PlanCuenta] = None
    cuenta_caja: Optional[PlanCuenta] = None
    modulos: List[PHModuloContribucionResponse] = []

    class Config:
        orm_mode = True
