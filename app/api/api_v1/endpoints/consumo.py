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
    mes: int = Query(None, ge=1, le=12, description="Mes a consultar (1-12)"),
    anio: int = Query(None, ge=2000, description="Año a consultar"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Any:
    """
    Obtiene el estado actual del cupo de registros para el periodo especificado:
    - Plan Mensual del mes/año solicitado.
    - Bolsas de excedentes vigentes EN ese periodo.
    - Recargas adicionales vigentes EN ese periodo.
    """
    empresa_id = current_user.empresa_id
    now = datetime.now()
    
    # Defaults si no se especifican
    query_mes = mes if mes else now.month
    query_anio = anio if anio else now.year
    
    # Fecha de referencia para el periodo consultado (Primer día del mes)
    # Esto os sirve para filtrar qué bolsas/recargas estaban "vivas" en ese momento
    # periodo_start = datetime(query_anio, query_mes, 1)
    # Calculamos el último día del mes para periodo_end (opcional, por ahora usaremos lógica simple)
    
    # 1. Plan Actual (o del pasado/futuro)
    plan = db.query(ControlPlanMensual).filter(
        ControlPlanMensual.empresa_id == empresa_id,
        ControlPlanMensual.anio == query_anio,
        ControlPlanMensual.mes == query_mes
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
    # 2. Bolsas Vigentes
    # Una bolsa es visible si su fecha de vencimiento es POSTERIOR al inicio del mes consultado
    # Y su fecha de creación (si la tuviéramos) anterior al fin del mes. 
    # Por simplicidad: Bolsas que vencen DESPUES del inicio del mes consultado.
    # (Si consulto Enero 2025, veo bolsas que vencen en Feb 2025 o después)
    # Y que idealmente se crearon antes/durante (pero created_at no siempre se chequea estricto en vista resumen)
    periodo_ref = datetime(query_anio, query_mes, 1)
    
    bolsas = db.query(BolsaExcedente).filter(
        BolsaExcedente.empresa_id == empresa_id,
        BolsaExcedente.estado == EstadoBolsa.VIGENTE,
        BolsaExcedente.fecha_vencimiento >= periodo_ref
    ).order_by(asc(BolsaExcedente.fecha_vencimiento)).all()
    
    # 3. Recargas Vigentes
    # Similar lógica, o simplemente mostramos las disponibles.
    # Si estamos viendo el pasado, esto puede ser inexacto ya que muestra el saldo ACTUAL.
    # Pero para "gestión" suele referirse a qué tengo disponible.
    # NOTA: El historial de consumo muestra qué pasó exactamente. El resumen muestra "qué hay".
    # Si viajo al pasado, veré el saldo actual de las recargas que AUN no han vencido respecto a esa fecha.
    recargas = db.query(RecargaAdicional).filter(
        RecargaAdicional.empresa_id == empresa_id,
        RecargaAdicional.estado == EstadoRecarga.VIGENTE
        # Opcional: filtrar por fecha de compra si se desea ocultar futuras
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
