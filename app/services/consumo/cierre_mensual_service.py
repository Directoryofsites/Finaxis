from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
import calendar
from app.models.consumo_registros import (
    ControlPlanMensual, BolsaExcedente, RecargaAdicional, HistorialConsumo,
    EstadoPlan, EstadoBolsa, EstadoRecarga, TipoOperacionConsumo, TipoFuenteConsumo
)

def ejecutar_cierre_mensual(db: Session, empresa_id: int, anio: int, mes: int, user_id: int = None):
    """
    Cierra el mes especificado y traslada excedentes a Bolsa.
    Vinculado al Cierre de Periodo Contable.
    """
    now = datetime.now()

    # 1. Buscar Plan Mensual
    plan = db.query(ControlPlanMensual).filter(
        ControlPlanMensual.empresa_id == empresa_id,
        ControlPlanMensual.anio == anio,
        ControlPlanMensual.mes == mes
    ).with_for_update().first()
    
    if not plan:
        # Si no existe plan (raro, pero posible si no iniciaron operaciones), no hacemos nada
        return
        
    if plan.estado == EstadoPlan.CERRADO:
        return # Idempotencia

    # 2. Traslado Plan -> Bolsa
    remanente_plan = plan.cantidad_disponible
    if remanente_plan > 0:
        nueva_bolsa = BolsaExcedente(
            empresa_id=empresa_id,
            anio_origen=anio,
            mes_origen=mes,
            cantidad_inicial=remanente_plan,
            cantidad_disponible=remanente_plan,
            fecha_creacion=now,
            # FIX: Vencimiento es 1 año desde el mes de ORIGEN (Fin de mes), no desde la fecha de ejecución
            fecha_vencimiento=datetime(anio + 1, mes, calendar.monthrange(anio + 1, mes)[1], 23, 59, 59),
            estado=EstadoBolsa.VIGENTE
        )
        db.add(nueva_bolsa)
        
        # Log Historial
        historial = HistorialConsumo(
            empresa_id=empresa_id,
            fecha=now,
            cantidad=remanente_plan,
            tipo_operacion=TipoOperacionConsumo.CIERRE,
            fuente_tipo=TipoFuenteConsumo.BOLSA,
            fuente_id=None, # Se asignará tras commit, pero por ahora lo dejamos genérico o requerimos flush
            saldo_fuente_antes=0,
            saldo_fuente_despues=remanente_plan,
            documento_id=None
        )
        db.add(historial)

    # 3. Cerrar Plan
    plan.estado = EstadoPlan.CERRADO.value
    plan.fecha_cierre = now
    plan.cantidad_disponible = 0 # Se vacía porque se movió (o se perdió)
    
    db.add(plan)


    # 4. Expirar Recargas del Mes (Política: Recargas de este mes solo valen para este mes)
    # A MENOS que la política cambie. Asumimos por ahora que mueren si no se usan.
    # El usuario dijo: "lo de las recargas... debe cancelar ese valor".
    # Pero no dijo si el SALDO de las recargas se acumula.
    # Por seguridad y simplicidad inicial, las dejamos VIGENTES si no se dice lo contrario,
    # O las expiramos si esa era la regla previa.
    # En el código anterior propuesto las expiraba. Mantendré eso pero es reversible.
    
    # REGLA: Si recargas son "del mes", deben consumirse o morir, o pasar a bolsa?
    # Usualmente las recargas extra no tienen rollover automático a menos que sea explícito.
    # Voy a EXPIRARLAS para consistencia con el cierre, pero si el usuario reclama, se ajusta.
    recargas = db.query(RecargaAdicional).filter(
        RecargaAdicional.empresa_id == empresa_id,
        RecargaAdicional.anio == anio,
        RecargaAdicional.mes == mes,
        RecargaAdicional.estado == EstadoRecarga.VIGENTE
    ).all()
    
    for r in recargas:
        if r.cantidad_disponible > 0:
            # Log Expiracion
            h_exp = HistorialConsumo(
                empresa_id=empresa_id,
                fecha=now,
                cantidad=r.cantidad_disponible,
                tipo_operacion=TipoOperacionConsumo.EXPIRACION,
                fuente_tipo=TipoFuenteConsumo.RECARGA,
                fuente_id=r.id,
                saldo_fuente_antes=r.cantidad_disponible,
                saldo_fuente_despues=0
            )
            db.add(h_exp)
            r.estado = EstadoRecarga.EXPIRADA
            r.cantidad_disponible = 0

    db.flush()

