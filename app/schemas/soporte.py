# app/schemas/soporte.py
from pydantic import BaseModel
from typing import List, Optional
from .empresa import EmpresaConUsuarios, EmpresaConUsuariosCreate
from .usuario import User

class DashboardData(BaseModel):
    # Backward compatibility
    empresas: List[EmpresaConUsuarios]
    usuarios_soporte: List[User]

    class Config:
        from_attributes = True

# --- NUEVOS SCHEMAS PARA BÚSQUEDA ---

class EmpresaSearchResponse(BaseModel):
    items: List[EmpresaConUsuarios]
    total: int
    page: int
    size: int
    pages: int

    class Config:
        from_attributes = True

class EmpresaCreateFromTemplate(BaseModel):
    empresa_data: EmpresaConUsuariosCreate
    template_category: str
    owner_id: Optional[int] = None

class TemplateConversionRequest(BaseModel):
    template_category: str
