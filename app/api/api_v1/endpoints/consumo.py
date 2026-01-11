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

@router.get("/precio-unitario")
def get_precio_unitario(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Retorna el precio unitario configurado para recargas personalizadas."""
    from app.models.configuracion_sistema import ConfiguracionSistema
    from sqlalchemy import inspect
    
    # Simple table existence check to avoid crashing if migration hasn't run
    if not inspect(db.get_bind()).has_table("configuracion_sistema"):
         return {"precio": 150}

    config = db.query(ConfiguracionSistema).filter_by(clave="PRECIO_POR_REGISTRO").first()
    return {"precio": int(config.valor) if config else 150}

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
    # Calculamos el último día del mes para periodo_end (opcional,    # Validar fecha
    
    # Construir fecha arbitraria para el servicio (día 1)
    fecha_consulta = datetime(query_anio, query_mes, 1)
    
    # Usar el servicio para obtener O CREAR (y sincronizar) el plan
    # Esto soluciona que meses pasados se vean como "No Iniciado"
    # IMPORTANTE: Se requiere commit? _get_or_create hace flush. Haremos commit al final si es necesario,
    # pero como es un GET, idealmente no debería escribir, pero aqui estamos "inicializando" vista.
    # FastAPI hace commit automático si no hay error al final del request si usamos el dependency correcto, 
    # pero nuestra dependency `get_db` es yield session.
    # Dado que _get_or_create puede escribir, debemos hacer commit explícito si queremos persistir la creación.
    plan = _get_or_create_plan_mensual(db, empresa_id, fecha_consulta)
    try:
        db.commit() # Persistir la creación/sync del plan si era nuevo
    except:
        db.rollback()
    
    # Recargar para asegurar data fresca tras commit
    db.refresh(plan)
    
    # Asignar el plan para la respuesta
    plan_schema = plan

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
    # 3. Recargas y Compras del Periodo
    # Mostramos las que están vigentes (saldo > 0) Y TAMBIÉN todas las compradas en este mes específico
    # para que el cliente vea registro de lo que compró, aunque ya se lo haya gastado.
    from sqlalchemy import or_

    recargas = db.query(RecargaAdicional).filter(
        RecargaAdicional.empresa_id == empresa_id,
        or_(
            RecargaAdicional.estado == EstadoRecarga.VIGENTE,
            (RecargaAdicional.mes == query_mes) & (RecargaAdicional.anio == query_anio)
        )
    ).order_by(asc(RecargaAdicional.fecha_compra)).all()
    
    # Calculo Total DISPONIBLE (Solo sumamos lo disponible real, no lo comprado histórico)
    total = (plan.cantidad_disponible if plan and plan.estado == EstadoPlan.ABIERTO else 0) + \
            sum(b.cantidad_disponible for b in bolsas) + \
            sum(r.cantidad_disponible for r in recargas) # cantidad_disponible será 0 si está agotada
            
    return {
        "plan_actual": plan_schema,
        "bolsas_vigentes": bolsas,
        "recargas_vigentes": recargas,
        "total_disponible": total
    }

@router.get("/historial", response_model=List[HistorialConsumoRead])
def get_historial_consumo(
    skip: int = 0,
    limit: int = 50,
    fecha_inicio: str = Query(None, description="Fecha inicio YYYY-MM-DD"),
    fecha_fin: str = Query(None, description="Fecha fin YYYY-MM-DD"),
    tipo_operacion: str = Query(None, description="Tipo de operación"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Any:
    """
    Obtiene el historial de auditoría de consumos y reversiones con filtros.
    """
    query = db.query(HistorialConsumo).filter(
        HistorialConsumo.empresa_id == current_user.empresa_id
    )

    if fecha_inicio:
        try:
            dt_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            query = query.filter(HistorialConsumo.fecha >= dt_inicio)
        except ValueError:
            pass # Ignorar formato invalido

    if fecha_fin:
        try:
            dt_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            query = query.filter(HistorialConsumo.fecha <= dt_fin)
        except ValueError:
            pass

    if tipo_operacion and tipo_operacion != "TODOS":
        query = query.filter(HistorialConsumo.tipo_operacion == tipo_operacion)

    if tipo_operacion and tipo_operacion != "TODOS":
        query = query.filter(HistorialConsumo.tipo_operacion == tipo_operacion)

    # JOIN con Documento para obtener el número humano (consecutivo)
    from app.models.documento import Documento
    
    # Query proyectada: Traemos el modelo Historial entero + el consecutivo del documento
    # Usamos outerjoin porque no todos los historiales tienen documento (ej: reversión)
    results = query.outerjoin(
        Documento, HistorialConsumo.documento_id == Documento.id
    ).add_columns(
        Documento.numero
    ).order_by(desc(HistorialConsumo.fecha)).offset(skip).limit(limit).all()
    
    # Mapeo de respuesta
    response = []
    for historial_model, doc_nro in results:
        # Pydantic from_attributes=True puede leer atributos de objetos, 
        # pero aquí tenemos una mezcla. Atribuimos el nro al objeto temporalmente o creamos dict.
        # La forma más limpia para Pydantic es pasarle el objeto Historial con el atributo 'inyectado'
        # Ojo: SQLAlchemy models no son diccionarios.
        
        # Estrategia: Usar setattr en el objeto modelo volátil (no guardado) para que el schema lo lea
        setattr(historial_model, "documento_numero", doc_nro)
        response.append(historial_model)

    return response

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
    paquete_id: str = None
    cantidad_custom: int = None
    mes: int = None
    anio: int = None

@router.post("/recargas")
def comprar_paquete_recarga(
    data: CompraRecargaRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Procesa la compra de un paquete o recarga personalizada.
    """
    try:
        if not data.paquete_id and not data.cantidad_custom:
            raise ValueError("Debe especificar un paquete o una cantidad personalizada.")

        # Se pasa mes y año si vienen en el request (para recargas retroactivas)
        recarga = comprar_recarga(
            db, 
            current_user.empresa_id, 
            paquete_id=data.paquete_id,
            cantidad_custom=data.cantidad_custom,
            mes=data.mes,
            anio=data.anio
        )
        return {"status": "success", "message": "Recarga exitosa", "recarga_id": recarga.id}
    except ValueError as e:
        # Re-raise as HTTP 400
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class MarcarPagadaRequest(BaseModel):
    pagado: bool = True

@router.put("/recargas/{recarga_id}/pago")
def marcar_recarga_pagada(
    recarga_id: int,
    data: MarcarPagadaRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Marca una recarga como pagada (facturada=True) o pendiente.
    Esto permite 'dar de baja' el saldo pendiente por cobrar en el dashboard de soporte.
    """
    # En un sistema real, validaríamos que current_user.es_admin o similar.
    # Por ahora asumimos que solo soporte accede a esto.
    
    recarga = db.query(RecargaAdicional).filter(RecargaAdicional.id == recarga_id).first()
    if not recarga:
        raise HTTPException(status_code=404, detail="Recarga no encontrada")
        
    recarga.facturado = data.pagado
    if data.pagado:
        recarga.fecha_facturacion = datetime.now()
    else:
        recarga.fecha_facturacion = None
        
    db.commit()
    return {"status": "success", "message": f"Estado de pago actualizado a {data.pagado}"}
