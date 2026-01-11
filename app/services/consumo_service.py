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

def comprar_recarga(db: Session, empresa_id: int, paquete_id: str = None, cantidad_custom: int = None, mes: int = None, anio: int = None):
    """
    Registra la compra de un paquete de recarga adicional.
    Soporta ID de BD (preferido), claves hardcoded legacy, o cantidad personalizada.
    """
    from app.models.configuracion_sistema import ConfiguracionSistema # Import local to avoid circular deps if any
    from sqlalchemy import inspect

    cantidad = 0
    valor_total = 0
    
    # 1. Determinar Cantidad y Precio
    if paquete_id:
        # A. Por Paquete (Legacy o DB)
        if paquete_id in PAQUETES_RECARGA:
            pkg = PAQUETES_RECARGA[paquete_id]
            cantidad = pkg["cantidad"]
            valor_total = pkg["precio"]
        elif str(paquete_id).isdigit():
             # Fallback: Buscar en DB por ID
             pkg_db = db.query(PaqueteRecarga).get(int(paquete_id))
             if pkg_db:
                 cantidad = pkg_db.cantidad_registros
                 valor_total = pkg_db.precio
             else:
                 raise ValueError(f"Paquete ID {paquete_id} no encontrado")
        else:
            raise ValueError(f"Paquete {paquete_id} no válido.")

    elif cantidad_custom and cantidad_custom > 0:
        # B. Personalizado
        # Prioridad 1: Precio específico de la empresa
        empresa_obj = db.query(Empresa).filter(Empresa.id == empresa_id).first()
        precio_empresa = empresa_obj.precio_por_registro if empresa_obj else None

        if precio_empresa is not None and precio_empresa > 0:
             precio_unitario = precio_empresa
        else:
             # Prioridad 2: Precio Global del Sistema
             if inspect(db.get_bind()).has_table("configuracion_sistema"):
                  config_p = db.query(ConfiguracionSistema).filter_by(clave="PRECIO_POR_REGISTRO").first()
                  precio_unitario = int(config_p.valor) if config_p else 150
             else:
                  precio_unitario = 150
             
        cantidad = cantidad_custom
        valor_total = cantidad * precio_unitario
        
    else:
        raise ValueError("Debe indicar un paquete o una cantidad personalizada válida.")
    
    now = datetime.now()
    
    # Usar mes/año proporcionado o actual
    target_year = anio if anio else now.year
    target_month = mes if mes else now.month
    
    nueva_recarga = RecargaAdicional(
        empresa_id=empresa_id,
        anio=target_year,
        mes=target_month,
        cantidad_comprada=cantidad,
        cantidad_disponible=cantidad,
        fecha_compra=now, 
        estado=EstadoRecarga.VIGENTE,
        valor_total=valor_total,
        facturado=False,
        fecha_facturacion=None
    )
    
    db.add(nueva_recarga)
    db.flush() # Para obtener ID
    
    # Registrar Historial de COMPRA
    historial = HistorialConsumo(
        empresa_id=empresa_id,
        cantidad=cantidad,
        tipo_operacion=TipoOperacionConsumo.COMPRA,
        fuente_tipo=TipoFuenteConsumo.RECARGA,
        fuente_id=nueva_recarga.id,
        saldo_fuente_antes=0,
        saldo_fuente_despues=cantidad,
        documento_id=None,
        fecha=now
    )
    db.add(historial)
    
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
    
    # Imports necesarios para el sync
    from app.models.documento import Documento
    from app.models.movimiento_contable import MovimientoContable
    from sqlalchemy import func, extract
    from app.models.empresa import Empresa # Ensure import
    from app.models.cupo_adicional import CupoAdicional # Importar modelo Cupo

    plan = db.query(ControlPlanMensual).filter(
        ControlPlanMensual.empresa_id == empresa_id,
        ControlPlanMensual.anio == anio,
        ControlPlanMensual.mes == mes
    ).with_for_update().first()
    
    # 1. Obtener límite BASE de la empresa
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    limite_base = empresa.limite_registros if empresa and empresa.limite_registros is not None else 0
    
    # 2. Obtener CUPO ADICIONAL para este mes específico
    cupo_adicional = db.query(CupoAdicional).filter(
        CupoAdicional.empresa_id == empresa_id,
        CupoAdicional.anio == anio,
        CupoAdicional.mes == mes
    ).first()
    cantidad_extra = cupo_adicional.cantidad_adicional if cupo_adicional else 0
    
    # LIMIT TOTAL REAL = Base + Adicional
    limite_total = limite_base + cantidad_extra
    
    # Calcular Consumo Real (Siempre útil para sync)
    consumo_real = db.query(func.count(MovimientoContable.id))\
        .join(Documento, MovimientoContable.documento_id == Documento.id)\
        .filter(
            Documento.empresa_id == empresa_id,
            extract('year', Documento.fecha) == anio,
            extract('month', Documento.fecha) == mes,
            Documento.anulado == False
        ).scalar() or 0

    if not plan:
        # CREACIÓN NUEVA
        disponible_inicial = max(0, limite_total - consumo_real)
        
        plan = ControlPlanMensual(
            empresa_id=empresa_id,
            anio=anio,
            mes=mes,
            limite_asignado=limite_total,
            cantidad_disponible=disponible_inicial,
            estado=EstadoPlan.ABIERTO
        )
        db.add(plan)
        db.flush()
        
    else:
        # Si está CERRADO, no tocamos nada, respetamos el cierre (cantidad=0 usualmente)
        # Usamos .value por si el ORM devuelve string
        if plan.estado == EstadoPlan.CERRADO.value or plan.estado == "CERRADO":
            return plan

        # AUTO-HEALING / SYNC CONTINUO
        # Verificamos si el límite total ha cambiado (por cambio de plan o nuevo cupo adicional)
        
        # FIX: Si el plan es MANUAL, no tocamos el límite asignado (respetamos la decisión de soporte)
        if plan.es_manual:
             return plan

        limit_mismatch = (plan.limite_asignado != limite_total and limite_total > 0)
        
        if limit_mismatch:
            plan.limite_asignado = limite_total
            # Recalcular disponible
            plan.cantidad_disponible = max(0, limite_total - consumo_real)
            db.add(plan)
            db.flush()

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
            
        db.add(tramo) # Explicit add for safety

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
