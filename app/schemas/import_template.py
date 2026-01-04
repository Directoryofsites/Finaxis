from pydantic import BaseModel, Field, field_validator
from typing import Dict, Optional, Any
from datetime import datetime

class ImportTemplateBase(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=100)
    descripcion: Optional[str] = None
    
    # Mapping configuration: Key (Finaxis Field) -> Value (Column Index or ColumnName)
    # Recommended fields: fecha, tipo_doc, numero, tercero, nit, cuenta, detalle, debito, credito
    mapping_config: Dict[str, Any]

    @field_validator('mapping_config')
    def validate_mapping(cls, v):
        required_keys = ['fecha', 'cuenta', 'debito', 'credito']
        missing = [key for key in required_keys if key not in v]
        if missing:
            raise ValueError(f"La configuración de mapeo debe incluir al menos: {', '.join(missing)}")
        return v

class ImportTemplateCreate(ImportTemplateBase):
    pass

class ImportTemplateUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    mapping_config: Optional[Dict[str, Any]] = None

class ImportTemplateResponse(ImportTemplateBase):
    id: int
    empresa_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
