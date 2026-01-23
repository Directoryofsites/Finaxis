

def get_cartera_ph_pendientes_detallada(db: Session, empresa_id: int, unidad_id: int):
    # 1. Obtener Facturas Pendientes (Usando la lógica existente)
    # Esto ya nos da el saldo pendiente real por factura.
    pendientes = get_cartera_ph_pendientes(db, empresa_id, unidad_id=unidad_id)
    
    if not pendientes:
        return []

    # 2. Preparar Estructura de Resultado
    resultado_por_concepto = defaultdict(float)
    
    # Cache de Conceptos para identificar prioridades
    # Prioridad 1: Intereses (Mora)
    # Prioridad 2: Multas
    # Prioridad 3: Otros (Administración, Extraordinarias, etc.)
    
    # Identificar conceptos por sus cuentas contables o IDs
    conceptos_db = db.query(PHConcepto).filter(PHConcepto.empresa_id == empresa_id).all()
    
    # Mapas para clasificación rapida
    cuentas_interes = set()
    cuentas_multa = set()
    
    for c in conceptos_db:
        if c.es_interes and c.cuenta_interes_id:
            cuentas_interes.add(c.cuenta_interes_id)
            # A veces el interes se contabiliza en la cuenta ingreso directa
            if c.cuenta_ingreso_id: cuentas_interes.add(c.cuenta_ingreso_id)
        
        # Heurística para multas: Nombre contiene "MULTA" o "SANCION"
        if "MULTA" in c.nombre.upper() or "SANCION" in c.nombre.upper():
             if c.cuenta_ingreso_id: cuentas_multa.add(c.cuenta_ingreso_id)

    # 3. Procesar cada factura pendiente
    for factura in pendientes:
        doc_id = factura['id']
        saldo_pendiente_factura = factura['saldo_pendiente'] # Lo que aun se debe de esta factura total
        valor_original_factura = factura['valor_total']
        
        # Si ya está pagada (margen error), saltar
        if saldo_pendiente_factura <= 0.01:
            continue
            
        # Analizar composición original de la factura (Que se cobró?)
        # Buscamos movimientos CRÉDITO (Ingresos) del documento
        movimientos = db.query(MovimientoContable).filter(
            MovimientoContable.documento_id == doc_id,
            MovimientoContable.credito > 0
        ).all()
        
        # Estructura temporal para esta factura
        composicion_factura = []
        total_items_factura = 0
        
        for mov in movimientos:
            tipo_concepto = 'CAPITAL' # Default (Admin, Agua, etc)
            
            if mov.cuenta_id in cuentas_interes:
                tipo_concepto = 'INTERES'
            elif mov.cuenta_id in cuentas_multa:
                 tipo_concepto = 'MULTA'
            elif "INTERES" in (mov.concepto or "").upper() or "MORA" in (mov.concepto or "").upper():
                 # Segunda oportunidad para detectar Interes por texto
                 tipo_concepto = 'INTERES'
            elif "MULTA" in (mov.concepto or "").upper() or "SANCION" in (mov.concepto or "").upper():
                 # Chequear si es multa por texto
                 tipo_concepto = 'MULTA'
            
            # Nombre para mostrar
            nombre_concepto = mov.concepto or "Concepto General"
            # Limpieza: Remover prefijos comunes si se desea
            
            val = float(mov.credito)
            composicion_factura.append({
                'tipo': tipo_concepto,
                'nombre': nombre_concepto,
                'valor': val,
                'saldo_simulado': val # Inicialmente se debe todo
            })
            total_items_factura += val
            
        # Calcular Cuánto se ha Pagado de esta factura
        # Pagado = ValorOriginal - SaldoPendiente
        # OJO: ValorOriginal viene de la query de cartera (Suma Debitos CXC).
        # total_items_factura viene de Suma Creditos Ingreso. Deberían matchear (Partida doble).
        # Si no matchean (ej. impuestos), usaremos total_items_factura como base de proporción 100%.
        
        monto_pagado_total = max(0, total_items_factura - saldo_pendiente_factura)
        
        # 4. APLICAR PRELACIÓN DE PAGO (Simulación)
        # El dinero que entró (monto_pagado_total) se usa para "matar" deudas en orden:
        # 1. INTERES
        # 2. MULTA
        # 3. CAPITAL (Resto)
        
        # Ordenar composición para iterar
        # Orden de prioridad para CONSUMIR EL PAGO: Interes -> Multa -> Capital
        def priority_key(item):
            if item['tipo'] == 'INTERES': return 1
            if item['tipo'] == 'MULTA': return 2
            return 3
            
        items_ordenados = sorted(composicion_factura, key=priority_key)
        
        pago_remanente = monto_pagado_total
        
        for item in items_ordenados:
            if pago_remanente <= 0:
                break
            
            # Cuánto puedo pagar de este item?
            pagar = min(item['saldo_simulado'], pago_remanente)
            
            item['saldo_simulado'] -= pagar
            pago_remanente -= pagar
            
        # 5. Acumular lo que quedó pendiente al resultado global
        for item in composicion_factura:
            if item['saldo_simulado'] > 0.01:
                key = item['nombre']
                resultado_por_concepto[key] += item['saldo_simulado']

    # 6. Formatear para retorno
    lista_final = []
    for concepto, valor in resultado_por_concepto.items():
        # Inferir tipo para el icono/color en frontend
        tipo = 'CAPITAL'
        upper_c = concepto.upper()
        if "INTERES" in upper_c or "MORA" in upper_c: tipo = 'INTERES'
        elif "MULTA" in upper_c or "SANCION" in upper_c: tipo = 'MULTA'
        
        lista_final.append({
            "concepto": concepto,
            "saldo": valor,
            "tipo": tipo
        })
        
    # Ordenar: Intereses primero, luego Multas, luego el resto
    def sort_final(x):
        if x['tipo'] == 'INTERES': return 0
        if x['tipo'] == 'MULTA': return 1
        return 2
        
    lista_final.sort(key=sort_final)
    
    return lista_final
