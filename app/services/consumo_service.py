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



def calcular_deficit(db: Session, empresa_id: int, cantidad_necesaria: int) -> int:
    # Simplemente reusamos lógica base, si tiene padre delegamos
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    
    # --- LOGICA HIJA -> PADRE ---
    if empresa and empresa.padre_id:
        # A. Validación Local (Cupo Asignado) -> ELIMINADA PARA MODELO SHARED WALLET
        # pass

        # B. Validación Global (Saldo del Padre)
        return calcular_deficit(db, empresa.padre_id, cantidad_necesaria)
        
    """
    Calcula cuántos registros faltan para cubrir una operación.
    Retorna 0 si hay saldo suficiente.
    Retorna > 0 con la cantidad faltante.
    """
    now = datetime.now()
    anio, mes = now.year, now.month
    
    # 1. Plan Mensual
    plan = db.query(ControlPlanMensual).filter(
        ControlPlanMensual.empresa_id == empresa_id,
        ControlPlanMensual.anio == anio,
        ControlPlanMensual.mes == mes
    ).first()
    
    saldo_plan = plan.cantidad_disponible if plan and plan.estado == EstadoPlan.ABIERTO else 0
    
    # 2. Bolsas
    saldo_bolsa = db.query(BolsaExcedente).filter(
        BolsaExcedente.empresa_id == empresa_id,
        BolsaExcedente.estado == EstadoBolsa.VIGENTE,
        BolsaExcedente.fecha_vencimiento >= now
    ).with_entities(BolsaExcedente.cantidad_disponible).all()
    total_bolsa = sum([b.cantidad_disponible for b in saldo_bolsa])
    
    # 3. Recargas
    saldo_recargas = db.query(RecargaAdicional).filter(
        RecargaAdicional.empresa_id == empresa_id,
        RecargaAdicional.estado == EstadoRecarga.VIGENTE
    ).with_entities(RecargaAdicional.cantidad_disponible).all()
    total_recargas = sum([r.cantidad_disponible for r in saldo_recargas])
    
    total_disponible = saldo_plan + total_bolsa + total_recargas
    
    if total_disponible >= cantidad_necesaria:
        return 0
    
    return cantidad_necesaria - total_disponible

