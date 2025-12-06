from pydantic import BaseModel
from typing import Optional
from datetime import date

class RecodificacionFiltros(BaseModel):
    """ Define los filtros para seleccionar los documentos a recodificar. """
    # empresaId se elimina porque ahora se obtiene del token del usuario de forma segura.
    tipoDocId: int
    numero: Optional[str] = None
    fechaInicio: Optional[date] = None
    fechaFin: Optional[date] = None

class RecodificacionPayload(BaseModel):
    """ Define el cambio a realizar: de un ID de origen a uno de destino. """
    origenId: int
    destinoId: int

class RecodificacionRequest(BaseModel):
    """ El cuerpo completo de la petición que recibirá la API. """
    filtros: RecodificacionFiltros
    recodificacion: RecodificacionPayload