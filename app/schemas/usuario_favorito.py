# app/schemas/usuario_favorito.py (REEMPLAZO COMPLETO Y LÍMITE 16 DEFINITIVO)

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

# LÍMITE ACTUALIZADO: Expandido a 24 posiciones
MAX_FAVORITES_LIMIT = 24 

class UsuarioFavoritoBase(BaseModel):
    # La ruta de la aplicación debe ser obligatoria
    ruta_enlace: str = Field(..., max_length=255, description="URL del enlace rápido.")
    
    # El nombre que el usuario personaliza
    nombre_personalizado: str = Field(..., max_length=100, description="Nombre del botón en el Dashboard.")
    
    # ORDEN ACTUALIZADO: Posición del botón (1 a 24)
    orden: int = Field(..., ge=1, le=MAX_FAVORITES_LIMIT, description=f"Posición del acceso rápido (1 a {MAX_FAVORITES_LIMIT}).")

class UsuarioFavoritoCreate(UsuarioFavoritoBase):
    pass

class UsuarioFavoritoUpdate(BaseModel):
    # Todos los campos son opcionales para la actualización parcial (PUT/PATCH)
    ruta_enlace: Optional[str] = Field(None, max_length=255, description="URL del enlace rápido.")
    nombre_personalizado: Optional[str] = Field(None, max_length=100, description="Nombre del botón en el Dashboard.")

    # ORDEN ACTUALIZADO: Posición del botón (1 a 24)
    orden: Optional[int] = Field(None, ge=1, le=MAX_FAVORITES_LIMIT, description=f"Posición del acceso rápido (1 a {MAX_FAVORITES_LIMIT}).")
    
class UsuarioFavoritoResponse(UsuarioFavoritoBase):
    id: int
    usuario_id: int
    empresa_id: Optional[int] = None # Se añade para consistencia
    created_by: Optional[int] = None # Se añade para consistencia
    updated_by: Optional[int] = None # Se añade para consistencia
    
    model_config = ConfigDict(from_attributes=True) # Habilita mapeo directo desde el ORM