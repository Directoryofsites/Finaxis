from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.schemas.plan_cuenta import PlanCuentaSimple

# --- CONFIGURACION ---
class PHConfiguracionBase(BaseModel):
    interes_mora_mensual: float = Field(default=1.5, ge=0)
    dia_corte: int = Field(default=1, ge=1, le=31)
    dia_limite_pago: int = Field(default=10, ge=1, le=31)
    dia_limite_pronto_pago: int = Field(default=5, ge=1, le=31)
    descuento_pronto_pago: float = Field(default=0.0, ge=0)
    mensaje_factura: Optional[str] = None
    tipo_documento_factura_id: Optional[int] = None
    # Duplicate line removed in cleanup, keeping one
    tipo_documento_recibo_id: Optional[int] = None
    cuenta_cartera_id: Optional[int] = None
    cuenta_caja_id: Optional[int] = None
    cuenta_ingreso_intereses_id: Optional[int] = None
    interes_mora_habilitado: bool = True

class PHConfiguracionUpdate(PHConfiguracionBase):
    pass

class PHConfiguracionResponse(PHConfiguracionBase):
    id: int
    empresa_id: int
    
    # Relationships for UI
    cuenta_cartera: Optional[PlanCuentaSimple] = None
    cuenta_caja: Optional[PlanCuentaSimple] = None
    cuenta_ingreso_intereses: Optional[PlanCuentaSimple] = None

    class Config:
        from_attributes = True

# --- CONCEPTOS ---
class PHConceptoBase(BaseModel):
    nombre: str
    codigo_contable: Optional[str] = None
    tipo_calculo: str = "COEFICIENTE" # FIJO, COEFICIENTE
    valor_defecto: float = 0
    activo: bool = True
    tipo_documento_id: Optional[int] = None
    cuenta_cartera_id: Optional[int] = None
    tipo_documento_recibo_id: Optional[int] = None
    cuenta_caja_id: Optional[int] = None

class PHConceptoCreate(PHConceptoBase):
    pass

class PHConceptoUpdate(BaseModel):
    nombre: Optional[str] = None
    codigo_contable: Optional[str] = None
    tipo_calculo: Optional[str] = None
    valor_defecto: Optional[float] = None
    activo: Optional[bool] = None
    tipo_documento_id: Optional[int] = None
    cuenta_cartera_id: Optional[int] = None
    tipo_documento_recibo_id: Optional[int] = None
    cuenta_caja_id: Optional[int] = None



class PHConceptoResponse(PHConceptoBase):
    id: int
    empresa_id: int
    
    # Nested Relationships for UI Display
    cuenta_cartera: Optional[PlanCuentaSimple] = None
    cuenta_caja: Optional[PlanCuentaSimple] = None

    class Config:
        from_attributes = True
