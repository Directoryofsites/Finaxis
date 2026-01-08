from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc
from datetime import datetime
from fastapi import HTTPException
from app.models.consumo_registros import (
    ControlPlanMensual, BolsaExcedente, RecargaAdicional, HistorialConsumo, PaqueteRecarga,
    EstadoPlan, EstadoBolsa, EstadoRecarga, TipoFuenteConsumo, TipoOperacionConsumo
)


# --- DEFINICIÓN DE PRECIOS (Hardcoded por ahora) ---
PAQUETES_RECARGA = {
    "basic": {"nombre": "Pack Básico", "cantidad": 100, "precio": 15000},
    "pro": {"nombre": "Pack Pro", "cantidad": 500, "precio": 60000},
    "enterprise": {"nombre": "Pack Enterprise", "cantidad": 2000, "precio": 200000},
}

def get_paquetes_activos(db: Session):
    return db.query(PaqueteRecarga).filter(PaqueteRecarga.activo == True).order_by(asc(PaqueteRecarga.precio)).all()

def get_all_paquetes(db: Session):
    return db.query(PaqueteRecarga).order_by(asc(PaqueteRecarga.precio)).all()

def create_paquete(db: Session, nombre: str, cantidad_registros: int, precio: int, activo: bool = True):
    pkg = PaqueteRecarga(nombre=nombre, cantidad_registros=cantidad_registros, precio=precio, activo=activo)
    db.add(pkg)
    db.commit()
    db.refresh(pkg)
    return pkg

def update_paquete(db: Session, paquete_id: int, nombre: str, cantidad_registros: int, precio: int, activo: bool):
    pkg = db.query(PaqueteRecarga).get(paquete_id)
    if not pkg: return None
    pkg.nombre = nombre
    pkg.cantidad_registros = cantidad_registros
    pkg.precio = precio
    pkg.activo = activo
    db.commit()
    db.refresh(pkg)
    return pkg

def delete_paquete(db: Session, paquete_id: int):
    pkg = db.query(PaqueteRecarga).get(paquete_id)
    if not pkg: return False
    db.delete(pkg)
    db.commit()
    return True

def comprar_recarga(db: Session, empresa_id: int, paquete_identifier: str):
    """
    Registra la compra de un paquete de recarga adicional.
    Soporta ID de BD (preferido) o claves hardcoded legacy.
    """
    cantidad = 0
    precio = 0
    
    # 1. Intentar buscar en DB
    if str(paquete_identifier).isdigit():
        paquete_db = db.query(PaqueteRecarga).get(int(paquete_identifier))
        if paquete_db:
            cantidad = paquete_db.cantidad_registros
            precio = paquete_db.precio
    
    # 2. Fallback Legacy
    if cantidad == 0:
        if paquete_identifier in PAQUETES_RECARGA:
            paquete = PAQUETES_RECARGA[paquete_identifier]
            cantidad = paquete["cantidad"]
            precio = paquete["precio"]
        else:
            raise ValueError(f"Paquete de recarga inválido: {paquete_identifier}")
    
    now = datetime.now()
    
    nueva_recarga = RecargaAdicional(
        empresa_id=empresa_id,
        anio=now.year,
        mes=now.month,
        cantidad_comprada=cantidad,
        cantidad_disponible=cantidad,
        fecha_compra=now,
        estado=EstadoRecarga.VIGENTE,
        valor_total=precio,
        facturado=False,
        fecha_facturacion=None
    )
    
    db.add(nueva_recarga)
    db.commit()
    db.refresh(nueva_recarga)
    
    return nueva_recarga
from app.models.empresa import Empresa

class SaldoInsuficienteException(Exception):
    def __init__(self, message: str, detalle: dict = None):
        self.message = message
        self.detalle = detalle
        super().__init__(self.message)

