from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal

# --- Esquemas para los Detalles de la Plantilla ---

class PlantillaDetalleBase(BaseModel):
    cuenta_id: int
    concepto: Optional[str] = Field(default=None)
    debito: Decimal = 0
    credito: Decimal = 0

class PlantillaDetalleCreate(PlantillaDetalleBase):
    pass

class PlantillaDetalle(PlantillaDetalleBase):
    id: int

    class Config:
        from_attributes = True


# --- Esquemas para la Plantilla Maestra ---

class PlantillaMaestraBase(BaseModel):
    nombre_plantilla: str = Field(max_length=255)
    tipo_documento_id_sugerido: Optional[int] = None
    beneficiario_id_sugerido: Optional[int] = None
    centro_costo_id_sugerido: Optional[int] = None

class PlantillaMaestraCreate(PlantillaMaestraBase):
    detalles: List[PlantillaDetalleCreate]

class PlantillaMaestraUpdate(PlantillaMaestraBase):
    detalles: List[PlantillaDetalleCreate]

class PlantillaMaestra(PlantillaMaestraBase):
    id: int
    empresa_id: int
    detalles: List[PlantillaDetalle] = []

    class Config:
        from_attributes = True

# --- INICIO: NUEVO SCHEMA PARA LA FUNCIONALIDAD ---

class TemplateCreateFromDocument(BaseModel):
    nombre_plantilla: str = Field(..., min_length=1, max_length=255, description="El nombre para la nueva plantilla.")

# --- FIN: NUEVO SCHEMA ---