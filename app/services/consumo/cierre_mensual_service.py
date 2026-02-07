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

    # 1.1 Obtener Empresa para verificar jerarquía
    from app.models.empresa import Empresa
    empresa_obj = db.query(Empresa).get(empresa_id)
    es_hija = empresa_obj.padre_id is not None if empresa_obj else False

    # 2. Traslado Plan -> Bolsa (ELIMINADO - ROLLING QUOTA MODEL)
    # En el nuevo modelo, no se trasladan excedentes. Se quedan en el plan del mes original.
    # El status CERRADO solo indica cierre administrativo, pero el saldo sigue disponible
    # para consumo por otros periodos (FIFO).
    
    # 3. Cerrar Plan
    plan.estado = EstadoPlan.CERRADO.value
    plan.fecha_cierre = now
    # plan.cantidad_disponible = 0  <-- NO HACEMOS ESTO. El saldo queda vivo.
    
    db.add(plan)


    # 4. Expirar Recargas del Mes
    # (Mantenemos esta lógica si se desea que las recargas sean "Use it or lose it" mensual, 
    #  o podríamos dejarlas vivir. Por ahora, respetamos la lógica previa de expiración 
    #  si el cliente no indicó lo contrario para Recargas).
    #  Nota: El cliente dijo "dejar de ultimo las recargas".
    #  Si expiramos las recargas, no las "dejamos de ultimo", las matamos.
    #  Asumiremos que las Recargas Adicionales son PERMANENTES hasta que se agoten (o 1 año).
    #  Por tanto, comentar la expiración forzosa sería lo coherente con "Rolling Quota".
    #  Pero para no cambiar demasiadas reglas a la vez, mantengo la expiración SOLO si era explícito.
    #  El código previo expiraba. Voy a comentar la expiración para ser consistency con el modelo acumulativo.
    
    """
    recargas = db.query(RecargaAdicional).filter(
        RecargaAdicional.empresa_id == empresa_id,
        RecargaAdicional.anio == anio,
        RecargaAdicional.mes == mes,
        RecargaAdicional.estado == EstadoRecarga.VIGENTE
    ).all()
    
    for r in recargas:
         # Expiración logic removed/commented specifically for Rolling Model compatibility.
         # If user wants them to expire, uncomment.
         pass
    """

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
        # SECURITY CHECK (Vulnerability: Reopen abused after usage)
        # Verify if the bag has been touched (Credits consumed)
        # Checking if available < initial is the fastest way.
        if bolsa.cantidad_disponible < bolsa.cantidad_inicial:
             # SECURITY CHECK (Vulnerability: Reopen abused after usage)
             # Logic V2: Allow "Debt Swap" if User has purchased an Extra Recharge sufficient to cover the usage.
             
             deficit = bolsa.cantidad_inicial - bolsa.cantidad_disponible
             
             # Buscar Recarga Adicional VIGENTE con saldo suficiente
             recarga_salvadora = db.query(RecargaAdicional).filter(
                 RecargaAdicional.empresa_id == empresa_id,
                 RecargaAdicional.estado == EstadoRecarga.VIGENTE,
                 RecargaAdicional.cantidad_disponible >= deficit
             ).order_by(RecargaAdicional.fecha_compra.asc()).first() # FIFO (Usar la mas vieja disponible)
             
             if recarga_salvadora:
                 # --- SWAP DEUDOR ---
                 # 1. Debitar de la Recarga
                 recarga_salvadora.cantidad_disponible -= deficit
                 
                 # 2. Migrar los consumos históricos (De Bolsa -> Recarga)
                 # Identificar consumos que apuntan a esta bolsa
                 consumos_bolsa = db.query(HistorialConsumo).filter(
                     HistorialConsumo.fuente_id == bolsa.id,
                     HistorialConsumo.fuente_tipo == TipoFuenteConsumo.BOLSA,
                     HistorialConsumo.tipo_operacion == TipoOperacionConsumo.CONSUMO
                 ).all()
                 
                 for c in consumos_bolsa:
                     c.fuente_tipo = TipoFuenteConsumo.RECARGA
                     c.fuente_id = recarga_salvadora.id
                     # Nota: saldo_fuente_antes/despues quedaran "desactualizados" contextualmente
                     # pero es aceptable para mantener la integridad referencial y permitir el undo.
                 
                 db.add(recarga_salvadora)
                 # Permite continuar hacia la eliminación de la bolsa...
                 
             else:
                 # No hay recarga suficiente -> Bloqueo
                 from fastapi import HTTPException
                 raise HTTPException(
                     status_code=400, 
                     detail=f"NO SE PUEDE REABRIR EL PERIODO: La Bolsa de Excedentes generada ya ha sido utilizada (Déficit: {deficit}). Para reabrir, debe adquirir un Paquete Extra/Recarga con al menos {deficit} registros disponibles para cubrir lo consumido."
                 )
             
        # Si hubo swap (o no se tocó), debemos restaurar AL PLAN la cantidad TOTAL inicial de la bolsa.
        # Por qué?
        # Caso 1 (Intacta): Disponible=Inicial. Se devuelve todo.
        # Caso 2 (Usada + Swap): El déficit se pagó con Recarga. Por tanto, los créditos que formaban ese déficit
        # quedan "liberados" de su obligación de pago. Deben volver al Plan para que la ecuación cuadre.
        # Si solo devolvemos el 'disponible', estamos "quemando" los créditos que refinanciamos.
        
        # Ej:
        # Bolsa: 100. Usado: 80. Disponible: 20.
        # Swap: Paga 80 con Recarga.
        # Devolución al Plan: Debería ser 100.
        # (Porque la Recarga asumió la deuda de 80, y los 20 sobran. Total 100 regresan al origen).
        
        devolucion_plan = bolsa.cantidad_inicial
        
        # ELIMINACION FISICA (Clean Undo)
        # 1. Eliminar Historial de Creación (Tipo CIERRE que apunta a esta bolsa)
        db.query(HistorialConsumo).filter(
            HistorialConsumo.fuente_id == bolsa.id,
            HistorialConsumo.fuente_tipo == TipoFuenteConsumo.BOLSA,
            HistorialConsumo.tipo_operacion == TipoOperacionConsumo.CIERRE
        ).delete()
        
        # 2. Eliminar la Bolsa
        db.delete(bolsa)
        
        # No creamos Historial de Reversión porque hemos eliminado el historial de Cierre.
        # Es como si nunca hubiera pasado.


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
