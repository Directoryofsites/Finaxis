import unicodedata
from sqlalchemy.orm import Session
from app.models.movimiento_contable import MovimientoContable
from app.models.propiedad_horizontal.concepto import PHConcepto
from app.models.aplicacion_pago import AplicacionPago
from app.services.propiedad_horizontal import pago_service


def _norm(t):
    if not t:
        return ""
    s = "".join(c for c in unicodedata.normalize('NFD', t)
                if unicodedata.category(c) != 'Mn')
    return s.strip().upper()


def _tipo_concepto(co, nombre_fallback=""):
    """Clasifica un PHConcepto en INTERES, MULTA o CAPITAL."""
    if co is None:
        return 'CAPITAL'
    if co.es_interes:
        return 'INTERES'
    if 'MULTA' in _norm(co.nombre):
        return 'MULTA'
    return 'CAPITAL'


def _concepto_desde_mov(mov_concepto_text, conceptos_db):
    """
    Identifica el PHConcepto desde el texto de un movimiento de recibo.
    Ej: "Abono Multas - b2/101" → PHConcepto(nombre='Multas')
    """
    if not mov_concepto_text:
        return None
    texto = _norm(mov_concepto_text)
    for pfx in ("ABONO ", "RECAUDO ", "CXC ", "PAGO "):
        if texto.startswith(pfx):
            texto = texto[len(pfx):]
    mejor, mejor_len = None, 0
    for c in conceptos_db:
        nombre_norm = _norm(c.nombre)
        if nombre_norm and nombre_norm in texto and len(nombre_norm) > mejor_len:
            mejor = c
            mejor_len = len(nombre_norm)
    return mejor


TEXTOS_GENERICOS = ('CARTERA PH', 'ABONO PH', 'RECAUDO PH', 'ANTICIPO')


def _es_pago_dirigido(movs_credito_recibo, conceptos_db):
    """
    Retorna (True, PHConcepto_o_None) si el recibo está dirigido a un concepto.
    Un recibo es dirigido cuando su texto de movimiento NO es genérico.
    """
    for mv in movs_credito_recibo:
        txt = _norm(mv.concepto or '')
        if txt and not any(g in txt for g in TEXTOS_GENERICOS):
            co = _concepto_desde_mov(mv.concepto, conceptos_db)
            return True, co
    return False, None


