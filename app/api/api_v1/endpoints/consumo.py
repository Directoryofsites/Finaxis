from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import desc, asc

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.consumo import ResumenConsumo, PlanMensualRead, BolsaItemRead, RecargaItemRead, HistorialConsumoRead
from app.models.consumo_registros import ControlPlanMensual, BolsaExcedente, RecargaAdicional, HistorialConsumo, EstadoPlan, EstadoBolsa, EstadoRecarga
from app.services.consumo_service import _get_or_create_plan_mensual, PAQUETES_RECARGA, comprar_recarga
from pydantic import BaseModel

router = APIRouter()

@router.get("/resumen", response_model=ResumenConsumo)
def get_resumen_consumo(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Any:
    """
    Obtiene el estado actual del cupo de registros:
    - Plan Mensual del mes en curso.
    - Bolsas de excedentes vigentes.
    - Recargas adicionales vigentes.
    """
    empresa_id = current_user.empresa_id
    now = datetime.now()
    
    # 1. Plan Actual
    # Usamos la funcion interna del servicio para garantizar que si no existe, lo crea (o muestra stats por defecto)
    # Sin embargo, _get_or_create usa with_for_update, lo cual puede ser overkill para lectura.
    # Haremos query normal de lectura.
    plan = db.query(ControlPlanMensual).filter(
        ControlPlanMensual.empresa_id == empresa_id,
        ControlPlanMensual.anio == now.year,
        ControlPlanMensual.mes == now.month
    ).first()
    
    # Si no existe plan, retornamos una estructura dummy o null?
    # Mejor retornar null en plan_actual o crear uno en memoria para visualización.
    plan_schema = None
    if plan:
        plan_schema = plan
    else:
        # Simulamos respuesta vacía si no se ha inicializado
        # Ojo: El frontend debe manejar esto.
        pass

    # 2. Bolsas Vigentes (Ordenadas por vencimiento, FIFO visual)
    bolsas = db.query(BolsaExcedente).filter(
        BolsaExcedente.empresa_id == empresa_id,
        BolsaExcedente.estado == EstadoBolsa.VIGENTE,
        BolsaExcedente.fecha_vencimiento >= now
    ).order_by(asc(BolsaExcedente.fecha_vencimiento)).all()
    
    # 3. Recargas Vigentes
    recargas = db.query(RecargaAdicional).filter(
        RecargaAdicional.empresa_id == empresa_id,
        RecargaAdicional.estado == EstadoRecarga.VIGENTE
    ).order_by(asc(RecargaAdicional.fecha_compra)).all()
    
    # Calculo Total
    total = (plan.cantidad_disponible if plan and plan.estado == EstadoPlan.ABIERTO else 0) + \
            sum(b.cantidad_disponible for b in bolsas) + \
            sum(r.cantidad_disponible for r in recargas)
            
    return {
        "plan_actual": plan_schema,
        "bolsas_vigentes": bolsas,
        "recargas_vigentes": recargas,
        "total_disponible": total
    }

@router.get("/historial", response_model=List[HistorialConsumoRead])
def get_historial_consumo(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Any:
    """
    Obtiene el historial de auditoría de consumos y reversiones.
    """
    historial = db.query(HistorialConsumo).filter(
        HistorialConsumo.empresa_id == current_user.empresa_id
    ).order_by(desc(HistorialConsumo.fecha)).offset(skip).limit(limit).all()
    
    return historial

# --- NUEVOS ENDPOINTS DE RECARGAS ---

@router.get("/paquetes")
def get_paquetes_recarga(
    current_user = Depends(get_current_user)
):
    """Retorna la lista de paquetes de recarga disponibles y sus precios."""
    # Convertimos dict a lista para facil consumo en frontend
    return [
        {"id": k, **v} 
        for k, v in PAQUETES_RECARGA.items()
    ]

class CompraRecargaRequest(BaseModel):
    paquete_id: str

@router.post("/recargas")
def comprar_paquete_recarga(
    data: CompraRecargaRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Procesa la compra de un paquete. 
    Aumenta el cupo disponible inmediatamente y genera una deuda pendiente de facturar.
    """
    try:
        recarga = comprar_recarga(db, current_user.empresa_id, data.paquete_id)
        return {"status": "success", "message": "Recarga exitosa", "recarga_id": recarga.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
