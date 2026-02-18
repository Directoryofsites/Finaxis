
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date

class ConfiguracionFEBase(BaseModel):
    proveedor: str = "FACTUS"
    ambiente: str = "PRUEBAS"
    api_token: Optional[str] = None
    api_url: Optional[str] = None
    email_registro: Optional[str] = None
    
    # Numeración Ventas
    prefijo: Optional[str] = None
    resolucion_numero: Optional[str] = None
    resolucion_fecha: Optional[date] = None
    rango_desde: Optional[int] = None
    rango_hasta: Optional[int] = None
    factura_rango_id: Optional[int] = None

    # Numeración Documento Soporte
    ds_prefijo: Optional[str] = None
    ds_resolucion_numero: Optional[str] = None
    ds_rango_id: Optional[int] = None
    
    # Range IDs Notas
    nc_rango_id: Optional[int] = None
    nd_rango_id: Optional[int] = None
    
    habilitado: bool = False

class ConfiguracionFECreate(ConfiguracionFEBase):
    pass

class ConfiguracionFEUpdate(ConfiguracionFEBase):
    pass

class ConfiguracionFEResponse(ConfiguracionFEBase):
    id: int
    empresa_id: int
    
    model_config = ConfigDict(from_attributes=True)
