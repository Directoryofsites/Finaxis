from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import date
from dateutil.relativedelta import relativedelta
from typing import List

# --- INICIO DE LA CORRECCIÓN CLAVE ---
# Se corrige la ruta de importación para que apunte a los archivos correctos
from ..models.periodo_contable_cerrado import PeriodoContableCerrado
from ..models.empresa import Empresa
from ..schemas import periodo as schemas
from app.services.consumo.cierre_mensual_service import ejecutar_cierre_mensual, revertir_cierre_mensual

def cerrar_periodo(db: Session, empresa_id: int, ano: int, mes: int, user_id: int):
    """
    Cierra un período contable, aplicando validaciones de negocio.
    AHORA ACEPTA año y mes como enteros directamente.
    """
    # 1. Validar que el período no esté ya cerrado
    existente = db.query(PeriodoContableCerrado).filter(
        PeriodoContableCerrado.empresa_id == empresa_id,
        PeriodoContableCerrado.ano == ano,
        PeriodoContableCerrado.mes == mes
    ).first()
    if existente:
        raise HTTPException(status_code=409, detail=f"El período {mes}/{ano} ya se encuentra cerrado.")

    # 2. Validar cierre secuencial (lógica clave)
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa or not empresa.fecha_inicio_operaciones:
        raise HTTPException(status_code=404, detail="No se encontró la empresa o su fecha de inicio de operaciones.")

    fecha_inicio_op = empresa.fecha_inicio_operaciones
    periodo_a_cerrar = date(ano, mes, 1)

    # Validación: No se puede cerrar un período anterior al inicio de operaciones.
    if periodo_a_cerrar.year < fecha_inicio_op.year or \
       (periodo_a_cerrar.year == fecha_inicio_op.year and periodo_a_cerrar.month < fecha_inicio_op.month):
        raise HTTPException(
            status_code=409,
            detail=f"No se puede cerrar el período {mes}/{ano} porque es anterior a la fecha de inicio de operaciones ({fecha_inicio_op.strftime('%m/%Y')})."
        )

    es_primer_periodo_operativo = (
        periodo_a_cerrar.year == fecha_inicio_op.year and
        periodo_a_cerrar.month == fecha_inicio_op.month
    )

    if not es_primer_periodo_operativo:
        periodo_anterior = periodo_a_cerrar - relativedelta(months=1)
        ano_anterior = periodo_anterior.year
        mes_anterior = periodo_anterior.month

        periodo_anterior_cerrado = db.query(PeriodoContableCerrado).filter(
            PeriodoContableCerrado.empresa_id == empresa_id,
            PeriodoContableCerrado.ano == ano_anterior,
            PeriodoContableCerrado.mes == mes_anterior
        ).first()
        if not periodo_anterior_cerrado:
            raise HTTPException(status_code=409, detail=f"No se puede cerrar el período {mes}/{ano} porque el período anterior ({mes_anterior}/{ano_anterior}) está abierto.")

    # 3. Si todas las validaciones pasan, ejecutar logica de Negocio de Consumo y crear registro
    
    # --- PROCESO DE CIERRE DE CONSUMO (TRASLADO EXCEDENTES) ---
    ejecutar_cierre_mensual(db, empresa_id, ano, mes, user_id)
    
    db_periodo = PeriodoContableCerrado(
        empresa_id=empresa_id,
        ano=ano,
        mes=mes,
        cerrado_por_usuario_id=user_id  # <--- Usamos el user_id que ahora pasamos como parámetro
    )
    db.add(db_periodo)
    db.commit()
    db.refresh(db_periodo)
    return db_periodo

def reabrir_periodo(db: Session, empresa_id: int, ano: int, mes: int):
    """
    Reabre un período contable, eliminando el registro de bloqueoy revirtiendo cierre consumo.
    """
    # 1. Validar que no se pueda reabrir un período si el siguiente está cerrado
    fecha_periodo_actual = date(ano, mes, 1)
    fecha_periodo_siguiente = fecha_periodo_actual + relativedelta(months=1)
    ano_siguiente = fecha_periodo_siguiente.year
    mes_siguiente = fecha_periodo_siguiente.month
    periodo_siguiente_cerrado = db.query(PeriodoContableCerrado).filter(
        PeriodoContableCerrado.empresa_id == empresa_id,
        PeriodoContableCerrado.ano == ano_siguiente,
        PeriodoContableCerrado.mes == mes_siguiente
    ).first()

    if periodo_siguiente_cerrado:
        raise HTTPException(status_code=409, detail=f"No se puede reabrir el período {mes}/{ano} porque el período siguiente ({mes_siguiente}/{ano_siguiente}) está cerrado.")

    # 2. Buscar y eliminar el registro de bloqueo
    db_periodo = db.query(PeriodoContableCerrado).filter(
        PeriodoContableCerrado.empresa_id == empresa_id,
        PeriodoContableCerrado.ano == ano,
        PeriodoContableCerrado.mes == mes
    ).first()

    if not db_periodo:
        raise HTTPException(status_code=404, detail=f"El período {mes}/{ano} no se encuentra cerrado.")

    # --- PROCESO DE REVERSION CONSUMO ---
    revertir_cierre_mensual(db, empresa_id, ano, mes)

    db.delete(db_periodo)
    db.commit()
    return {"message": f"Período {mes}/{ano} reabierto exitosamente."}


def get_periodos_cerrados_por_empresa(db: Session, empresa_id: int) -> List[PeriodoContableCerrado]:
    """
    Obtiene todos los períodos cerrados para una empresa, ordenados del más reciente al más antiguo.
    """
    return db.query(PeriodoContableCerrado).filter(
        PeriodoContableCerrado.empresa_id == empresa_id
    ).order_by(
        PeriodoContableCerrado.ano.desc(),
        PeriodoContableCerrado.mes.desc()
    ).all()

# --- AGREGAR ESTO AL FINAL DE app/services/periodo.py ---

def validar_periodo_abierto(db: Session, empresa_id: int, fecha_operacion: date):
    """
    Función Guardián: Verifica si una fecha pertenece a un período cerrado.
    Si está cerrado, LANZA UNA EXCEPCIÓN (HTTP 409) bloqueando la operación.
    """
    periodo_cerrado = db.query(PeriodoContableCerrado).filter(
        PeriodoContableCerrado.empresa_id == empresa_id,
        PeriodoContableCerrado.ano == fecha_operacion.year,
        PeriodoContableCerrado.mes == fecha_operacion.month
    ).first()

    if periodo_cerrado:
        raise HTTPException(
            status_code=409,
            detail=f"⛔ BLOQUEO CONTABLE: El período {fecha_operacion.month}/{fecha_operacion.year} está CERRADO. No se pueden crear, modificar ni anular documentos en esta fecha."
        )
    
    # Si pasa, no retorna nada (silencio positivo), permitiendo que el flujo continúe.

    