from pydantic import BaseModel, Field
from typing import Optional

# Esquema base con los campos que se pueden crear o actualizar
class TipoDocumentoBase(BaseModel):
    codigo: str = Field(max_length=5)
    nombre: str = Field(max_length=100)
    numeracion_manual: bool = False
    funcion_especial: Optional[str] = Field(default=None, max_length=50)
    
    afecta_inventario: bool = False
    
    # --- INICIO CORRECCIÓN CRÍTICA: CAMPOS DE FILTRO ---
    es_venta: bool = False
    es_compra: bool = False
    # --- FIN CORRECCIÓN CRÍTICA ---
    
    # --- INICIO DE LA MODIFICACIÓN ---
    # Se añade el nuevo campo para la cuenta de caja/contado
    cuenta_caja_id: Optional[int] = None
    # --- FIN DE LA MODIFICACIÓN ---
    
    cuenta_debito_cxc_id: Optional[int] = None
    cuenta_credito_cxc_id: Optional[int] = None
    cuenta_debito_cxp_id: Optional[int] = None
    cuenta_credito_cxp_id: Optional[int] = None

# Esquema para la creación
class TipoDocumentoCreate(TipoDocumentoBase):
    empresa_id: int

# Esquema para la actualización
class TipoDocumentoUpdate(TipoDocumentoBase):
    consecutivo_actual: Optional[int] = None

# Esquema para devolver desde la API
class TipoDocumento(TipoDocumentoBase):
    id: int
    empresa_id: int
    consecutivo_actual: int

    class Config:
        from_attributes = True

# Esquema para la respuesta del endpoint de "siguiente-número"
class SiguienteNumero(BaseModel):
    siguiente_numero: int
    es_manual: bool

# Esquema para listas simples (menús desplegables)
class TipoDocumentoSimple(BaseModel):
    id: int
    nombre: str
    numeracion_manual: bool
    afecta_inventario: bool
    funcion_especial: Optional[str] = None
    # CRÍTICO: Asegurar que este esquema también los tenga si se usa
    es_venta: bool = False
    es_compra: bool = False

    class Config:
        from_attributes = True