def _get_or_create_plan_mensual(db: Session, empresa_id: int, fecha_doc: datetime, exclude_document_id: int = None) -> ControlPlanMensual:
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
    
    # MODIFICADO MULTI-TENANCY:
    # Si tiene padre (es hija), el ControlPlanMensual actúa como "Monitor de Cupo".
    # Su límite es el 'limite_registros_mensual' asignado administrativamente.
    # Si es Independiente/Padre, su límite es 'limite_registros' del plan comprado.
    if empresa and empresa.padre_id:
        limite_base = empresa.limite_registros_mensual if empresa.limite_registros_mensual is not None else 0
    else:
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
    query_consumo = db.query(func.count(MovimientoContable.id))\
        .join(Documento, MovimientoContable.documento_id == Documento.id)\
        .filter(
            Documento.empresa_id == empresa_id,
            extract('year', Documento.fecha) == anio,
            extract('month', Documento.fecha) == mes,
            Documento.anulado == False
        )
    
    # FIX: Excluir documento actual para evitar doble conteo durante auto-healing
    # Si excluimos el doc actual, el consumo_real será lo que había ANTES de esta transacción.
    if exclude_document_id:
        query_consumo = query_consumo.filter(Documento.id != exclude_document_id)

    consumo_real = query_consumo.scalar() or 0

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
        # Si está CERRADO, permitimos el Recálculo de Disponibilidad (para corregir discrepancias)
        # pero EVITAMOS cambiar el límite asignado (para mantener la foto histórica administrativa).
        
        # if plan.estado == EstadoPlan.CERRADO.value or plan.estado == "CERRADO":
        #    return plan  <-- REMOVIDO para permitir sync de saldos

        # FIX: Si el plan es MANUAL, no tocamos el límite asignado (respetamos la decisión de soporte)
        if plan.es_manual:
             pass # Continuar a sanity check, pero no tocar límite

        # AUTO-HEALING / SYNC CONTINUO
        # Verificamos si el límite total ha cambiado (por cambio de plan o nuevo cupo adicional)
        
        # Solo actualizamos LÍMITES si está ABIERTO. Si está cerrado, el límite es sagrado.
        if plan.estado != EstadoPlan.CERRADO.value and plan.estado != "CERRADO":
            limit_mismatch = (plan.limite_asignado != limite_total and limite_total > 0)
            
            # Sync simple de límite
            # Sync inteligente de límite: Preservamos el consumo realizado al actualizar el límite.
            if limit_mismatch and not plan.es_manual:
                 old_limit = plan.limite_asignado if plan.limite_asignado is not None else 0
                 diff = limite_total - old_limit
                 plan.limite_asignado = limite_total
                 plan.cantidad_disponible += diff
                 # Nota: Ajustamos 'plan.cantidad_disponible' por el delta, confiando en que refleja el consumo acumulado (incluyendo hijos)

        # RECALCULO DE DISPONIBILIDAD (Sanity Check)
        # MODIFICADO: Usar HistorialConsumo como fuente de verdad para el "Esperado".
        # El conteo simple de Documentos falla si hay "Cupo Rodante" (Consumo diferido).
        
        # 1. Calcular Uso Real de ESTE Plan (Suma de Historial donde este plan fue la fuente)
        # Incluye consumos hechos en ESTE mes y en FUTUROS meses (si se tomó prestado)
        consumo_ledger = db.query(func.sum(HistorialConsumo.cantidad)).filter(
            HistorialConsumo.fuente_id == plan.id,
            HistorialConsumo.fuente_tipo.in_([TipoFuenteConsumo.PLAN, 'PLAN_PASADO']),
            HistorialConsumo.tipo_operacion == TipoOperacionConsumo.CONSUMO
        ).scalar() or 0
        
        reversiones_ledger = db.query(func.sum(HistorialConsumo.cantidad)).filter(
            HistorialConsumo.fuente_id == plan.id,
            HistorialConsumo.fuente_tipo.in_([TipoFuenteConsumo.PLAN, 'PLAN_PASADO']),
            HistorialConsumo.tipo_operacion == TipoOperacionConsumo.REVERSION
        ).scalar() or 0
        
        uso_neto_plan = consumo_ledger - reversiones_ledger
        
        esperado = max(0, limite_total - uso_neto_plan)
        
        should_heal = False
        
        # Corrección: El "Esperado" (Ledger) debería coincidir con el "Disponible" (Snapshot).
        # Permitimos una tolerancia mínima.
        if plan.cantidad_disponible != esperado:
             should_heal = True
             print(f"[AUTO-HEAL] Corrigiendo Plan {plan.id} ({mes}/{anio}). DB({plan.cantidad_disponible}) -> Calc({esperado}). Ledger: -{consumo_ledger} +{reversiones_ledger}")

        if should_heal:
             plan.cantidad_disponible = esperado
             db.add(plan)
             db.flush() # Commit parcial
             
             # Nota: Eliminamos la lógica recursiva de "Familia" porque el HistorialConsumo
             # YA tiene registrado quién consumió (hijos, nietos, etc) apuntando a este FuenteID.
             # El Historial es la verdad absoluta.

    return plan