def verificar_disponibilidad(db: Session, empresa_id: int, cantidad_necesaria: int) -> bool:
    """
    Verifica si existe saldo suficiente sumando todas las fuentes VIGENTES.
    NO realiza bloqueos ni modificaciones.
    """
    # 1. Plan Mensual Actual
    # Asumimos mes actual del sistema o recibimos fecha? Mejor usar NOW para disponibilidad inmediata
    now = datetime.now()
    anio, mes = now.year, now.month
    
    plan = db.query(ControlPlanMensual).filter(
        ControlPlanMensual.empresa_id == empresa_id,
        ControlPlanMensual.anio == anio,
        ControlPlanMensual.mes == mes
    ).first()
    
    saldo_plan = plan.cantidad_disponible if plan and plan.estado == EstadoPlan.ABIERTO else 0
    
    # 2. Bolsa Excedente (VIGENTE y NO VENCIDA)
    # Filtro defensivo explícito
    saldo_bolsa = db.query(BolsaExcedente).filter(
        BolsaExcedente.empresa_id == empresa_id,
        BolsaExcedente.estado == EstadoBolsa.VIGENTE,
        BolsaExcedente.fecha_vencimiento >= now
    ).with_entities(BolsaExcedente.cantidad_disponible).all()
    
    total_bolsa = sum([b.cantidad_disponible for b in saldo_bolsa])
    
    # 3. Recargas (VIGENTE)
    saldo_recargas = db.query(RecargaAdicional).filter(
        RecargaAdicional.empresa_id == empresa_id,
        RecargaAdicional.estado == EstadoRecarga.VIGENTE
    ).with_entities(RecargaAdicional.cantidad_disponible).all()
    
    total_recargas = sum([r.cantidad_disponible for r in saldo_recargas])
    
    total_disponible = saldo_plan + total_bolsa + total_recargas
    
    return total_disponible >= cantidad_necesaria

def _get_or_create_plan_mensual(db: Session, empresa_id: int, fecha_doc: datetime) -> ControlPlanMensual:
    anio = fecha_doc.year
    mes = fecha_doc.month
    
    plan = db.query(ControlPlanMensual).filter(
        ControlPlanMensual.empresa_id == empresa_id,
        ControlPlanMensual.anio == anio,
        ControlPlanMensual.mes == mes
    ).with_for_update().first()
    
    if not plan:
        # Recuperar límite de la empresa
        empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
        limite = empresa.limite_registros if empresa.limite_registros is not None else 0 # 0 podría ser ilimitado? Asumamos estricto plan.
        # Regla de negocio: Si no tiene límite configurado, ¿qué hacemos? 
        # Asumiremos un plan básico default o bloqueamos?
        # Para evitar bloqueos totales en migración, si es None asumimos 1000 por defecto temp?
        # Mejor: Si es None -> 0.
        
        plan = ControlPlanMensual(
            empresa_id=empresa_id,
            anio=anio,
            mes=mes,
            limite_asignado=limite,
            cantidad_disponible=limite, # Inicia lleno
            estado=EstadoPlan.ABIERTO
        )
        db.add(plan)
        db.flush() # Para tenerlo disponible
        
    return plan

