from typing import List, Dict, Any
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, func, select, or_
from datetime import date

from ..models import PlanCuenta as models_plan
from app.models.propiedad_horizontal.concepto import PHConcepto as models_ph_concepto
from app.models.documento import Documento as models_doc
from ..models import AplicacionPago as models_aplica
from ..models import MovimientoContable as models_mov
from ..models import TipoDocumento as models_tipo
from ..models import Empresa as models_empresa
from app.services import documento as documento_service
from app.core.constants import FuncionEspecial
from ..models.propiedad_horizontal import PHConfiguracion

import unicodedata as _uda

def pnorm_ph(t):
    if not t: return ""
    s = "".join(c for c in _uda.normalize('NFD', str(t)) if _uda.category(c) != 'Mn')
    return s.strip().upper()

def identificar_concepto_ph(texto_mov, conceptos_ph):
    """
    Identifica un concepto PH a partir del texto de un movimiento contable.
    """
    if not texto_mov: return None
    t = pnorm_ph(texto_mov)
    # Quitar prefijos comunes de PH para no confundir startswith
    for prefijo in ["CXC ", "ABONO ", "RECAUDO ", "COBRO ", "PAGO ", "DIRIGIDO ", "DIRIGIDO:", "ABONO DIRIGIDO:", "RECAUDO DIRIGIDO:"]:
        if t.startswith(prefijo):
            t = t[len(prefijo):].strip()
    
    mejor, mejor_len = None, 0
    for cp in conceptos_ph:
        n = pnorm_ph(cp.nombre)
        if n and t.startswith(n) and len(n) > mejor_len:
            mejor = cp
            mejor_len = len(n)
    
    # Fallback: si no encontró con startswith, intentar con 'in' (por si hay prefijos adicionales)
    if not mejor:
        for cp in conceptos_ph:
            n = pnorm_ph(cp.nombre)
            if n and n in t and len(n) > mejor_len:
                mejor = cp
                mejor_len = len(n)
    return mejor


def get_cuentas_especiales_ids(db: Session, empresa_id: int, tipo: str) -> List[int]:
    cuentas_ids = set()
    query = db.query(
        models_tipo.cuenta_debito_cxc_id,
        models_tipo.cuenta_credito_cxc_id,
        models_tipo.cuenta_debito_cxp_id,
        models_tipo.cuenta_credito_cxp_id
    ).filter(models_tipo.empresa_id == empresa_id).distinct()

    if tipo == 'cxc':
        for row in query.all():
            if row.cuenta_debito_cxc_id: cuentas_ids.add(row.cuenta_debito_cxc_id)
            if row.cuenta_credito_cxc_id: cuentas_ids.add(row.cuenta_credito_cxc_id)
    elif tipo == 'cxp':
        for row in query.all():
            if row.cuenta_debito_cxp_id: cuentas_ids.add(row.cuenta_debito_cxp_id)
            if row.cuenta_credito_cxp_id: cuentas_ids.add(row.cuenta_credito_cxp_id)
    
    if not cuentas_ids:
        return []

    # Obtener configuración de prefijos de la empresa
    empresa = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()

    # --- INTEGRACION PH: Verificar si hay cuenta centralizada de Cartera ---
    # Esto asegura que la cuenta 16 (o cualquiera) configurada en PH sea reconocida como CXC
    ph_config = db.query(PHConfiguracion).filter(PHConfiguracion.empresa_id == empresa_id).first()
    ph_cuenta_cartera_id = ph_config.cuenta_cartera_id if ph_config else None
    
    # --- INTEGRACION PH: CONCEPTOS CON CUENTAS PROPIAS ---
    # Si un concepto tiene su propia cuenta CXC (ej: 1399 Multas), debemos incluirla
    # o de lo contrario la factura parecerá tener saldo 0.
    from ..models.propiedad_horizontal import PHConcepto
    conceptos_cxc = db.query(PHConcepto.cuenta_cxc_id).filter(
        PHConcepto.empresa_id == empresa_id,
        PHConcepto.cuenta_cxc_id.isnot(None)
    ).all()
    
    for row in conceptos_cxc:
        if row.cuenta_cxc_id:
            cuentas_ids.add(row.cuenta_cxc_id)

    # Lógica flexible para CXC:
    # En PH y otros negocios, la cartera puede ser 13, 14, 16, etc.
    # El problema original era que incluía la 11 (Caja) y los recibos sumaban deuda.
    # SOLUCIÓN: Si es CXC, aceptamos cualquier ACTIVO (1%) excepto DISPONIBLE (11%).
    
    if tipo == 'cxc':
        valid_ids = db.query(models_plan.id, models_plan.codigo).filter(
            models_plan.id.in_(list(cuentas_ids)),
            models_plan.codigo.like("1%"),
            ~models_plan.codigo.like("11%") # Excluir Caja/Bancos
        ).all()
        
        result_ids = [row.id for row in valid_ids]
        
        # AGREGAR CUENTA PH EXPLICITA SI EXISTE (Y SI ES VALIDA/ACTIVA)
        # Esto soluciona el caso donde por algun motivo el filtro de arriba no la cogiera,
        # O simplemente para dar prioridad total.
        if ph_cuenta_cartera_id and ph_cuenta_cartera_id in cuentas_ids:
            if ph_cuenta_cartera_id not in result_ids:
                result_ids.append(ph_cuenta_cartera_id)

        return result_ids
    else:
        # Para CXP (Proveedores), mantenemos Pasivos (2%)
        # Podríamos usar la configuración de empresa si se requiere algo exótico
        prefix = empresa.prefijo_cxp if empresa and empresa.prefijo_cxp else default_cxp
        valid_ids = db.query(models_plan.id).filter(
            models_plan.id.in_(list(cuentas_ids)),
            models_plan.codigo.like(f"{prefix}%")
        ).all()

    return [row.id for row in valid_ids]