def registrar_consumo(db: Session, empresa_id: int, cantidad: int, documento_id: int, fecha_doc: datetime):
    """
    Ejecuta el consumo estricto.
    Si es Hija: Valida Cupo Local y DEBITA Saldo del Padre.
    """
    if cantidad <= 0: return
        
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    
    # --- LOGICA HIJA -> PADRE ---
    # --- LOGICA HIJA -> PADRE ---
    if empresa and empresa.padre_id:
        # 1. Validar Cupo Local (Freno de Mano) -> ELIMINADO
        # Mantenemos el objeto monitor_cupo solo para actualizar estadísticas después.
        monitor_cupo = _get_or_create_plan_mensual(db, empresa_id, fecha_doc, exclude_document_id=documento_id)
        
        # if monitor_cupo.limite_asignado > 0:
             # if monitor_cupo.cantidad_disponible < cantidad:
                  # raise SaldoInsuficienteException(...)
        
        # 2. Si pasa el filtro local, DEBITAR AL PADRE
        # Delegamos recursivamente el débito real al padre.
        try:
            registrar_consumo(db, empresa.padre_id, cantidad, documento_id=documento_id, fecha_doc=fecha_doc)
        except SaldoInsuficienteException as e:
            raise SaldoInsuficienteException(f"Proveedor de servicios sin saldo: {str(e)}")
            
        # 3. Actualizar Monitor Local (Reflejar el consumo realizado)
        monitor_cupo.cantidad_disponible -= cantidad
        db.add(monitor_cupo)
        
        return # Fin flujo Hija


    # --- LÓGICA ESTÁNDAR (Padre / Independiente) ---
    
    remanente_a_consumir = cantidad
    
    # 1. OBTENER CANDIDATOS: PLAN ACTUAL Y PLANES ANTERIORES (FIFO)
    # El usuario requiere que se consuma SIEMPRE del mes más antiguo disponible.
    # Por tanto, construimos una lista ordenada cronológicamente: [Planes Pasados] + [Plan Actual]
    
    plan_mensual = _get_or_create_plan_mensual(db, empresa_id, fecha_doc, exclude_document_id=documento_id)
    
    # A. Buscar Planes Anteriores (Rolling Quota / FIFO)
    now = datetime.now()
    anio_limite = now.year - 1 

    empresa_obj = db.query(Empresa).get(empresa_id)
    start_filter = True 
    ref_date = empresa_obj.fecha_inicio_operaciones if empresa_obj.fecha_inicio_operaciones else empresa_obj.created_at

    if ref_date:
        if isinstance(ref_date, datetime):
            c_year = ref_date.year
            c_month = ref_date.month
        else:
            c_year = ref_date.year
            c_month = ref_date.month
            
        from sqlalchemy import or_
        start_filter = or_(
            ControlPlanMensual.anio > c_year,
            and_(ControlPlanMensual.anio == c_year, ControlPlanMensual.mes >= c_month)
        )
    
    planes_antiguos = db.query(ControlPlanMensual).filter(
        ControlPlanMensual.empresa_id == empresa_id,
        ControlPlanMensual.cantidad_disponible > 0,
        ControlPlanMensual.estado == EstadoPlan.ABIERTO, 
        or_(
            ControlPlanMensual.anio < plan_mensual.anio,
            and_(ControlPlanMensual.anio == plan_mensual.anio, ControlPlanMensual.mes < plan_mensual.mes)
        ),
        start_filter
    ).order_by(asc(ControlPlanMensual.anio), asc(ControlPlanMensual.mes)).with_for_update().all()
    
    # B. Construir Lista Prioritaria (FIFO Total)
    # [Nov, Dec... (Past)] + [Current]
    # Nota: plan_mensual se añade al final porque es el "último recurso" antes de ir a bolsas/extras.
    candidatos_plan = list(planes_antiguos)
    if plan_mensual.cantidad_disponible > 0:
        candidatos_plan.append(plan_mensual)
        
    # C. Iterar y Consumir
    for plan_candidato in candidatos_plan:
        if remanente_a_consumir <= 0: break
        
        disponible = plan_candidato.cantidad_disponible
        a_tomar = min(disponible, remanente_a_consumir)
        
        saldo_antes = plan_candidato.cantidad_disponible
        
        plan_candidato.cantidad_disponible -= a_tomar
        remanente_a_consumir -= a_tomar
        
        # Determinar tipo de fuente (Visual)
        # Si es el plan del documento -> PLAN. Si es pasado -> PLAN_PASADO.
        es_plan_doc = (plan_candidato.id == plan_mensual.id)
        fuente_tipo = TipoFuenteConsumo.PLAN if es_plan_doc else "PLAN_PASADO"
        
        historial = HistorialConsumo(
            empresa_id=empresa_id,
            cantidad=a_tomar,
            tipo_operacion=TipoOperacionConsumo.CONSUMO,
            fuente_tipo=fuente_tipo, 
            fuente_id=plan_candidato.id,
            saldo_fuente_antes=saldo_antes,
            saldo_fuente_despues=plan_candidato.cantidad_disponible,
            documento_id=documento_id,
            fecha=datetime.now()
        )
        db.add(historial)
        
    if remanente_a_consumir == 0:
        return

    
    # 2.5 BOLSAS DE EXCEDENTES (Prioridad 2.5)
    # Si los planes abiertos pasados no alcanzaron, miramos las Bolsas (Periodos Cerrados con ahorro)
    if remanente_a_consumir > 0:
        bolsas = db.query(BolsaExcedente).filter(
            BolsaExcedente.empresa_id == empresa_id,
            BolsaExcedente.estado == EstadoBolsa.VIGENTE,
            BolsaExcedente.cantidad_disponible > 0,
            BolsaExcedente.fecha_vencimiento >= now
        ).order_by(asc(BolsaExcedente.fecha_vencimiento)).with_for_update().all()
        
        for bolsa in bolsas:
            if remanente_a_consumir <= 0: break
            
            disponible = bolsa.cantidad_disponible
            a_tomar = min(disponible, remanente_a_consumir)
            
            saldo_antes = bolsa.cantidad_disponible
            
            bolsa.cantidad_disponible -= a_tomar
            remanente_a_consumir -= a_tomar
            
            historial = HistorialConsumo(
                empresa_id=empresa_id,
                cantidad=a_tomar,
                tipo_operacion=TipoOperacionConsumo.CONSUMO,
                fuente_tipo=TipoFuenteConsumo.BOLSA,
                fuente_id=bolsa.id,
                saldo_fuente_antes=saldo_antes,
                saldo_fuente_despues=bolsa.cantidad_disponible,
                documento_id=documento_id,
                fecha=datetime.now()
            )
            db.add(historial)


    # 3. RECARGAS ADICIONALES (Prioridad 3)
    # Solo si el Plan Actual y los Planes Pasados no cubrieron la demanda.
    if remanente_a_consumir > 0:
        tramos_recarga = db.query(RecargaAdicional).filter(
            RecargaAdicional.empresa_id == empresa_id,
            RecargaAdicional.estado == EstadoRecarga.VIGENTE
        ).order_by(asc(RecargaAdicional.fecha_compra)).with_for_update().all()
        
        for recarga in tramos_recarga:
            if remanente_a_consumir <= 0: break
                
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
            f"Saldo insuficiente. Faltan {remanente_a_consumir} registros.",
            detalle={"faltante": remanente_a_consumir}
        )