def registrar_consumo(db: Session, empresa_id: int, cantidad: int, documento_id: int, fecha_doc: datetime):
    """
    Ejecuta el consumo estricto FIFO.
    Lanza SaldoInsuficienteException si falla.
    """
    if cantidad <= 0:
        return # Nada que consumir
        
    # Validacion Previa (Optimista)
    #if not verificar_disponibilidad(db, empresa_id, cantidad):
    #    raise SaldoInsuficienteException("No hay saldo suficiente para esta operación.")
        
    # --- INICIO TRANSACCIÓN DE CONSUMO ---
    
    remanente_a_consumir = cantidad
    
    # 1. PLAN MENSUAL (Del mes del documento)
    # Usamos with_for_update dentro de _get_or_create
    plan_mensual = _get_or_create_plan_mensual(db, empresa_id, fecha_doc)
    
    consumo_plan = 0
    if plan_mensual.estado == EstadoPlan.ABIERTO and plan_mensual.cantidad_disponible > 0:
        disponible = plan_mensual.cantidad_disponible
        a_tomar = min(disponible, remanente_a_consumir)
        
        # Auditoría Snapshot Antes
        saldo_antes = plan_mensual.cantidad_disponible
        
        # Consumir
        plan_mensual.cantidad_disponible -= a_tomar
        remanente_a_consumir -= a_tomar
        consumo_plan = a_tomar
        
        # Registrar Historial
        historial = HistorialConsumo(
            empresa_id=empresa_id,
            cantidad=a_tomar,
            tipo_operacion=TipoOperacionConsumo.CONSUMO,
            fuente_tipo=TipoFuenteConsumo.PLAN,
            fuente_id=None, # Plan se identifica por fecha implícita
            saldo_fuente_antes=saldo_antes,
            saldo_fuente_despues=plan_mensual.cantidad_disponible,
            documento_id=documento_id,
            fecha=datetime.now()
        )
        db.add(historial)
        
    if remanente_a_consumir == 0:
        return # Éxito total solo con plan

    # 2. BOLSA EXCEDENTE (FIFO)
    # Buscar tramos VIGENTES ordenados por antigüedad
    now = datetime.now()
    tramos_bolsa = db.query(BolsaExcedente).filter(
        BolsaExcedente.empresa_id == empresa_id,
        BolsaExcedente.estado == EstadoBolsa.VIGENTE,
        BolsaExcedente.fecha_vencimiento >= now
    ).order_by(asc(BolsaExcedente.fecha_vencimiento)).with_for_update().all()
    
    for tramo in tramos_bolsa:
        if remanente_a_consumir <= 0:
            break
            
        disponible = tramo.cantidad_disponible
        if disponible <= 0: 
            continue
            
        a_tomar = min(disponible, remanente_a_consumir)
        
        saldo_antes = tramo.cantidad_disponible
        
        tramo.cantidad_disponible -= a_tomar
        remanente_a_consumir -= a_tomar
        
        # Actualizar estado si se agota
        if tramo.cantidad_disponible == 0:
            tramo.estado = EstadoBolsa.AGOTADO
            
        # Historial
        historial = HistorialConsumo(
            empresa_id=empresa_id,
            cantidad=a_tomar,
            tipo_operacion=TipoOperacionConsumo.CONSUMO,
            fuente_tipo=TipoFuenteConsumo.BOLSA,
            fuente_id=tramo.id,
            saldo_fuente_antes=saldo_antes,
            saldo_fuente_despues=tramo.cantidad_disponible,
            documento_id=documento_id,
            fecha=datetime.now()
        )
        db.add(historial)

    if remanente_a_consumir == 0:
        return

    # 3. RECARGAS ADICIONALES
    tramos_recarga = db.query(RecargaAdicional).filter(
        RecargaAdicional.empresa_id == empresa_id,
        RecargaAdicional.estado == EstadoRecarga.VIGENTE
    ).order_by(asc(RecargaAdicional.fecha_compra)).with_for_update().all()
    
    for recarga in tramos_recarga:
        if remanente_a_consumir <= 0:
            break
            
        disponible = recarga.cantidad_disponible
        if disponible <= 0:
            continue
            
        a_tomar = min(disponible, remanente_a_consumir)
        
        saldo_antes = recarga.cantidad_disponible
        
        recarga.cantidad_disponible -= a_tomar
        remanente_a_consumir -= a_tomar
        
        if recarga.cantidad_disponible == 0:
            recarga.estado = EstadoRecarga.AGOTADA
            
        historial = HistorialConsumo(
            empresa_id=empresa_id,
            cantidad=a_tomar,
            tipo_operacion=TipoOperacionConsumo.CONSUMO,
            fuente_tipo=TipoFuenteConsumo.RECARGA,
            fuente_id=recarga.id,
            saldo_fuente_antes=saldo_antes,
            saldo_fuente_despues=recarga.cantidad_disponible,
            documento_id=documento_id,
            fecha=datetime.now()
        )
        db.add(historial)

    # FINAL CHECK
    if remanente_a_consumir > 0:
        # Falla atómica: Si llegamos aquí es que realmente no alcanzó a pesar de todo.
        # Como hemos modificado objetos en session pero no commit, el caller debe hacer rollback.
        raise SaldoInsuficienteException(
            f"Saldo insuficiente. Faltan {remanente_a_consumir} registros para completar la operación.",
            detalle={"faltante": remanente_a_consumir}
        )

