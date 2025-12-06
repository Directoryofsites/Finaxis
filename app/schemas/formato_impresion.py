from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

# Esquema base con los campos comunes
class FormatoImpresionBase(BaseModel):
    nombre: str = Field(max_length=255)
    contenido_html: str
    tipo_documento_id: Optional[int] = None
    variables_ejemplo_json: Optional[Dict[str, Any]] = None

# Esquema para la creación de una plantilla
class FormatoImpresionCreate(FormatoImpresionBase):
    empresa_id: Optional[int] = None

# Esquema para la actualización de una plantilla (todos los campos opcionales)
class FormatoImpresionUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, max_length=255)
    contenido_html: Optional[str] = None
    tipo_documento_id: Optional[int] = None
    variables_ejemplo_json: Optional[Dict[str, Any]] = None

# Esquema para devolver una plantilla desde la API
class FormatoImpresion(FormatoImpresionBase):
    id: int
    empresa_id: int
    fecha_creacion: datetime
    ultima_modificacion: datetime
    creado_por_usuario_id: Optional[int] = None

    class Config:
        from_attributes = True