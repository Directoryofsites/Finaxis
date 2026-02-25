from datetime import date
from sqlalchemy.orm import Session
from app.models.empresa import Empresa

def apply_default_ai_context(params: dict, empresa_id: int, db: Session) -> dict:
    """
    Rellena inteligentemente los parámetros que el modelo de IA dejó nulos o vacíos.
    Si el usuario no dice una fecha, usamos la fecha de creación de su empresa en el software.
    """
    if "fecha_inicio" in params and not params.get("fecha_inicio"):
        # Buscar empresa para saber cuando empezó
        empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
        if empresa and empresa.fecha_inicio_operaciones:
            params["fecha_inicio"] = empresa.fecha_inicio_operaciones.isoformat()
        elif empresa and empresa.created_at:
            params["fecha_inicio"] = empresa.created_at.date().isoformat()
        else:
            params["fecha_inicio"] = "2020-01-01" # Extremo fallback
            
    if "fecha_fin" in params and not params.get("fecha_fin"):
        params["fecha_fin"] = date.today().isoformat()
        
    if "fecha_corte" in params and not params.get("fecha_corte"):
        params["fecha_corte"] = date.today().isoformat()
        
    return params
