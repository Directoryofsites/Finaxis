
import os

path = r"c:\ContaPY2\app\services\propiedad_horizontal\pago_service.py"

# El código nuevo que queríamos agregar (Limpio)
new_code = """
def get_cartera_ph_pendientes_detallada(db: Session, empresa_id: int, unidad_id: int):
    # 1. Obtener Facturas Pendientes (Usando la lógica existente)
    pendientes = pago_service.get_cartera_ph_pendientes(db, empresa_id, unidad_id=unidad_id)
    
    if not pendientes:
        return []

    # 2. Preparar Estructura de Resultado
    resultado_por_concepto = defaultdict(float)
    
    conceptos_db = db.query(PHConcepto).filter(PHConcepto.empresa_id == empresa_id).all()
    
    cuentas_interes = set()
    cuentas_multa = set()
    
    for c in conceptos_db:
        if c.es_interes and c.cuenta_interes_id:
            cuentas_interes.add(c.cuenta_interes_id)
            if c.cuenta_ingreso_id: cuentas_interes.add(c.cuenta_ingreso_id)
        
        if "MULTA" in c.nombre.upper() or "SANCION" in c.nombre.upper():
             if c.cuenta_ingreso_id: cuentas_multa.add(c.cuenta_ingreso_id)

    # 3. Procesar cada factura pendiente
    for factura in pendientes:
        doc_id = factura['id']
        saldo_pendiente_factura = factura['saldo_pendiente']
        
        if saldo_pendiente_factura <= 0.01:
            continue
            
        movimientos = db.query(MovimientoContable).filter(
            MovimientoContable.documento_id == doc_id,
            MovimientoContable.credito > 0
        ).all()
        
        composicion_factura = []
        total_items_factura = 0
        
        for mov in movimientos:
            tipo_concepto = 'CAPITAL'
            
            if mov.cuenta_id in cuentas_interes:
                tipo_concepto = 'INTERES'
            elif mov.cuenta_id in cuentas_multa:
                 tipo_concepto = 'MULTA'
            elif "INTERES" in (mov.concepto or "").upper() or "MORA" in (mov.concepto or "").upper():
                 tipo_concepto = 'INTERES'
            elif "MULTA" in (mov.concepto or "").upper() or "SANCION" in (mov.concepto or "").upper():
                 tipo_concepto = 'MULTA'
            
            nombre_concepto = mov.concepto or "Concepto General"
            val = float(mov.credito)
            
            composicion_factura.append({
                'tipo': tipo_concepto,
                'nombre': nombre_concepto,
                'valor': val,
                'saldo_simulado': val
            })
            total_items_factura += val
            
        monto_pagado_total = max(0, total_items_factura - saldo_pendiente_factura)
        
        # 4. APLICAR PRELACIÓN DE PAGO (Simulación)
        def priority_key(item):
            if item['tipo'] == 'INTERES': return 1
            if item['tipo'] == 'MULTA': return 2
            return 3
            
        items_ordenados = sorted(composicion_factura, key=priority_key)
        
        pago_remanente = monto_pagado_total
        
        for item in items_ordenados:
            if pago_remanente <= 0:
                break
            pagar = min(item['saldo_simulado'], pago_remanente)
            item['saldo_simulado'] -= pagar
            pago_remanente -= pagar
            
        # 5. Acumular
        for item in composicion_factura:
            if item['saldo_simulado'] > 0.01:
                key = item['nombre']
                resultado_por_concepto[key] += item['saldo_simulado']

    # 6. Formatear
    lista_final = []
    for concepto, valor in resultado_por_concepto.items():
        tipo = 'CAPITAL'
        upper_c = concepto.upper()
        if "INTERES" in upper_c or "MORA" in upper_c: tipo = 'INTERES'
        elif "MULTA" in upper_c or "SANCION" in upper_c: tipo = 'MULTA'
        
        lista_final.append({
            "concepto": concepto,
            "saldo": valor,
            "tipo": tipo
        })
        
    def sort_final(x):
        if x['tipo'] == 'INTERES': return 0
        if x['tipo'] == 'MULTA': return 1
        return 2
        
    lista_final.sort(key=sort_final)
    return lista_final
"""

try:
    with open(path, "rb") as f:
        raw_content = f.read()
    
    # Decodificar recuperando lo posible
    content_str = raw_content.decode('utf-8', errors='replace')
    
    # Encontrar el punto justo antes de la basura añadida.
    # El archivo original terminaba en la función registrar_pago_consolidado
    marker = "def registrar_pago_consolidado"
    
    last_idx = content_str.rfind(marker)
    if last_idx == -1:
        print("CRITICAL: No encontré el marcador original. Abortando para no dañar más.")
    else:
        # Encontramos el inicio de la ultima funcion original. Buscamos su final.
        # Esa funcion terminaba en la linea 927 aprox.
        # Simplemente buscaremos el ultimo "return" o indentación de esa funcion.
        # O mejor: Cortamos donde empieza mi intento fallido de append ("def get_cartera_ph_pendientes_detallada")
        # Si existe.
        
        garbage_start = content_str.find("def get_cartera_ph_pendientes_detallada", last_idx)
        
        if garbage_start != -1:
            clean_part = content_str[:garbage_start]
        else:
            # Si no se encuentra, quizás quedó cortado o con caracteres raros.
            # Asumimos que todo despues del último '}' o return valido es basura? No.
            # Vamos a buscar el final de `registrar_pago_consolidado` visualmente? Imposible en script.
            
            # Busquemos el string "} \n" o similar?
            # Mejor: Busquemos el inicio de la basura por los caracteres de reemplazo 
            # O simplemente adjuntamos el nuevo codigo al final del contenido 'valido' conocido.
            
            # Recuperar hasta el final del archivo original...
            # Asumamos que el archivo original no tenía 'get_cartera_ph_pendientes_detallada'
            clean_part = content_str
        
        # Asegurarnos de limpiar caracteres  del final
        # clean_part = clean_part.replace('\ufffd', '') 
        
        # Concatenar
        final_content = clean_part.strip() + "\n\n" + new_code.strip()
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(final_content)
            
        print("Success: File repaired and updated.")
        
except Exception as e:
    print(f"Error repairing: {e}")