def revertir_cierre_mensual(db: Session, empresa_id: int, anio: int, mes: int):
    """
    Revierte las acciones de cierre:
    - Devuelve saldo de Bolsa (si existe) al Plan.
    - Anula la Bolsa.
    - Reactiva Recargas expiradas.
    - Abre el Plan.
    """
    
    # 1. Buscar Plan
    plan = db.query(ControlPlanMensual).filter(
        ControlPlanMensual.empresa_id == empresa_id,
        ControlPlanMensual.anio == anio,
        ControlPlanMensual.mes == mes
    ).with_for_update().first()
    
    if not plan:
        return 
        
    if plan.estado != EstadoPlan.CERRADO.value:
        return # Ya está abierto

    # 2. Buscar Bolsa generada por este mes
    # 2. Buscar Bolsa generada por este mes
    bolsa = db.query(BolsaExcedente).filter(
        BolsaExcedente.empresa_id == empresa_id,
        BolsaExcedente.anio_origen == anio,
        BolsaExcedente.mes_origen == mes,
        BolsaExcedente.estado.in_([EstadoBolsa.VIGENTE, EstadoBolsa.AGOTADO]) # Podría estar agotada si se usó
    ).with_for_update().first()
    
    devolucion_plan = 0
    
    if bolsa:
        # Recuperamos lo que le quede
        devolucion_plan = bolsa.cantidad_disponible
        
        # Anulamos la bolsa
        bolsa.cantidad_disponible = 0
        bolsa.estado = EstadoBolsa.ANULADO.value
        db.add(bolsa)
        
        # Log Reversion
        if devolucion_plan > 0:
            db.add(HistorialConsumo(
                empresa_id=empresa_id,
                fecha=datetime.now(),
                cantidad=devolucion_plan,
                tipo_operacion=TipoOperacionConsumo.REVERSION,
                fuente_tipo=TipoFuenteConsumo.PLAN,
                fuente_id=None,
                saldo_fuente_antes=0,
                saldo_fuente_despues=devolucion_plan
            ))

    # 3. Restaurar Plan
    plan.estado = EstadoPlan.ABIERTO.value
    plan.fecha_cierre = None
    plan.cantidad_disponible += devolucion_plan # Sumamos lo devuelto
    
    db.add(plan)
    
    # 4. Reactivar Recargas Expiradas del mes
    # (Solo las que expiraron en este proceso, difícil saber exactamente cuales, 
    # pero asumimos todas las expiradas de este mes origen)
    recargas_expiradas = db.query(RecargaAdicional).filter(
        RecargaAdicional.empresa_id == empresa_id,
        RecargaAdicional.anio == anio,
        RecargaAdicional.mes == mes,
        RecargaAdicional.estado == EstadoRecarga.EXPIRADA
    ).all()
    
    for r in recargas_expiradas:
        # Tratamos de recuperar su saldo original? No tenemos el dato fácil aquí, 
        # PERO en HistorialConsumo de tipo EXPIRACION está la cantidad.
        # Buscar el último historial de expiración para esta recarga
        ultimo_log = db.query(HistorialConsumo).filter(
            HistorialConsumo.fuente_id == r.id,
            HistorialConsumo.fuente_tipo == TipoFuenteConsumo.RECARGA,
            HistorialConsumo.tipo_operacion == TipoOperacionConsumo.EXPIRACION
        ).order_by(HistorialConsumo.id.desc()).first()
        
        cantidad_recuperada = ultimo_log.cantidad if ultimo_log else 0
        
        if cantidad_recuperada > 0:
            r.estado = EstadoRecarga.VIGENTE
            r.cantidad_disponible = cantidad_recuperada
            
    db.flush()
