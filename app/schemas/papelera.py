# app/schemas/papelera.py
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from decimal import Decimal

class PapeleraItem(BaseModel):
    id: int
    id_original: int
    fecha: date
    numero: str # Se ajusta a str para consistencia con otros schemas
    fecha_eliminacion: datetime
    usuario_eliminacion: Optional[str] = None
    
    # --- INICIO DE LA CORRECCIÓN ---
    # Se añaden los campos que faltaban en el contrato
    tipo_documento_nombre: Optional[str] = None
    valor_documento: Decimal
    # --- FIN DE LA CORRECCIÓN ---

    class Config:
        from_attributes = True