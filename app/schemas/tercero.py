# app/schemas/tercero.py (Versión con lista_precio_id)

from pydantic import BaseModel, Field
from typing import Optional

# Esquema base con los campos que se repiten y la sintaxis corregida
class TerceroBase(BaseModel):
    nit: str = Field(max_length=20)
    razon_social: str = Field(max_length=255)
    dv: Optional[str] = Field(default=None, max_length=1)
    nombre_comercial: Optional[str] = Field(default=None, max_length=255)
    es_cliente: Optional[bool] = False
    es_proveedor: Optional[bool] = False
    es_empleado: Optional[bool] = False
    responsabilidad_fiscal: Optional[str] = Field(default=None, max_length=100)
    direccion: Optional[str] = Field(default=None, max_length=255)
    ciudad: Optional[str] = Field(default=None, max_length=100)
    telefono: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=255)
    actividad_economica_ciiu: Optional[str] = Field(default=None, max_length=10)
    es_regimen_simple: Optional[bool] = False
    # --- INICIO NUEVO CAMPO OPCIONAL ---
    lista_precio_id: Optional[int] = None
    # --- FIN NUEVO CAMPO OPCIONAL ---

# Esquema para crear un Tercero
class TerceroCreate(TerceroBase):
    empresa_id: int # El empresa_id lo asignamos en la ruta, no viene del frontend

# Esquema para actualizar un Tercero (todos los campos son opcionales)
class TerceroUpdate(BaseModel):
    nit: Optional[str] = Field(default=None, max_length=20)
    razon_social: Optional[str] = Field(default=None, max_length=255)
    dv: Optional[str] = Field(default=None, max_length=1)
    nombre_comercial: Optional[str] = Field(default=None, max_length=255)
    es_cliente: Optional[bool] = None
    es_proveedor: Optional[bool] = None
    es_empleado: Optional[bool] = None
    responsabilidad_fiscal: Optional[str] = Field(default=None, max_length=100)
    direccion: Optional[str] = Field(default=None, max_length=255)
    ciudad: Optional[str] = Field(default=None, max_length=100)
    telefono: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=255)
    actividad_economica_ciiu: Optional[str] = Field(default=None, max_length=10)
    es_regimen_simple: Optional[bool] = None
    # --- INICIO NUEVO CAMPO OPCIONAL ---
    lista_precio_id: Optional[int] = None # Permitimos actualizar la lista de precios
    # --- FIN NUEVO CAMPO OPCIONAL ---

# Esquema para leer un Tercero
class Tercero(TerceroBase):
    id: int
    empresa_id: int
    # Añadimos los campos de auditoría para que se devuelvan en la respuesta
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    # --- INICIO NUEVO CAMPO OPCIONAL ---
    # lista_precio_id ya está en TerceroBase, se hereda automáticamente
    # --- FIN NUEVO CAMPO OPCIONAL ---

    class Config:
        from_attributes = True # Cambiado de orm_mode a from_attributes (Pydantic v2)

# Esquema para la respuesta de la verificación de existencia
class TerceroExiste(BaseModel):
    existe: bool