from pydantic import BaseModel
from typing import Optional

class EmpresaConfigBuzonBase(BaseModel):
    email_addr: Optional[str] = None
    password_app: Optional[str] = None
    tipo_documento_id: Optional[int] = None
    cuenta_gasto_id: Optional[int] = None
    cuenta_caja_id: Optional[int] = None
    is_active: Optional[bool] = True

class EmpresaConfigBuzonCreate(EmpresaConfigBuzonBase):
    pass

class EmpresaConfigBuzonUpdate(EmpresaConfigBuzonBase):
    pass

class EmpresaConfigBuzonResponse(EmpresaConfigBuzonBase):
    id: int
    empresa_id: int

    class Config:
        from_attributes = True

class BuzonConfigDTO(BaseModel):
    email_addr: Optional[str] = None
    password_app_masked: Optional[str] = None
    tipo_documento_id: Optional[int] = None
    cuenta_gasto_id: Optional[int] = None
    cuenta_caja_id: Optional[int] = None
    is_active: Optional[bool] = True