def _documento_afecta_cuentas(db: Session, documento_id: int, cuentas_ids: List[int]) -> bool:
    if not cuentas_ids:
        return False

    movimiento_existente = db.query(models_mov.id).filter(
        models_mov.documento_id == documento_id,
        models_mov.cuenta_id.in_(cuentas_ids)
    ).first()
    return movimiento_existente is not None

def recalcular_aplicaciones_tercero(db: Session, tercero_id: int, empresa_id: int, commit: bool = True):
    # CORRECCIÓN CRÍTICA: Buscamos documentos donde el tercero aparece en el encabezado
    # O en los movimientos contables de las cuentas CXC/CXP (el caso de los CE/RC).
    try:
        cuentas_cxc_ids = get_cuentas_especiales_ids(db, empresa_id, 'cxc')
        cuentas_cxp_ids = get_cuentas_especiales_ids(db, empresa_id, 'cxp')
        todas_cuentas_ids = list(set(cuentas_cxc_ids + cuentas_cxp_ids))

        # IDs de docs donde el tercero está en el ENCABEZADO
        ids_por_encabezado = select(models_doc.id).where(
            models_doc.beneficiario_id == tercero_id,
            models_doc.empresa_id == empresa_id
        )

        # IDs de docs donde el tercero está en un MOVIMIENTO sobre cuentas CXC/CXP
        ids_por_movimiento = select(models_mov.documento_id).where(
            models_mov.tercero_id == tercero_id,
            models_mov.cuenta_id.in_(todas_cuentas_ids) if todas_cuentas_ids else False
        ).join(models_doc, models_mov.documento_id == models_doc.id).where(
            models_doc.empresa_id == empresa_id
        )

        # UNIÓN de ambos conjuntos para obtener todos los IDs relevantes
        todos_ids_subquery = select(models_doc.id).where(
            models_doc.empresa_id == empresa_id,
            or_(
                models_doc.beneficiario_id == tercero_id,
                models_doc.id.in_(ids_por_movimiento)
            )
        ).scalar_subquery()

        # Eliminar aplicaciones existentes de TODOS los documentos relevantes
        db.query(models_aplica).where(
            or_(
                models_aplica.documento_factura_id.in_(todos_ids_subquery),
                models_aplica.documento_pago_id.in_(todos_ids_subquery)
            )
        ).delete(synchronize_session=False)

        # Cargar documentos usando la condición extendida
        documentos_potenciales = db.query(models_doc).options(
            joinedload(models_doc.tipo_documento),
            selectinload(models_doc.movimientos)
        ).filter(
            models_doc.empresa_id == empresa_id,
            models_doc.anulado == False,
            or_(
                models_doc.beneficiario_id == tercero_id,
                models_doc.id.in_(ids_por_movimiento)
            )
        ).order_by(models_doc.fecha, models_doc.id).all()


        # Cargar conceptos PH para identificación por texto
        conceptos_ph = db.query(models_ph_concepto).filter(
            models_ph_concepto.empresa_id == empresa_id,
            models_ph_concepto.activo == True
        ).order_by(func.coalesce(models_ph_concepto.orden, 999).asc(), models_ph_concepto.id.asc()).all()
        
        # Log para debug en producción
        nombres_c = [f"{c.nombre} (ID:{c.id}, Ord:{c.orden})" for c in conceptos_ph]
        print(f"[ESPIA CARTERA] Jerarquia Activa: {nombres_c}")

        fac_cxc = {}   # doc_id -> {'doc': doc, 'saldo': float, 'saldo_x_cid': {cid: float}}
        pag_cxc = {}   # doc_id -> {'doc': doc, 'monto': float, 'movs': [mov, ...]}
        fac_cxp = {}   # doc_id -> {'doc': doc, 'saldo': float}
        pag_cxp = {}   # doc_id -> {'doc': doc, 'monto': float}

        for d in documentos_potenciales:
            for mov in d.movimientos:
                # ── CARTERA (CXC) ──
                if mov.cuenta_id in cuentas_cxc_ids:
                    if mov.debito > 0:
                        if d.id not in fac_cxc:
                            fac_cxc[d.id] = {'doc': d, 'saldo': 0.0, 'saldo_x_cid': {}}
                        monto = float(mov.debito)
                        fac_cxc[d.id]['saldo'] += monto
                        # Desglose por concepto (usando texto del débito)
                        co = identificar_concepto_ph(mov.concepto, conceptos_ph)
                        cid = co.id if co else 0
                        sxc = fac_cxc[d.id]['saldo_x_cid']
                        sxc[cid] = sxc.get(cid, 0.0) + monto

                    elif mov.credito > 0:
                        if d.id not in pag_cxc:
                            pag_cxc[d.id] = {'doc': d, 'monto': 0.0, 'movs': []}
                        pag_cxc[d.id]['monto'] += float(mov.credito)
                        pag_cxc[d.id]['movs'].append(mov)

                # ── PROVEEDORES (CXP) ──
                elif mov.cuenta_id in cuentas_cxp_ids:
                    if mov.credito > 0:
                        if d.id not in fac_cxp:
                            fac_cxp[d.id] = {'doc': d, 'saldo': 0.0}
                        fac_cxp[d.id]['saldo'] += float(mov.credito)
                    elif mov.debito > 0:
                        if d.id not in pag_cxp:
                            pag_cxp[d.id] = {'doc': d, 'monto': 0.0}
                        pag_cxp[d.id]['monto'] += float(mov.debito)

        # Listas ordenadas FIFO
        facturas_cxc = sorted(fac_cxc.values(), key=lambda x: (x['doc'].fecha, x['doc'].id))
        pagos_cxc    = sorted(pag_cxc.values(), key=lambda x: (x['doc'].fecha, x['doc'].id))
        facturas_cxp = sorted(fac_cxp.values(), key=lambda x: (x['doc'].fecha, x['doc'].id))
        pagos_cxp    = sorted(pag_cxp.values(), key=lambda x: (x['doc'].fecha, x['doc'].id))

        # ─────────────────────────────────────────────────────────────────────
        # pending_aplica: acumulador antes de persistir.
        # Clave (fac_id, pag_id) → monto_total garantiza
        # UN SOLO AplicacionPago por par, aunque pasen múltiples conceptos.
        # ─────────────────────────────────────────────────────────────────────
        pending_aplica = {}

        def apply_fifo(facturas, valor_restante, p_doc_id,
                       solo_unidad_id=None, concepto_id=None):
            for fac in facturas:
                if valor_restante <= 0.01:
                    break
                f_doc = fac['doc']
                
                # Filtrar por unidad si es necesario
                if solo_unidad_id and f_doc.unidad_ph_id != solo_unidad_id:
                    continue
                
                if fac['saldo'] <= 0.01:
                    continue

                if concepto_id is not None:
                    sxc = fac.get('saldo_x_cid', {})
                    monto_concepto = sxc.get(concepto_id, 0.0)
                    if monto_concepto <= 0.01:
                        continue
                    aplicar = min(valor_restante, monto_concepto, fac['saldo'])
                    c_nom = next((c.nombre for c in conceptos_ph if c.id == concepto_id), "ID:"+str(concepto_id))
                    print(f"       [ESPIA FIFO] Pago -> Factura {f_doc.numero} [{c_nom}]: Aplicando {aplicar}")
                else:
                    aplicar = min(valor_restante, fac['saldo'])
                    print(f"       [ESPIA FIFO] Pago -> Factura {f_doc.numero} [GENERICO]: Aplicando {aplicar}")

                if aplicar <= 0.01:
                    continue

                # Acumular — no crear DB record todavía
                key = (f_doc.id, p_doc_id)
                pending_aplica[key] = pending_aplica.get(key, 0.0) + aplicar

                fac['saldo'] -= aplicar
                valor_restante -= aplicar
                if concepto_id is not None and 'saldo_x_cid' in fac:
                    fac['saldo_x_cid'][concepto_id] = max(
                        0.0, fac['saldo_x_cid'].get(concepto_id, 0.0) - aplicar
                    )
            return valor_restante

        # ============================================================
        # CRUCE CXC
        # ============================================================
        TEXTOS_GENERICOS = ('CARTERA PH', 'ABONO PH', 'RECAUDO PH', 'ANTICIPO', 'SALDO EXCEDENTE')

        print(f"\n[ESPIA CARTERA] Iniciando cruce CXC para Tercero ID: {tercero_id}")
        print(f"[ESPIA CARTERA] Facturas encontradas: {len(facturas_cxc)}, Pagos encontrados: {len(pagos_cxc)}")

        for pag in pagos_cxc:
            valor_pago = pag['monto']
            pago_doc   = pag['doc']
            movs_pago  = pag.get('movs', [])

            print(f"\n---> [ESPIA] Procesando PAGO: {pago_doc.tipo_documento.codigo}-{pago_doc.numero} (Monto: {valor_pago})")

            # Limpiar acumulador para este pago
            pending_aplica.clear()

            # ── IDENTIFICACIÓN DE CONCEPTOS DIRIGIDOS ──
            intentos_pago = [] # List[(concepto_id, monto)]
            monto_generico = 0
            
            for mv in movs_pago:
                txt = pnorm_ph(mv.concepto or '')
                print(f"     [ESPIA] Analizando Movimiento: '{mv.concepto}' (Credito: {mv.credito})")
                
                # Si el texto es genérico, ignoramos identificación específica
                if any(pnorm_ph(g) in txt for g in TEXTOS_GENERICOS):
                    print(f"     [ESPIA]   - Es un texto GENERICO. Se suma a monto_generico.")
                    monto_generico += float(mv.credito)
                    continue
                
                co = identificar_concepto_ph(mv.concepto, conceptos_ph)
                if co:
                    print(f"     [ESPIA]   - Concepto IDENTIFICADO: {co.nombre} (ID: {co.id})")
                    intentos_pago.append((co.id, float(mv.credito)))
                else:
                    print(f"     [ESPIA]   - NO se identificó concepto. Se suma a monto_generico.")
                    monto_generico += float(mv.credito)

            print(f"     [ESPIA] Resultado ID: {len(intentos_pago)} dirigidos, Generico: {monto_generico}")

            # 1. Aplicar montos DIRIGIDOS primero
            for cid, monto in intentos_pago:
                if monto <= 0: continue
                # Buscamos el nombre del concepto para el log
                c_nom = next((c.nombre for c in conceptos_ph if c.id == cid), "ID:"+str(cid))
                print(f"     [ESPIA] APLICANDO DIRIGIDO -> Concepto: {c_nom}, Monto: {monto}")
                
                restante_dirigido = apply_fifo(facturas_cxc, monto, pago_doc.id,
                                               solo_unidad_id=pago_doc.unidad_ph_id,
                                               concepto_id=cid)
                
                print(f"     [ESPIA]   - Restante tras aplicar dirigido: {restante_dirigido}")
                # ¡OJO! Ya NO movemos el restante dirigido a monto_generico.
                # Si el usuario dijo "esto es para Pintura", el sobrante se queda quieto como anticipo.
                # if restante_dirigido > 0.01:
                #    monto_generico += restante_dirigido
                #    print(f"     [ESPIA]   - Sobrante {restante_dirigido} movido a monto_generico.")

            # 2. Aplicar monto GENÉRICO siguiendo jerarquía
            if monto_generico > 0.01:
                print(f"     [ESPIA] APLICANDO GENERICO (FIFO) -> Monto: {monto_generico}")
                jerarquia = [cp.id for cp in conceptos_ph] + [None]
                
                # A. Misma Unidad (Jerarquía)
                if pago_doc.unidad_ph_id:
                    for cid in jerarquia:
                        if monto_generico <= 0.01: break
                        c_nom = next((c.nombre for c in conceptos_ph if c.id == cid), "ANTICIPO")
                        
                        antes = monto_generico
                        monto_generico = apply_fifo(
                            facturas_cxc, monto_generico, pago_doc.id,
                            solo_unidad_id=pago_doc.unidad_ph_id,
                            concepto_id=cid)
                        
                        if antes != monto_generico:
                            print(f"     [ESPIA]   - Aplicado a {c_nom}: {antes - monto_generico}")

                # B. Otras Unidades (Fallback)
                if monto_generico > 0.01:
                    print(f"     [ESPIA]   - Aplicando remanente {monto_generico} a otras unidades...")
                    for cid in jerarquia:
                        if monto_generico <= 0.01: break
                        monto_generico = apply_fifo(
                            facturas_cxc, monto_generico, pago_doc.id,
                            concepto_id=cid)

            # ── Persistir UN solo AplicacionPago por par (factura, pago) ──
            for (fac_id, pag_id), total in pending_aplica.items():
                if total > 0:
                    db.add(models_aplica(
                        documento_factura_id=fac_id,
                        documento_pago_id=pag_id,
                        valor_aplicado=total,
                        empresa_id=empresa_id
                    ))


        # ============================================================
        # CRUCE CXP (FIFO simple, sin cambios)
        # ============================================================
        for pago_data in pagos_cxp:
            valor_pago = pago_data['monto']
            for fac_data in facturas_cxp:
                if valor_pago <= 0:
                    break
                if fac_data['saldo'] <= 0:
                    continue
                valor_a_aplicar = min(valor_pago, fac_data['saldo'])
                db.add(models_aplica(
                    documento_factura_id=fac_data['doc'].id,
                    documento_pago_id=pago_data['doc'].id,
                    valor_aplicado=valor_a_aplicar,
                    empresa_id=empresa_id
                ))
                fac_data['saldo'] -= valor_a_aplicar
                valor_pago -= valor_a_aplicar

        if commit:
            db.commit()
        else:
            db.flush()
        return {"status": "ok", "message": "Recálculo de cartera y proveedores completado."}

    except Exception as e:
        db.rollback()
        raise e
            
