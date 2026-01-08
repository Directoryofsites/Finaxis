from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from app.models.consumo_registros import (
    ControlPlanMensual, BolsaExcedente, RecargaAdicional, HistorialConsumo,
    EstadoPlan, EstadoBolsa, EstadoRecarga, TipoOperacionConsumo, TipoFuenteConsumo
)
from app.models.empresa import Empresa

def ejecutar_cierre_mensual(db: Session, empresa_id: int, anio: int, mes: int):
    """
    Cierra el mes especificado y ejecuta las reglas de negocio de transición:
    1. Plan Mensual -> Bolsa Excedente (Vigencia 12 meses).
    2. Recargas -> Expiran (Regla: No pasan a bolsa).
    3. Depuración -> Tramos de Bolsa vencidos pasan a VENCIDO.
    
    Este proceso es idempotente. Si el mes ya está cerrado, no hace nada crítico.
    """
    
    # 1. Buscar Plan Mensual y Cerrarlo
    plan = db.query(ControlPlanMensual).filter(
        ControlPlanMensual.empresa_id == empresa_id,
        ControlPlanMensual.anio == anio,
        ControlPlanMensual.mes == mes
    ).with_for_update().first()
    
    if not plan:
        # Si no existe plan, no hay nada que cerrar, pero podemos depurar.
        # Podríamos crearlo y cerrarlo para consistencia? No es necesario.
        return 
        
    if plan.estado == EstadoPlan.CERRADO:
        print(f"Mes {anio}-{mes} ya cerrado para empresa {empresa_id}.")
        return

    # LOGICA DE TRASLADO PLAN -> BOLSA
    remanente_plan = plan.cantidad_disponible
    if remanente_plan > 0:
        # Crear Bolsa Excedente
        nueva_bolsa = BolsaExcedente(
            empresa_id=empresa_id,
            anio_origen=anio,
            mes_origen=mes,
            cantidad_inicial=remanente_plan,
            cantidad_disponible=remanente_plan,
            fecha_creacion=datetime.now(),
            fecha_vencimiento=datetime.now() + timedelta(days=365), # 1 año vigencia
            estado=EstadoBolsa.VIGENTE
        )
        db.add(nueva_bolsa)
        
        # Historial (Opcional, pero bueno para trazabilidad del nacimiento de la bolsa)
        # Podríamos registrar un evento tipo "CIERRE"
        pass
        
    # Cerrar Plan
    plan.estado = EstadoPlan.CERRADO
    plan.fecha_cierre = datetime.now()
    plan.cantidad_disponible = 0 # Visualmente 0 porque ya se movió a Bolsa (o se perdió si era política distinta, pero aquí movemos)
    
    # LOGICA DE CADUCIDAD RECARGAS (Regla: Solo vigentes en SU mes)
    # Buscamos recargas de ESTE mes que estamos cerrando
    recargas_mes = db.query(RecargaAdicional).filter(
        RecargaAdicional.empresa_id == empresa_id,
        RecargaAdicional.anio == anio,
        RecargaAdicional.mes == mes,
        RecargaAdicional.estado == EstadoRecarga.VIGENTE
    ).with_for_update().all()
    
    for recarga in recargas_mes:
        saldo_sobrante = recarga.cantidad_disponible
        if saldo_sobrante > 0:
            recarga.estado = EstadoRecarga.EXPIRADA
            # No se transfiere a bolsa
            
            # Historial Expiración
            historial = HistorialConsumo(
                empresa_id=empresa_id,
                fecha=datetime.now(),
                cantidad=saldo_sobrante, # Cantidad perdida
                tipo_operacion=TipoOperacionConsumo.EXPIRACION,
                fuente_tipo=TipoFuenteConsumo.RECARGA,
                fuente_id=recarga.id,
                saldo_fuente_antes=saldo_sobrante,
                saldo_fuente_despues=0,
                documento_id=None
            )
            db.add(historial)
            recarga.cantidad_disponible = 0 # Limpieza visual

    # LOGICA DE DEPURACION BOLSA VENCIDA
    # Buscar tramos de bolsa de cualquier fecha que ya hayan vencido hoy
    now = datetime.now()
    tramos_vencidos = db.query(BolsaExcedente).filter(
        BolsaExcedente.empresa_id == empresa_id,
        BolsaExcedente.estado == EstadoBolsa.VIGENTE,
        BolsaExcedente.fecha_vencimiento < now
    ).with_for_update().all()
    
    for tramo in tramos_vencidos:
        saldo = tramo.cantidad_disponible
        tramo.estado = EstadoBolsa.VENCIDO
        
        if saldo > 0:
             historial = HistorialConsumo(
                empresa_id=empresa_id,
                fecha=now,
                cantidad=saldo,
                tipo_operacion=TipoOperacionConsumo.EXPIRACION,
                fuente_tipo=TipoFuenteConsumo.BOLSA,
                fuente_id=tramo.id,
                saldo_fuente_antes=saldo,
                saldo_fuente_despues=0,
                documento_id=None
            )
             db.add(historial)
        
        tramo.cantidad_disponible = 0

    pass