def get_cartera_ph_pendientes_detallada(db: Session, empresa_id: int, unidad_id: int):
    """
    Saldo pendiente desglosado por concepto para una unidad.

    ESTRATEGIA GLOBAL:
    ─────────────────
    En lugar de atribuir pagos factura por factura (lo cual favorece los meses
    más antiguos sin importar el concepto), se hace una atribución GLOBAL:

    1. Se suman los débitos CXC de TODAS las facturas por concepto.
       → total_cobrado[concepto] = suma de lo facturado en todos los meses

    2. Se separan los pagos en dos grupos:
       a. DIRIGIDOS: identificados por texto ("Abono Multas...") → atribuidos
          directamente al concepto identificado.
       b. AUTOMÁTICOS: sin concepto específico → su monto total se aplica al
          pool global usando jerarquía: INTERES → MULTA → CAPITAL.

    3. total_pagado_por_concepto = dirigidos + proporción de automáticos.

    4. saldo = total_cobrado - total_pagado (por concepto).

    Esto garantiza que:
    - Un abono de $1M cubre Intereses ($9,600) + Multas ($800K) + lo que
      sobre del Capital, SIN importar en qué mes está cada concepto.
    - Un abono dirigido a Multas solo reduce Multas, nunca Admin.
    """
    pendientes = pago_service.get_cartera_ph_pendientes(db, empresa_id, unidad_id=unidad_id)
    if not pendientes:
        return []

    conceptos_db = db.query(PHConcepto).filter(PHConcepto.empresa_id == empresa_id).order_by(PHConcepto.orden.asc()).all()

    # ── Índice de conceptos por nombre normalizado (para búsqueda por texto) ──
    # Las cuentas contables NO se usan para identificar conceptos en la distribución.
    # El nombre del concepto en el texto del movimiento es la ÚNICA fuente de verdad.
    conceptos_por_nombre = {_norm(c.nombre): c for c in conceptos_db if c.nombre}

    # ── PASO 1: Acumular total cobrado por concepto (todas las facturas) ──
    # pool[c_id] = {'id', 'nombre', 'tipo', 'cobrado', 'pagado'}
    pool = {}

    # También colectar todos los doc_ids pendientes para buscar APs
    doc_ids_pendientes = set()

    for factura in pendientes:
        doc_id = factura['id']
        doc_ids_pendientes.add(doc_id)

        movs_cr = db.query(MovimientoContable).filter(
            MovimientoContable.documento_id == doc_id,
            MovimientoContable.credito > 0
        ).all()

        for mov in movs_cr:
            # ── IDENTIFICACIÓN 100% POR NOMBRE — el nombre debe estar al INICIO del texto ──
            # 'startswith' evita que "Contribucion para Pintura" robe el movimiento
            # de intereses cuyo texto dice "Intereses Mora (2%) - Contribucion para Pintura".
            texto_mov = _norm(mov.concepto or "")
            for pfx in ("ABONO ", "RECAUDO ", "CXC ", "PAGO "):
                if texto_mov.startswith(pfx):
                    texto_mov = texto_mov[len(pfx):].strip()
            co = None
            mejor_len = 0
            for c in conceptos_db:
                nombre_c = _norm(c.nombre)
                if nombre_c and texto_mov.startswith(nombre_c) and len(nombre_c) > mejor_len:
                    co = c
                    mejor_len = len(nombre_c)

            tipo = _tipo_concepto(co)
            c_id = co.id if co else 0
            nombre = co.nombre if co else (mov.concepto or 'General')
            val = float(mov.credito)
            if c_id not in pool:
                pool[c_id] = {'id': c_id, 'nombre': nombre,
                              'tipo': tipo, 'cobrado': 0.0, 'pagado': 0.0}
            pool[c_id]['cobrado'] += val

        # Si no hay movimientos de ingreso, usar el saldo total como CAPITAL
        if not movs_cr:
            saldo_fac = float(factura.get('saldo_pendiente', 0))
            if 0 not in pool:
                pool[0] = {'id': 0, 'nombre': 'Cartera General',
                           'tipo': 'CAPITAL', 'cobrado': 0.0, 'pagado': 0.0}
            pool[0]['cobrado'] += saldo_fac

    if not pool:
        return []

    # ── PASO 2: Procesar Aplicaciones de Pago (AP) ──
    # Atribuimos el valor de cada AP (recibo -> factura) a los conceptos de esa factura.
    # Siguiendo el mismo orden de prioridad que el motor de cartera.py,
    # PERO respetando si el recibo original fue un "Abono Dirigido".
    
    # 2.1 Obtener todos los IDs de pagos involucrados en las aplicaciones
    all_aps = db.query(AplicacionPago).filter(
        AplicacionPago.documento_factura_id.in_(list(doc_ids_pendientes))
    ).all()
    
    pago_ids = list(set(ap.documento_pago_id for ap in all_aps))
    
    # 2.2 Pre-identificar si cada pago es dirigido
    # Estructura: dict_pagos_dirigidos[pago_id] = PHConcepto o None
    dict_pagos_dirigidos = {}
    if pago_ids:
        movs_pagos = db.query(MovimientoContable).filter(
            MovimientoContable.documento_id.in_(pago_ids),
            MovimientoContable.credito > 0
        ).all()
        
        # Agrupar movimientos por pago
        movs_por_pago = {}
        for m in movs_pagos:
            if m.documento_id not in movs_por_pago:
                movs_por_pago[m.documento_id] = []
            movs_por_pago[m.documento_id].append(m)
            
        for pid, ms in movs_por_pago.items():
            es_dir, co_dir = _es_pago_dirigido(ms, conceptos_db)
            if es_dir:
                dict_pagos_dirigidos[pid] = co_dir

    # 2.3 Aplicar cada AP al pool
    for ap in all_aps:
        valor_ap = float(ap.valor_aplicado)
        if valor_ap <= 0: continue
        
        pago_id = ap.documento_pago_id
        concepto_fijo = dict_pagos_dirigidos.get(pago_id)
        
        valor_ap_restante = valor_ap
        
        if concepto_fijo:
            # Si el pago es DIRIGIDO, solo puede restar de ese concepto
            cid = concepto_fijo.id
            if cid in pool:
                c_pool = pool[cid]
                pendiente = c_pool['cobrado'] - c_pool['pagado']
                if pendiente > 0:
                    restar = min(valor_ap_restante, pendiente)
                    c_pool['pagado'] += restar
                    valor_ap_restante -= restar
            # Si sobró algo (anticipo de ese concepto), no se aplica a nada más en este desglose
        else:
            # Si el pago es GENÉRICO, sigue la jerarquía (FIFO)
            orden_map = {c.id: (c.orden if c.orden is not None else 9999) for c in conceptos_db}
            jerarquia_factura = sorted(pool.keys(), key=lambda x: (x == 0, orden_map.get(x, 9999), x))
            
            for cid in jerarquia_factura:
                if valor_ap_restante <= 0: break
                c_pool = pool[cid]
                
                pendiente = c_pool['cobrado'] - c_pool['pagado']
                if pendiente <= 0: continue
                
                restar = min(valor_ap_restante, pendiente)
                c_pool['pagado'] += restar
                valor_ap_restante -= restar

    # ── PASO 3: Consolidar resultados finales ──
    resultado = []
    # Usamos la lista de conceptos originales para mantener el orden visual
    for c_db in conceptos_db:
        if c_db.id in pool:
            data = pool[c_db.id]
            saldo = round(data['cobrado'] - data['pagado'], 2)
            if saldo > 0.01:
                resultado.append({
                    'id': c_db.id,
                    'nombre': data['nombre'],
                    'tipo': data['tipo'],
                    'saldo': saldo
                })
    
    # Agregar Cartera General si tiene saldo
    if 0 in pool:
        data = pool[0]
        saldo = round(data['cobrado'] - data['pagado'], 2)
        if saldo > 0.01:
            resultado.append({
                'id': 0,
                'nombre': data['nombre'],
                'tipo': data['tipo'],
                'saldo': saldo
            })

    return resultado
