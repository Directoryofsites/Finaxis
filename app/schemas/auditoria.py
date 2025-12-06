from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date

class LogOperacionItem(BaseModel):
    """
    Define la estructura de un único registro en el informe de auditoría.
    """
    id: int
    fecha_operacion: datetime
    tipo_operacion: str
    email_usuario: Optional[str] = None
    razon: Optional[str] = None
    detalle_documento_json: Optional[List[Dict[str, Any]]] = None

    class Config:
        from_attributes = True

class UltimasOperacionesRequest(BaseModel):
    """
    Define los filtros para la consulta de últimas operaciones de soporte.
    """
    limit: int
    # --- CORRECCIÓN: Se restaura el campo para el ordenamiento dinámico ---
    orderBy: Optional[str] = 'fecha_evento' 
    empresaIds: Optional[List[int]] = None

    # --- NUEVOS FILTROS DE FECHA ---
    # Todos son opcionales para permitir máxima flexibilidad en la consulta.
    fecha_creacion_inicio: Optional[datetime] = None
    fecha_creacion_fin: Optional[datetime] = None
    fecha_documento_inicio: Optional[datetime] = None
    fecha_documento_fin: Optional[datetime] = None
    
class UltimasOperacionesResponse(BaseModel):
    """
    Define la estructura de la respuesta para el informe de últimas operaciones.
    """
    id: int
    empresa_razon_social: str
    fecha_operacion: Optional[datetime] = None
    # --- INICIO DE LA MEJORA ---
    # Añadimos el campo para la fecha interna del documento.
    fecha_documento: Optional[date] = None
    # --- FIN DE LA MEJORA ---
    email_usuario: Optional[str] = None
    tipo_operacion: str
    razon: Optional[str] = None
    detalle_documento: str