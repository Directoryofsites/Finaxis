from pydantic import BaseModel, Field, conint
from typing import Optional, List
from datetime import datetime

# 1. Esquema Base (Datos de Entrada)
class ConceptoFavoritoBase(BaseModel):
    # La descripción es el campo de negocio principal y es requerido
    descripcion: str = Field(..., max_length=255)
    # El centro de costo es opcional
    centro_costo_id: Optional[int] = Field(None, description="ID del centro de costo asociado, si aplica.")

# 2. Esquema de Creación (Usado internamente por el servicio)
class ConceptoFavoritoCreate(ConceptoFavoritoBase):
    # Campos que el servicio debe inyectar
    empresa_id: int
    created_by: int
    updated_by: int

# 3. Esquema de Actualización (Permite campos opcionales)
class ConceptoFavoritoUpdate(ConceptoFavoritoBase):
    descripcion: Optional[str] = Field(None, max_length=255)
    
# 4. Esquema de Respuesta (Incluye ID y metadata)
class ConceptoFavorito(ConceptoFavoritoBase):
    id: int
    created_at: datetime
    created_by: int
    updated_by: int
    
    # Campo para la respuesta masiva o eliminación
class ConceptosDelete(BaseModel):
    ids: List[int]

    class Config:
        from_attributes = True