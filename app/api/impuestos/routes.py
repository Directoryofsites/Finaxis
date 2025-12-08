from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.services import reportes_tributarios

router = APIRouter()

# --- Schemas (Interiores para simplicidad o mover a app/schemas/impuestos.py) ---
class ConfigRenglon(BaseModel):
    renglon: str
    concepto: str
    cuentas_ids: List[str] # Códigos de cuenta

class ConfiguracionSave(BaseModel):
    configs: List[ConfigRenglon]

# --- Rutas ---

@router.get("/configuracion/{tipo_reporte}")
def obtener_configuracion(
    tipo_reporte: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """ Retorna la configuración de renglones para un tipo de reporte (IVA, RENTA). """
    data = reportes_tributarios.get_configuracion(db, current_user.empresa_id, tipo_reporte)
    # Serializar básico
    return [
        {
            "renglon": c.renglon,
            "concepto": c.concepto,
            "cuentas_ids": c.cuentas_ids
        }
        for c in data
    ]

@router.post("/configuracion/{tipo_reporte}")
def guardar_configuracion(
    tipo_reporte: str,
    payload: ConfiguracionSave,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """ Guarda la configuración. Reemplaza la anterior para ese tipo. """
    configs_list = [c.dict() for c in payload.configs]
    updated = reportes_tributarios.save_configuracion(db, current_user.empresa_id, tipo_reporte, configs_list)
    return {"message": "Configuración guardada", "total": len(updated)}

@router.get("/declaracion/{tipo_reporte}")
def calcular_declaracion(
    tipo_reporte: str,
    anio: int = Query(..., description="Año gravable"),
    periodo: str = Query(..., description="Periodo (01, 02...)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """ Calcula los valores del formulario basado en movimientos. """
    if tipo_reporte.upper() == 'IVA':
        return reportes_tributarios.calcular_declaracion_iva(db, current_user.empresa_id, anio, periodo)
    elif tipo_reporte.upper() == 'RETEFUENTE':
        return reportes_tributarios.calcular_declaracion_retefuente(db, current_user.empresa_id, anio, periodo)
    elif tipo_reporte.upper() == 'RENTA':
        return reportes_tributarios.calcular_declaracion_renta(db, current_user.empresa_id, anio)
    else:
        raise HTTPException(status_code=400, detail=f"Reporte {tipo_reporte} no soportado")