def revertir_consumo(db: Session, documento_id: int):
    """
    Revierte TODO el consumo asociado a un documento.
    Restaura el saldo a la fuente original exacta (Plan ID, Recarga ID).
    """
    # 1. Buscar todo el historial de consumo de este documento
    consumos_previos = db.query(HistorialConsumo).filter(
        HistorialConsumo.documento_id == documento_id,
        HistorialConsumo.tipo_operacion == TipoOperacionConsumo.CONSUMO
    ).all()
    
    if not consumos_previos:
        return # No hubo consumo registrado
        
    for consumo in consumos_previos:
        # Revertir según el tipo de fuente
        if consumo.fuente_tipo == TipoFuenteConsumo.PLAN or consumo.fuente_tipo == "PLAN_PASADO":
            # Restaurar a ControlPlanMensual específico por ID
            plan_origen = db.query(ControlPlanMensual).get(consumo.fuente_id)
            if plan_origen:
                plan_origen.cantidad_disponible += consumo.cantidad
                # No cambiamos el estado (si estaba cerrado, sigue cerrado pero con más saldo)
                db.add(plan_origen)
                
        elif consumo.fuente_tipo == TipoFuenteConsumo.RECARGA:
            recarga = db.query(RecargaAdicional).get(consumo.fuente_id)
            if recarga:
                recarga.cantidad_disponible += consumo.cantidad
                if recarga.estado == EstadoRecarga.AGOTADA:
                    recarga.estado = EstadoRecarga.VIGENTE
                db.add(recarga)
        
        elif consumo.fuente_tipo == TipoFuenteConsumo.BOLSA:
             # Legacy Support: Por si estamos revirtiendo un documento viejo que usó Bolsas
             from app.models.consumo_registros import BolsaExcedente
             bolsa = db.query(BolsaExcedente).get(consumo.fuente_id)
             if bolsa:
                 bolsa.cantidad_disponible += consumo.cantidad
                 if bolsa.estado == EstadoBolsa.AGOTADO:
                      bolsa.estado = EstadoBolsa.VIGENTE
                 db.add(bolsa)

        # Crear LOG de reversión (opcional, por ahora borramos el log de consumo o creamos contra-asiento?)
        # Lo ideal es crear un contra-asiento:
        reversion = HistorialConsumo(
            empresa_id=consumo.empresa_id,
            fecha=datetime.now(),
            cantidad=consumo.cantidad, # Cantidad positiva devuelta
            tipo_operacion=TipoOperacionConsumo.REVERSION,
            fuente_tipo=consumo.fuente_tipo,
            fuente_id=consumo.fuente_id,
            saldo_fuente_antes=0, # No recalculamos snapshots para reversion simple
            saldo_fuente_despues=0,
            documento_id=documento_id
        )
        db.add(reversion)
        
        # OJO: ¿Borramos el registro original de consumo? 
        # Si borramos, perdemos la historia de que "existió". Mejor marcamos REVERSION.
        # Pero para simplicidad de reporting, a veces se borra.
        # Dejaremos el registro de Reversion.

    # Finalmente, commits manejados por caller.