def get_facturas_pendientes_por_tercero(db: Session, tercero_id: int, empresa_id: int, unidad_ph_id: int = None, fecha_corte: date = None):
    cuentas_cxc_ids = get_cuentas_especiales_ids(db, empresa_id, 'cxc')
    if not cuentas_cxc_ids:
        return []

    subquery_valor_total = db.query(
        models_mov.documento_id.label("documento_id"),
        func.sum(models_mov.debito).label("valor_total")
    ).join(models_doc, models_mov.documento_id == models_doc.id).filter(
        models_doc.empresa_id == empresa_id,
        models_doc.beneficiario_id == tercero_id, # OPTIMIZACIÓN PATH B
        models_doc.anulado == False,
        models_mov.cuenta_id.in_(cuentas_cxc_ids) 
    ).group_by(models_mov.documento_id).subquery()

    # Construir query base para pagos aplicados
    q_pagos = db.query(
        models_aplica.documento_factura_id.label("documento_id"),
        func.sum(models_aplica.valor_aplicado).label("total_aplicado")
    ).join(models_doc, models_aplica.documento_pago_id == models_doc.id).filter(
        models_doc.empresa_id == empresa_id, # OPTIMIZACIÓN PATH B
        models_doc.beneficiario_id == tercero_id, # OPTIMIZACIÓN PATH B
        models_doc.anulado == False
    )
    
    # [NUEVO] Filtro de fecha de corte para ver el pasado
    if fecha_corte:
        q_pagos = q_pagos.filter(models_doc.fecha <= fecha_corte)
        
    subquery_valor_aplicado = q_pagos.group_by(models_aplica.documento_factura_id).subquery()

    query = db.query(
        models_doc.id, models_doc.numero, models_doc.fecha, models_doc.fecha_vencimiento,
        subquery_valor_total.c.valor_total,
        func.coalesce(subquery_valor_aplicado.c.total_aplicado, 0).label("total_aplicado")
    ).join(
        subquery_valor_total, subquery_valor_total.c.documento_id == models_doc.id
    ).join(
        models_tipo, models_doc.tipo_documento_id == models_tipo.id
    ).outerjoin(
        subquery_valor_aplicado, subquery_valor_aplicado.c.documento_id == models_doc.id
    ).filter(
        models_doc.beneficiario_id == tercero_id,
        models_doc.empresa_id == empresa_id,
        models_doc.anulado == False,
        subquery_valor_total.c.valor_total > func.coalesce(subquery_valor_aplicado.c.total_aplicado, 0)
    )
    
    # DEBUG SPY
    # print(f"DEBUG CARTERA: Buscando pendientes para Tercero {tercero_id} (Unidad {unidad_ph_id})")
    # print(f"DEBUG CARTERA: Cuentas CXC IDs usadas: {cuentas_cxc_ids}")

    if unidad_ph_id:
        query = query.filter(models_doc.unidad_ph_id == unidad_ph_id)
    
    facturas_pendientes = query.order_by(models_doc.fecha).all()

    resultado_formateado = []
    for factura in facturas_pendientes:
        saldo_pendiente = factura.valor_total - factura.total_aplicado
        resultado_formateado.append({
            "id": factura.id, "numero": factura.numero,
            "fecha": factura.fecha.isoformat(),
            "valor_total": float(factura.valor_total),
            "saldo_pendiente": float(saldo_pendiente),
            "fecha_vencimiento": factura.fecha_vencimiento.isoformat() if factura.fecha_vencimiento else None
        })
    return resultado_formateado

