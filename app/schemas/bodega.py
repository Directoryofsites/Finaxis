# app/schemas/bodega.py (Versión Completa y Corregida)

from pydantic import BaseModel
from typing import Optional

# --- Schema Base ---
# Define los campos comunes. Así no repetimos código.
class BodegaBase(BaseModel):
    nombre: str

# --- Schema para la Creación (el que faltaba) ---
# Este es el "molde" que la ruta POST /bodegas/ usará.
class BodegaCreate(BodegaBase):
    pass

# --- Schema para la Actualización ---
# Permite que el nombre sea opcional al actualizar.
class BodegaUpdate(BodegaBase):
    nombre: Optional[str] = None

# --- Schema Principal para Respuestas (el que ya tenías, pero mejorado) ---
# Este es el "molde" para los datos que se envían desde el backend.
class Bodega(BodegaBase):
    id: int
    empresa_id: int

    class Config:
        from_attributes = True