def revertir_consumo(db: Session, documento_id: int):
    """
    Revierte TODO el consumo asociado a un documento.
    Restaura el saldo a la fuente original SI es posible, o al Plan Actual.
    """
    # 1. Buscar todo el historial de consumo de este documento
    consumos_previos = db.query(HistorialConsumo).filter(
        HistorialConsumo.documento_id == documento_id,
        HistorialConsumo.tipo_operacion == TipoOperacionConsumo.CONSUMO
    ).all()
    
    if not consumos_previos:
        return # No hubo consumo registrado (tal vez era documento viejo o sin costo)
        
    now = datetime.now()
    plan_actual = _get_or_create_plan_mensual(db, consumos_previos[0].empresa_id, now)
    
    for consumo in consumos_previos:
        cantidad_a_devolver = consumo.cantidad
        fuente_destino = None
        tipo_destino = None # Para log
        
        # Intento de restauración a fuente original
        if consumo.fuente_tipo == TipoFuenteConsumo.PLAN:
            # Plan Mensual original
            # El plan mensual "original" es difícil de rastrear directamente por ID (es null),
            # pero podemos inferirlo de la fecha del consumo o documento original?
            # En el modelo Historial NO guardamos el año/mes del plan, solo 'PLAN'.
            # Asumiremos que si fue PLAN, tratamos de devolver al Plan del DOCUMENTO original o al ACTUAL?
            # Regla defensiva: Devolver al Plan ACTUAL es lo más seguro y beneficioso para el usuario.
            # Salvo que queramos reactivar un plan viejo.
            # Dado que el 'bolsillo' es el plan, lo devolvemos al Plan Actual que es donde lo necesita hoy.
            fuente_destino = plan_actual
            tipo_destino = TipoFuenteConsumo.PLAN
            
        elif consumo.fuente_tipo == TipoFuenteConsumo.BOLSA:
            bolsa = db.query(BolsaExcedente).get(consumo.fuente_id)
            if bolsa and bolsa.estado in [EstadoBolsa.VIGENTE, EstadoBolsa.AGOTADO] and bolsa.fecha_vencimiento >= now:
                fuente_destino = bolsa
                tipo_destino = TipoFuenteConsumo.BOLSA
                # Si estaba agotado, lo revivimos
                if bolsa.estado == EstadoBolsa.AGOTADO:
                    bolsa.estado = EstadoBolsa.VIGENTE
            else:
                # Bolsa vencida o inexistente -> Plan Actual
                fuente_destino = plan_actual
                tipo_destino = TipoFuenteConsumo.PLAN
                
        elif consumo.fuente_tipo == TipoFuenteConsumo.RECARGA:
            recarga = db.query(RecargaAdicional).get(consumo.fuente_id)
            if recarga and recarga.estado in [EstadoRecarga.VIGENTE, EstadoRecarga.AGOTADA]:
                fuente_destino = recarga
                tipo_destino = TipoFuenteConsumo.RECARGA
                if recarga.estado == EstadoRecarga.AGOTADA:
                    recarga.estado = EstadoRecarga.VIGENTE
            else:
                # Recarga expirada -> Plan Actual
                fuente_destino = plan_actual
                tipo_destino = TipoFuenteConsumo.PLAN
        
        # Ejecutar devolución
        saldo_antes = fuente_destino.cantidad_disponible
        fuente_destino.cantidad_disponible += cantidad_a_devolver
        
        # Registrar Historial de Reversión
        log_reversion = HistorialConsumo(
            empresa_id=consumo.empresa_id,
            cantidad=cantidad_a_devolver, # Positivo porque 'añadimos' saldo
            tipo_operacion=TipoOperacionConsumo.REVERSION,
            fuente_tipo=tipo_destino,
            fuente_id=fuente_destino.id if tipo_destino != TipoFuenteConsumo.PLAN else None,
            saldo_fuente_antes=saldo_antes,
            saldo_fuente_despues=fuente_destino.cantidad_disponible,
            documento_id=documento_id,
            fecha=now
        )
        db.add(log_reversion)