def verificar_disponibilidad(db: Session, empresa_id: int, cantidad_necesaria: int) -> bool:
    """
    Verifica si existe saldo suficiente sumando todas las fuentes VIGENTES:
    1. Plan Actual
    2. Planes Pasados Desbloqueados (Rolling Quota)
    3. Recargas
    """
    # 0. Check Jerarquía y Cupo Local (Si aplica)
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa: return False

    # Si tiene Padre (Es Hija) -> Lógica de Doble Validación
    if empresa.padre_id:
        return verificar_disponibilidad(db, empresa.padre_id, cantidad_necesaria)

    # --- LÓGICA ESTÁNDAR ---
    # 1. Plan Mensual Actual
    now = datetime.now()
    plan = _get_or_create_plan_mensual(db, empresa_id, now)
    
    saldo_plan = plan.cantidad_disponible if plan and plan.estado == EstadoPlan.ABIERTO else 0
    
    # 2. Planes Pasados (Rolling Quota)
    # Sumar saldo de planes pasados (cantidad_disponible > 0)
    # Ventana de 1 año (similar a registrar_consumo)
    anio_limite = now.year - 1
    
    query_rolling = db.query(ControlPlanMensual).filter(
        ControlPlanMensual.empresa_id == empresa_id,
        ControlPlanMensual.cantidad_disponible > 0,
        ~and_(ControlPlanMensual.anio == plan.anio, ControlPlanMensual.mes == plan.mes),
        # ControlPlanMensual.anio >= anio_limite # Opcional
    )
    saldo_rolling = sum(p.cantidad_disponible for p in query_rolling.all())
    
    # 3. Recargas (VIGENTE)
    saldo_recargas = db.query(RecargaAdicional).filter(
        RecargaAdicional.empresa_id == empresa_id,
        RecargaAdicional.estado == EstadoRecarga.VIGENTE
    ).with_entities(RecargaAdicional.cantidad_disponible).all()
    
    total_recargas = sum([r.cantidad_disponible for r in saldo_recargas])

    total_disponible = saldo_plan + saldo_rolling + total_recargas
    
    if total_disponible < cantidad_necesaria:
         missing = cantidad_necesaria - total_disponible
         raise HTTPException(
            status_code=400,
            detail=f"Saldo insuficiente (Empresa {empresa_id}). Te faltan {missing} registros para completar esta transacción."
        )
    
    return True