def get_facturas_compra_pendientes_por_tercero(db: Session, tercero_id: int, empresa_id: int):
    cuentas_cxp_ids = get_cuentas_especiales_ids(db, empresa_id, 'cxp')
    if not cuentas_cxp_ids:
        return []

    # --- CORRECCIÓN CRÍTICA EN JOIN ---
    # Antes: .join(models_mov, ...) -> Incorrecto, intentaba unir movimiento consigo mismo o flotaba
    # Ahora: .join(models_doc, ...) -> Correcto, une con documento para filtrar por empresa/anulado
    subquery_valor_total = db.query(
        models_mov.documento_id.label("documento_id"),
        func.sum(models_mov.credito).label("valor_total")
    ).join(models_doc, models_mov.documento_id == models_doc.id).filter(
        models_doc.empresa_id == empresa_id,
        models_doc.anulado == False,
        models_mov.cuenta_id.in_(cuentas_cxp_ids)
    ).group_by(models_mov.documento_id).subquery()

    subquery_valor_aplicado = db.query(
        models_aplica.documento_factura_id.label("documento_id"),
        func.sum(models_aplica.valor_aplicado).label("total_aplicado")
    ).join(models_doc, models_aplica.documento_pago_id == models_doc.id).filter(
        models_doc.anulado == False
    ).group_by(models_aplica.documento_factura_id).subquery()

    facturas_pendientes = db.query(
        models_doc.id, models_doc.numero, models_doc.fecha,
        subquery_valor_total.c.valor_total,
        func.coalesce(subquery_valor_aplicado.c.total_aplicado, 0).label("total_aplicado")
    ).join(
        subquery_valor_total, subquery_valor_total.c.documento_id == models_doc.id
    ).join(
        models_tipo, models_doc.tipo_documento_id == models_tipo.id
    ).outerjoin(
        subquery_valor_aplicado, subquery_valor_aplicado.c.documento_id == models_doc.id
    ).filter(
        models_doc.beneficiario_id == tercero_id,
        models_doc.empresa_id == empresa_id,
        models_doc.anulado == False,
        subquery_valor_total.c.valor_total > func.coalesce(subquery_valor_aplicado.c.total_aplicado, 0)
    ).order_by(models_doc.fecha).all()

    resultado_formateado = []
    for factura in facturas_pendientes:
        saldo_pendiente = factura.valor_total - factura.total_aplicado
        resultado_formateado.append({
            "id": factura.id, "numero": factura.numero,
            "fecha": factura.fecha.isoformat(),
            "valor_total": float(factura.valor_total),
            "saldo_pendiente": float(saldo_pendiente)
        })
    return resultado_formateado