# -*- coding: utf-8 -*-
# ¡¡¡ ARCHIVO AUTO-GENERADO !!!
# No editar este archivo manualmente. Ejecutar precompile_templates.py para actualizar.

TEMPLATES_EMPAQUETADOS = {
    'reports/account_ledger_report.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-g">
    <title>Auxiliar por Cuenta</title>
    <style>
        body { font-family: sans-serif; font-size: 10px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ccc; padding: 4px; text-align: left; }
        th { background-color: #f2f2f2; }
        .header { text-align: center; margin-bottom: 20px; }
        .header h1 { margin: 0; }
        .header h2 { margin: 0; font-weight: normal; }
        .report-info { margin-bottom: 15px; }
        .text-right { text-align: right; }
        .total-row td { font-weight: bold; background-color: #f8f8f8; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ empresa_nombre }}</h1>
        <h2>NIT: {{ empresa_nit }}</h2>
        <h2>Auxiliar por Cuenta</h2>
    </div>

    <div class="report-info">
        <strong>Cuenta:</strong> {{ cuenta_codigo }} - {{ cuenta_nombre }}<br>
        <strong>Periodo:</strong> Del {{ fecha_inicio }} al {{ fecha_fin }}
    </div>

    <table>
        <thead>
            <tr>
                <th>Fecha</th>
                <th>Documento</th>
                <th>Beneficiario</th>
                <th>Concepto</th>
                {% if has_cost_centers %}
                <th>C. Costo</th>
                {% endif %}
                <th class="text-right">Débito</th>
                <th class="text-right">Crédito</th>
                <th class="text-right">Saldo Parcial</th>
            </tr>
        </thead>
        <tbody>
            <tr class="total-row">
                <td colspan="{{ 5 if has_cost_centers else 4 }}"><strong>SALDO ANTERIOR</strong></td>
                <td colspan="3" class="text-right"><strong>{{ "{:,.2f}".format(saldo_anterior) }}</strong></td>
            </tr>
            {% for mov in movimientos %}
            <tr>

                <td>{{ mov.fecha.strftime('%Y-%m-%d') }}</td>
                <td>{{ mov.tipo_documento }}-{{ mov.numero_documento }}</td>
                <td>{{ mov.beneficiario or '' }}</td>
                <td>{{ mov.concepto }}</td>
                {% if has_cost_centers %}
                <td>{{ mov.centro_costo_codigo or '' }}</td>
                {% endif %}
                <td class="text-right">{{ "{:,.2f}".format(mov.debito) }}</td>
                <td class="text-right">{{ "{:,.2f}".format(mov.credito) }}</td>
                <td class="text-right">{{ "{:,.2f}".format(mov.saldo_parcial) }}</td>
            </tr>
            {% endfor %}
            <tr class="total-row">
                <td colspan="{{ 5 if has_cost_centers else 4 }}"><strong>SALDO FINAL</strong></td>
                {% set saldo_final = movimientos[-1].saldo_parcial if movimientos else saldo_anterior %}
                <td colspan="3" class="text-right"><strong>{{ "{:,.2f}".format(saldo_final) }}</strong></td>
            </tr>
        </tbody>
    </table>
</body>
</html>
''',

    'reports/auxiliar_cartera_report.html': r'''
<!DOCTYPE html>
<html>
<head>
    <title>Auxiliar de Cartera Detallado</title>
    <style>
        @page { size: letter portrait; margin: 1.5cm; }
        body { font-family: Arial, sans-serif; font-size: 10px; }
        h1, h2 { text-align: center; color: #333; margin: 0; }
        h1 { font-size: 1.4em; }
        h2 { font-size: 1.1em; font-weight: normal; }
        .company-info { text-align: center; margin-bottom: 20px; }
        .report-info { margin-bottom: 15px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #ddd; padding: 5px; text-align: left; }
        th { background-color: #f2f2f2; text-align: center; }
        .text-right { text-align: right; }
        .saldo-row td { font-weight: bold; background-color: #f0f0f0; }
        .detalle-app { padding-left: 20px !important; font-size: 0.9em; color: #555; border-top: none !important; }
    </style>
</head>
<body>
    <div class="company-info">
        <h1>{{ empresa.razon_social }}</h1>
        <h2>NIT: {{ empresa.nit }}</h2>
    </div>
    <div class="report-info">
        <h2>Auxiliar de Cartera Detallado</h2>
        <p><strong>Cliente:</strong> {{ tercero.razon_social }} (NIT: {{ tercero.nit }})</p>
        <p><strong>Periodo:</strong> Del {{ fecha_inicio }} al {{ fecha_fin }}</p>
    </div>

    <table>
        <thead>
            <tr>
                <th style="width: 12%;">Fecha</th>
                <th style="width: 18%;">Documento</th>
                <th style="width: 20%;">Débito (Cargos)</th>
                <th style="width: 20%;">Crédito (Abonos)</th>
                <th style="width: 30%;">Saldo</th>
            </tr>
        </thead>
        <tbody>
            <tr class="saldo-row">
                <td colspan="4" class="text-right">SALDO ANTERIOR</td>
                <td class="text-right">{{ '{:,.2f}'.format(reporte.saldoAnterior) }}</td>
            </tr>
            {% for mov in reporte.movimientos %}
                <tr>
                    <td>{{ mov.fecha.strftime('%Y-%m-%d') }}</td>
                    <td>{{ mov.tipo_documento }}-{{ mov.numero }}</td>
                    <td class="text-right">{{ '{:,.2f}'.format(mov.debito) }}</td>
                    <td class="text-right">{{ '{:,.2f}'.format(mov.credito) }}</td>
                    <td class="text-right">{{ '{:,.2f}'.format(mov.saldo_parcial) }}</td>
                </tr>
                {% if mov.detalle_aplicaciones %}
                    <tr>
                        <td></td>
                        <td colspan="4" class="detalle-app">
                        {% for app in mov.detalle_aplicaciones %}
                            {% if app.afectado_por %}
                                <span>↳ Abonado por {{ app.afectado_por }} por valor de {{ '{:,.2f}'.format(app.valor) }}</span><br>
                            {% elif app.afecta_a %}
                                <span>↳ Abona a {{ app.afecta_a }} por valor de {{ '{:,.2f}'.format(app.valor) }}</span><br>
                            {% endif %}
                        {% endfor %}
                        </td>
                    </tr>
                {% endif %}
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
''',

    'reports/auxiliar_cc_cuenta_report.html': r'''
<!DOCTYPE html>
<html>
<head>
    <title>Auxiliar por Centro de Costo y Cuenta</title>
    <style>
        @page { size: letter landscape; margin: 2cm 1cm 2cm 2cm; }
        body { font-family: Arial, sans-serif; font-size: 10px; }
        h1 { text-align: center; color: #333; font-size: 1.5em; margin-bottom: 5px;}
        h2 { text-align: center; color: #555; font-size: 1.1em; margin-top: 0;}
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #ddd; padding: 4px; text-align: left; font-size: 0.9em; vertical-align: top; }
        th { background-color: #f2f2f2; text-align: center; }
        /* --- INICIO: NUEVOS ESTILOS PARA TFOOT --- */
        tfoot td { 
            background-color: #e0e0e0; 
            font-weight: bold; 
            border: 1px solid #ddd;
        }
        /* --- FIN: NUEVOS ESTILOS --- */
        .text-right { text-align: right; }
        .text-center { text-align: center; }
        .company-info { text-align: center; margin-bottom: 15px; }
        .header-line { border-bottom: 2px solid #333; padding-bottom: 3px; margin-bottom: 8px; }
        .saldo-row td { font-weight: bold; background-color: #f9f9f9; }
    </style>
</head>
<body>
    <div class="company-info">
        <h1>{{ empresa_nombre }}</h1>
        <p>NIT: {{ empresa_nit }}</p>
        <div class="header-line"></div>
        <h2>Auxiliar por Centro de Costo y Cuenta</h2>
        <p>Centro de Costo: {{ centro_costo_nombre_display }}</p>
        <p>Cuenta: {{ cuenta_nombre_display }}</p>
        <p>Período: {{ fecha_inicio }} al {{ fecha_fin }}</p>
    </div>

    <table>
        <thead>
            <tr>
                <th style="width: 8%;">Fecha</th>
                <th style="width: 8%;">Doc.</th>
                <th style="width: 15%;">Beneficiario</th>
                <th style="width: 10%;">Cuenta</th>
                <th style="width: 20%;">Concepto</th>
                <th style="width: 10%;">Débito</th>
                <th style="width: 10%;">Crédito</th>
                <th style="width: 12%;">Saldo Parcial</th>
            </tr>
        </thead>
        <tbody>
            {# --- INICIO: BUCLE MODIFICADO PARA EL CUERPO DE LA TABLA --- #}
            {# Este bucle ahora renderiza todo EXCEPTO la fila de totales finales #}
            {% for row in report_rows_for_pdf %}
                {% if row.type != 'saldo_final_cc_global' %}
                    {% if row.type == 'saldo_inicial_cc_global' %}
                    <tr class="saldo-row">
                        <td colspan="7" class="text-right">SALDO INICIAL CENTRO DE COSTO</td>
                        <td class="text-right">{{ '{:,.2f}'.format(row.saldo | default(0)) }}</td>
                    </tr>
                    {% elif row.type == 'saldo_inicial_cuenta' %}
                    <tr class="saldo-row">
                        <td colspan="7" class="text-right">SALDO INICIAL CUENTA: {{ row.cuenta_codigo | default('') }} - {{ row.cuenta_nombre | default('') }}</td>
                        <td class="text-right">{{ '{:,.2f}'.format(row.saldo | default(0)) }}</td>
                    </tr>
                    {% elif row.type == 'movimiento' %}
                    <tr>
                        <td>{{ row.fecha | default('') }}</td>
                        <td>{{ row.tipo_documento | slice(0, 3) | upper | default('') }} #{{ row.numero_documento | default('') }}</td>
                        <td>{{ row.beneficiario | default('') }}</td>
                        <td>{{ row.cuenta_codigo | default('') }} - {{ row.cuenta_nombre | default('') }}</td>
                        <td>{{ row.concepto | default('') }}</td>
                        <td class="text-right">{{ '{:,.2f}'.format(row.debito | default(0)) }}</td>
                        <td class="text-right">{{ '{:,.2f}'.format(row.credito | default(0)) }}</td>
                        <td class="text-right">{{ '{:,.2f}'.format(row.saldo_parcial | default(0)) }}</td>
                    </tr>
                    {% endif %}
                {% endif %}
            {% endfor %}
            {# --- FIN: BUCLE MODIFICADO --- #}
        </tbody>
        
        {# --- INICIO: NUEVO BLOQUE TFOOT PARA LOS TOTALES --- #}
        <tfoot>
            {% for row in report_rows_for_pdf %}
                {% if row.type == 'saldo_final_cc_global' %}
                <tr>
                    <td colspan="7" class="text-right">SALDO FINAL CENTRO DE COSTO</td>
                    <td class="text-right">
                        {{ '{:,.2f}'.format(row.saldo | default(0)) }}
                    </td>
                </tr>
                {% endif %}
            {% endfor %}
        </tfoot>
        {# --- FIN: NUEVO BLOQUE TFOOT --- #}
    </table>
</body>
</html>
''',

    'reports/auxiliar_por_facturas_report.html': r'''
<!DOCTYPE html>
<html>
<head>
    <title>Auxiliar por Facturas</title>
    <style>
        @page { size: letter portrait; margin: 1.5cm; }
        body { font-family: Arial, sans-serif; font-size: 10px; }
        h1, h2 { text-align: center; color: #333; margin: 0; }
        .company-info { text-align: center; margin-bottom: 20px; }
        .report-info { margin-bottom: 15px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #ddd; padding: 5px; text-align: left; }
        th { background-color: #f2f2f2; text-align: center; }
        .text-right { text-align: right; }
        tfoot td { font-weight: bold; background-color: #f0f0f0; }
        .detalle-app { padding-left: 20px !important; font-size: 0.9em; color: #555; border-top: none !important; }
    </style>
</head>
<body>
    <div class="company-info"><h1>{{ empresa.razon_social }}</h1><h2>NIT: {{ empresa.nit }}</h2></div>
    <div class="report-info">
        <h2>Auxiliar de Cartera por Facturas</h2>
        <p><strong>Cliente:</strong> {{ tercero.razon_social }} (NIT: {{ tercero.nit }})</p>
        <p><strong>Periodo:</strong> Del {{ fecha_inicio }} al {{ fecha_fin }}</p>
    </div>
    <table>
        <thead>
            <tr>
                <th style="width: 10%;">Fecha</th>
                <th style="width: 20%;">Documento</th>
                <th style="width: 20%;">Valor Original</th>
                <th style="width: 20%;">Total Abonos</th>
                <th style="width: 20%;">Saldo Factura</th>
            </tr>
        </thead>
        <tbody>
            {% for f in reporte.facturas %}
            <tr>
                <td>{{ f.fecha.strftime('%Y-%m-%d') }}</td>
                <td>{{ f.documento }}</td>
                <td class="text-right">{{ '{:,.2f}'.format(f.valor_original) }}</td>
                <td class="text-right">{{ '{:,.2f}'.format(f.total_abonos) }}</td>
                <td class="text-right">{{ '{:,.2f}'.format(f.saldo_factura) }}</td>
            </tr>
            {% if f.abonos_detalle %}
            <tr>
                <td></td><td colspan="4" class="detalle-app">
                {% for abono in f.abonos_detalle %}
                    <span>↳ Abonado por {{ abono.documento }} por valor de {{ '{:,.2f}'.format(abono.valor) }}</span><br>
                {% endfor %}
                </td>
            </tr>
            {% endif %}
            {% endfor %}
        </tbody>
        <tfoot>
            <tr>
                <td colspan="2" class="text-right">TOTAL FACTURAS</td>
                <td class="text-right">{{ '{:,.2f}'.format(reporte.totales.total_facturas) }}</td>
                <td class="text-right">{{ '{:,.2f}'.format(reporte.totales.total_abonos) }}</td>
                <td class="text-right">{{ '{:,.2f}'.format(reporte.totales.saldo_final) }}</td>
            </tr>
        </tfoot>
    </table>
</body>
</html>
''',

    'reports/auxiliar_por_recibos_report.html': r'''
<!DOCTYPE html>
<html>
<head>
    <title>Auxiliar por Recibos de Caja</title>
    <style>
        @page { size: letter portrait; margin: 1.5cm; }
        body { font-family: Arial, sans-serif; font-size: 10px; }
        h1, h2 { text-align: center; color: #333; margin: 0; }
        .company-info { text-align: center; margin-bottom: 20px; }
        .report-info { margin-bottom: 15px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #ddd; padding: 5px; text-align: left; }
        th { background-color: #f2f2f2; text-align: center; }
        .text-right { text-align: right; }
        tfoot td { font-weight: bold; background-color: #f0f0f0; }
        .detalle-app { padding-left: 20px !important; font-size: 0.9em; color: #555; border-top: none !important; }
    </style>
</head>
<body>
    <div class="company-info"><h1>{{ empresa.razon_social }}</h1><h2>NIT: {{ empresa.nit }}</h2></div>
    <div class="report-info">
        <h2>Auxiliar de Cartera por Recibos de Caja</h2>
        <p><strong>Cliente:</strong> {{ tercero.razon_social }} (NIT: {{ tercero.nit }})</p>
        <p><strong>Periodo:</strong> Del {{ fecha_inicio }} al {{ fecha_fin }}</p>
    </div>
    <table>
        <thead>
            <tr>
                <th style="width: 15%;">Fecha</th>
                <th style="width: 35%;">Documento (Recibo)</th>
                <th style="width: 35%;">Valor Recibo</th>
            </tr>
        </thead>
        <tbody>
            {% for r in reporte.recibos %}
            <tr>
                <td>{{ r.fecha.strftime('%Y-%m-%d') }}</td>
                <td>{{ r.documento }}</td>
                <td class="text-right">{{ '{:,.2f}'.format(r.valor_total) }}</td>
            </tr>
            {% if r.facturas_afectadas %}
            <tr>
                <td></td><td colspan="2" class="detalle-app">
                {% for f in r.facturas_afectadas %}
                    <span>↳ Abona a {{ f.documento }} por valor de {{ '{:,.2f}'.format(f.valor) }}</span><br>
                {% endfor %}
                </td>
            </tr>
            {% endif %}
            {% endfor %}
        </tbody>
        <tfoot>
            <tr>
                <td colspan="2" class="text-right">TOTAL RECIBOS DE CAJA</td>
                <td class="text-right">{{ '{:,.2f}'.format(reporte.totales.total_recibos) }}</td>
            </tr>
        </tfoot>
    </table>
</body>
</html>
''',

    'reports/auxiliar_proveedores_por_facturas_report.html': r'''
<!DOCTYPE html>
<html>
<head>
    <title>Auxiliar por Facturas de Compra</title>
    <style>
        @page { size: letter portrait; margin: 1.5cm; }
        body { font-family: Arial, sans-serif; font-size: 10px; }
        h1, h2 { text-align: center; color: #333; margin: 0; }
        .company-info { text-align: center; margin-bottom: 20px; }
        .report-info { margin-bottom: 15px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #ddd; padding: 5px; text-align: left; }
        th { background-color: #f2f2f2; text-align: center; }
        .text-right { text-align: right; }
        tfoot td { font-weight: bold; background-color: #f0f0f0; }
        .detalle-app { padding-left: 20px !important; font-size: 0.9em; color: #555; border-top: none !important; }
    </style>
</head>
<body>
    <div class="company-info"><h1>{{ empresa.razon_social }}</h1><h2>NIT: {{ empresa.nit }}</h2></div>
    <div class="report-info">
        <h2>Auxiliar de Proveedores por Facturas de Compra</h2>
        <p><strong>Proveedor:</strong> {{ tercero.razon_social }} (NIT: {{ tercero.nit }})</p>
        <p><strong>Periodo:</strong> Del {{ fecha_inicio }} al {{ fecha_fin }}</p>
    </div>
    <table>
        <thead>
            <tr>
                <th style="width: 10%;">Fecha</th>
                <th style="width: 20%;">Documento</th>
                <th style="width: 20%;">Valor Original</th>
                <th style="width: 20%;">Total Abonos</th>
                <th style="width: 20%;">Saldo Factura</th>
            </tr>
        </thead>
        <tbody>
            {% for f in reporte.facturas %}
            <tr>
                <td>{{ f.fecha.strftime('%Y-%m-%d') }}</td>
                <td>{{ f.documento }}</td>
                <td class="text-right">{{ '{:,.2f}'.format(f.valor_original) }}</td>
                <td class="text-right">{{ '{:,.2f}'.format(f.total_abonos) }}</td>
                <td class="text-right">{{ '{:,.2f}'.format(f.saldo_factura) }}</td>
            </tr>
            {% if f.abonos_detalle %}
            <tr>
                <td></td><td colspan="4" class="detalle-app">
                {% for abono in f.abonos_detalle %}
                    <span>↳ Pagado por {{ abono.documento }} por valor de {{ '{:,.2f}'.format(abono.valor) }}</span><br>
                {% endfor %}
                </td>
            </tr>
            {% endif %}
            {% endfor %}
        </tbody>
        <tfoot>
            <tr>
                <td colspan="2" class="text-right">TOTALES</td>
                <td class="text-right">{{ '{:,.2f}'.format(reporte.totales.total_facturas) }}</td>
                <td class="text-right">{{ '{:,.2f}'.format(reporte.totales.total_abonos) }}</td>
                <td class="text-right">{{ '{:,.2f}'.format(reporte.totales.saldo_final) }}</td>
            </tr>
        </tfoot>
    </table>
</body>
</html>
''',

    'reports/auxiliar_proveedores_por_recibos_report.html': r'''
<!DOCTYPE html>
<html>
<head>
    <title>Auxiliar por Comprobantes de Egreso</title>
    <style>
        @page { size: letter portrait; margin: 1.5cm; }
        body { font-family: Arial, sans-serif; font-size: 10px; }
        h1, h2 { text-align: center; color: #333; margin: 0; }
        .company-info { text-align: center; margin-bottom: 20px; }
        .report-info { margin-bottom: 15px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #ddd; padding: 5px; text-align: left; }
        th { background-color: #f2f2f2; text-align: center; }
        .text-right { text-align: right; }
        tfoot td { font-weight: bold; background-color: #f0f0f0; }
        .detalle-app { padding-left: 20px !important; font-size: 0.9em; color: #555; border-top: none !important; }
    </style>
</head>
<body>
    <div class="company-info"><h1>{{ empresa.razon_social }}</h1><h2>NIT: {{ empresa.nit }}</h2></div>
    <div class="report-info">
        <h2>Auxiliar de Proveedores por Comprobantes de Egreso</h2>
        <p><strong>Proveedor:</strong> {{ tercero.razon_social }} (NIT: {{ tercero.nit }})</p>
        <p><strong>Periodo:</strong> Del {{ fecha_inicio }} al {{ fecha_fin }}</p>
    </div>
    <table>
        <thead>
            <tr>
                <th style="width: 15%;">Fecha</th>
                <th style="width: 35%;">Documento (Pago)</th>
                <th style="width: 35%;">Valor Pago</th>
            </tr>
        </thead>
        <tbody>
            {% for r in reporte.recibos %}
            <tr>
                <td>{{ r.fecha.strftime('%Y-%m-%d') }}</td>
                <td>{{ r.documento }}</td>
                <td class="text-right">{{ '{:,.2f}'.format(r.valor_total) }}</td>
            </tr>
            {% if r.facturas_afectadas %}
            <tr>
                <td></td><td colspan="2" class="detalle-app">
                {% for f in r.facturas_afectadas %}
                    <span>↳ Paga a {{ f.documento }} por valor de {{ '{:,.2f}'.format(f.valor) }}</span><br>
                {% endfor %}
                </td>
            </tr>
            {% endif %}
            {% endfor %}
        </tbody>
        <tfoot>
            <tr>
                <td colspan="2" class="text-right">TOTAL COMPROBANTES DE EGRESO</td>
                <td class="text-right">{{ '{:,.2f}'.format(reporte.totales.total_recibos) }}</td>
            </tr>
        </tfoot>
    </table>
</body>
</html>
''',

    'reports/auxiliar_proveedores_report.html': r'''
<!DOCTYPE html>
<html>
<head>
    <title>Auxiliar de Proveedores Detallado</title>
    <style>
        @page { size: letter portrait; margin: 1.5cm; }
        body { font-family: Arial, sans-serif; font-size: 10px; }
        h1, h2 { text-align: center; color: #333; margin: 0; }
        .company-info { text-align: center; margin-bottom: 20px; }
        .report-info { margin-bottom: 15px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #ddd; padding: 5px; text-align: left; }
        th { background-color: #f2f2f2; text-align: center; }
        .text-right { text-align: right; }
        .saldo-row td { font-weight: bold; background-color: #f0f0f0; }
        .detalle-app { padding-left: 20px !important; font-size: 0.9em; color: #555; border-top: none !important; }
    </style>
</head>
<body>
    <div class="company-info">
        <h1>{{ empresa.razon_social }}</h1>
        <h2>NIT: {{ empresa.nit }}</h2>
    </div>
    <div class="report-info">
        <h2>Auxiliar de Proveedores Detallado</h2>
        <p><strong>Proveedor:</strong> {{ tercero.razon_social }} (NIT: {{ tercero.nit }})</p>
        <p><strong>Periodo:</strong> Del {{ fecha_inicio }} al {{ fecha_fin }}</p>
    </div>

    <table>
        <thead>
            <tr>
                <th style="width: 12%;">Fecha</th>
                <th style="width: 25%;">Documento</th>
                <th style="width: 21%;">Débito (Pagos)</th>
                <th style="width: 21%;">Crédito (Deudas)</th>
                <th style="width: 21%;">Saldo</th>
            </tr>
        </thead>
        <tbody>
            <tr class="saldo-row">
                <td colspan="4" class="text-right">SALDO ANTERIOR</td>
                <td class="text-right">{{ '{:,.2f}'.format(reporte.saldoAnterior) }}</td>
            </tr>
            {% for mov in reporte.movimientos %}
                <tr>
                    <td>{{ mov.fecha.strftime('%Y-%m-%d') }}</td>
                    <td>{{ mov.tipo_documento }}-{{ mov.numero }}</td>
                    <td class="text-right">{{ '{:,.2f}'.format(mov.debito) }}</td>
                    <td class="text-right">{{ '{:,.2f}'.format(mov.credito) }}</td>
                    <td class="text-right">{{ '{:,.2f}'.format(mov.saldo_parcial) }}</td>
                </tr>
                {% if mov.detalle_aplicaciones %}
                    <tr>
                        <td></td>
                        <td colspan="4" class="detalle-app">
                        {% for app in mov.detalle_aplicaciones %}
                            {% if app.afectado_por %}
                                <span>↳ Pagado por {{ app.afectado_por }} por valor de {{ '{:,.2f}'.format(app.valor) }}</span><br>
                            {% elif app.afecta_a %}
                                <span>↳ Paga a {{ app.afecta_a }} por valor de {{ '{:,.2f}'.format(app.valor) }}</span><br>
                            {% endif %}
                        {% endfor %}
                        </td>
                    </tr>
                {% endif %}
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
''',

    'reports/balance_de_prueba_cc_report.html': r'''
<!DOCTYPE html>
<html>
<head>
    <title>Balance de Prueba por Centro de Costo</title>
    <style>
        body { font-family: sans-serif; margin: 20px; }
        h1 { text-align: center; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 10px; }
        th, td { border: 1px solid #ddd; padding: 6px; text-align: left; }
        th { background-color: #f2f2f2; }
        .text-right { text-align: right; }
        .nivel-1 { font-weight: bold; background-color: #e0e0e0; }
        .nivel-2 { font-weight: bold; background-color: #f0f0f0; padding-left: 20px; }
        .nivel-3 { padding-left: 40px; }
        .nivel-4 { padding-left: 60px; }
        .nivel-5 { padding-left: 80px; }
        tfoot { font-weight: bold; background-color: #e0e0e0; }

        .report-header {
        text-align: center;
        margin-bottom: 30px;
    }
    .company-info h1 {
        margin: 0;
        font-size: 18px;
    }
    .company-info p {
        margin: 0;
        font-size: 14px;
        color: #555;
    }
    .report-info {
        margin-top: 15px;
    }
    .report-info h2 {
        margin: 0;
        font-size: 16px;
    }
    .report-info p {
        margin: 0;
        font-size: 12px;
        color: #777;
    }
    </style>
</head>
<body>

    <header class="report-header">
    <div class="company-info">
        <h1>{{ empresa.razon_social if empresa else 'Nombre de Empresa no disponible' }}</h1>
        <p>NIT: {{ empresa.nit if empresa else 'N/A' }}</p>
    </div>
    <div class="report-info">
        <h2>{{ titulo_reporte }}</h2>
        <p>{{ periodo }}</p>
        
        {# --- INICIO: NUEVO BLOQUE CONDICIONAL PARA MOSTRAR LA CUENTA --- #}
        {% if cuenta_info %}
        <p><b>Cuenta:</b> {{ cuenta_info.codigo }} - {{ cuenta_info.nombre }}</p>
        {% endif %}
        {# --- FIN: NUEVO BLOQUE CONDICIONAL --- #}
    </div>
</header>
    <table>
        <thead>
            <tr>
                <th>Código</th>
                <th>Nombre del Centro de Costo</th>
                <th class="text-right">Saldo Inicial</th>
                <th class="text-right">Débitos</th>
                <th class="text-right">Créditos</th>
                <th class="text-right">Nuevo Saldo</th>
            </tr>
        </thead>
        <tbody>
            {% for fila in filas %}
            <tr class="nivel-{{ fila.nivel }}">
                <td>{{ fila.codigo }}</td>
                <td>{{ fila.nombre }}</td>
                <td class="text-right">{{ "{:,.2f}".format(fila.saldo_inicial) }}</td>
                <td class="text-right">{{ "{:,.2f}".format(fila.debito) }}</td>
                <td class="text-right">{{ "{:,.2f}".format(fila.credito) }}</td>
                <td class="text-right">{{ "{:,.2f}".format(fila.nuevo_saldo) }}</td>
            </tr>
            {% endfor %}
        </tbody>
        <tfoot>
            <tr>
                <td colspan="2">TOTALES</td>
                <td class="text-right">{{ "{:,.2f}".format(totales.saldo_inicial) }}</td>
                <td class="text-right">{{ "{:,.2f}".format(totales.debito) }}</td>
                <td class="text-right">{{ "{:,.2f}".format(totales.credito) }}</td>
                <td class="text-right">{{ "{:,.2f}".format(totales.nuevo_saldo) }}</td>
            </tr>
        </tfoot>
    </table>
</body>
</html>
''',

    'reports/balance_de_prueba_report.html': r'''
<!DOCTYPE html>
<html>
<head>
    <title>Balance de Prueba</title>
    <style>
        body { font-family: sans-serif; margin: 20px; }
        h1 { text-align: center; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 10px; }
        th, td { border: 1px solid #ddd; padding: 6px; text-align: left; }
        th { background-color: #f2f2f2; }
        .text-right { text-align: right; }
        .nivel-1 { font-weight: bold; background-color: #e0e0e0; }
        .nivel-2 { font-weight: bold; background-color: #f0f0f0; padding-left: 20px; }
        .nivel-3 { padding-left: 40px; }
        .nivel-4 { padding-left: 60px; }
        .nivel-5 { padding-left: 80px; }
        tfoot { font-weight: bold; background-color: #e0e0e0; }

        .report-header {
        text-align: center;
        margin-bottom: 30px;
    }
    .company-info h1 {
        margin: 0;
        font-size: 18px;
    }
    .company-info p {
        margin: 0;
        font-size: 14px;
        color: #555;
    }
    .report-info {
        margin-top: 15px;
    }
    .report-info h2 {
        margin: 0;
        font-size: 16px;
    }
    .report-info p {
        margin: 0;
        font-size: 12px;
        color: #777;
    }
    </style>
</head>
<body>

    <header class="report-header">
    <div class="company-info">
        <h1>{{ empresa.razon_social if empresa else 'Nombre de Empresa no disponible' }}</h1>
        <p>NIT: {{ empresa.nit if empresa else 'N/A' }}</p>
    </div>
    <div class="report-info">
        <h2>{{ titulo_reporte }}</h2>
        <p>{{ periodo }}</p>
    </div>
</header>
    <table>
        <thead>
            <tr>
                <th>Código</th>
                <th>Nombre de la Cuenta</th>
                <th class="text-right">Saldo Inicial</th>
                <th class="text-right">Débitos</th>
                <th class="text-right">Créditos</th>
                <th class="text-right">Nuevo Saldo</th>
            </tr>
        </thead>
        <tbody>
            {% for fila in filas %}
            <tr class="nivel-{{ fila.nivel }}">
                <td>{{ fila.codigo }}</td>
                <td>{{ fila.nombre }}</td>
                <td class="text-right">{{ "{:,.2f}".format(fila.saldo_inicial) }}</td>
                <td class="text-right">{{ "{:,.2f}".format(fila.debito) }}</td>
                <td class="text-right">{{ "{:,.2f}".format(fila.credito) }}</td>
                <td class="text-right">{{ "{:,.2f}".format(fila.nuevo_saldo) }}</td>
            </tr>
            {% endfor %}
        </tbody>
        <tfoot>
            <tr>
                <td colspan="2">TOTALES</td>
                <td class="text-right">{{ "{:,.2f}".format(totales.saldo_inicial) }}</td>
                <td class="text-right">{{ "{:,.2f}".format(totales.debito) }}</td>
                <td class="text-right">{{ "{:,.2f}".format(totales.credito) }}</td>
                <td class="text-right">{{ "{:,.2f}".format(totales.nuevo_saldo) }}</td>
            </tr>
        </tfoot>
    </table>
</body>
</html>
''',

    'reports/balance_general_cc_report.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Balance General por Centro de Costo</title>
    <style>
        @page {
            size: letter;
            margin: 1.5cm;
        }
        body {
            font-family: Arial, sans-serif;
            font-size: 10pt;
            color: #333;
        }
        .header {
            text-align: center;
            margin-bottom: 2rem;
            border-bottom: 1px solid #ccc;
            padding-bottom: 1rem;
        }
        .header h1 {
            margin: 0;
            font-size: 16pt;
        }
        .header p {
            margin: 2px 0;
            font-size: 10pt;
        }
        .report-title {
            text-align: center;
            margin-bottom: 1.5rem;
        }
        .report-title h2 {
            margin: 0;
            font-size: 14pt;
        }
        .section {
            margin-bottom: 1.5rem;
        }
        .section-title {
            font-weight: bold;
            font-size: 12pt;
            border-bottom: 2px solid #333;
            padding-bottom: 4px;
            margin-bottom: 8px;
        }
        .item-row {
            display: flex;
            justify-content: space-between;
            padding: 4px 0;
        }
        .item-row span:last-child {
            font-family: monospace;
            text-align: right;
        }
        .total-row {
            display: flex;
            justify-content: space-between;
            font-weight: bold;
            border-top: 1px solid #666;
            margin-top: 8px;
            padding-top: 4px;
            font-size: 11pt;
        }
        .grand-total-row {
            display: flex;
            justify-content: space-between;
            font-weight: bold;
            font-size: 12pt;
            background-color: #f0f0f0;
            padding: 8px;
            margin-top: 1rem;
            border-top: 2px solid #333;
            border-bottom: 2px solid #333;
        }
        .utilidad-row {
            color: #0056b3;
        }
    </style>
</head>
<body>

    <div class="header">
        <h1>{{ empresa.razon_social or 'Nombre de Empresa no Disponible' }}</h1>
        <p>NIT: {{ empresa.nit or 'NIT no disponible' }}</p>
    </div>

    <div class="report-title">
        <h2>Balance General</h2>
        {# --- ESTE ES EL CAMBIO CLAVE --- #}
        {% if centro_costo_nombre %}
            <p style="font-size: 1.1em; color: #555;">Centro de Costo: {{ centro_costo_nombre }}</p>
        {% endif %}
        <p>Al {{ fecha_corte.strftime('%d de %B de %Y') }}</p>
    </div>

    <div class="section">
        <div class="section-title">Activos</div>
        {% for item in reporte.activos %}
            <div class="item-row">
                <span>{{ item.codigo }} - {{ item.nombre }}</span>
                <span>{{ "{:,.2f}".format(item.saldo) }}</span>
            </div>
        {% endfor %}
        <div class="total-row">
            <span>TOTAL ACTIVOS</span>
            <span>{{ "{:,.2f}".format(reporte.total_activos) }}</span>
        </div>
    </div>

    <div class="section">
        <div class="section-title">Pasivos</div>
        {% for item in reporte.pasivos %}
            <div class="item-row">
                <span>{{ item.codigo }} - {{ item.nombre }}</span>
                <span>{{ "{:,.2f}".format(item.saldo) }}</span>
            </div>
        {% endfor %}
        <div class="total-row">
            <span>TOTAL PASIVOS</span>
            <span>{{ "{:,.2f}".format(reporte.total_pasivos) }}</span>
        </div>
    </div>

    <div class="section">
        <div class="section-title">Patrimonio</div>
        {% for item in reporte.patrimonio %}
            <div class="item-row">
                <span>{{ item.codigo }} - {{ item.nombre }}</span>
                <span>{{ "{:,.2f}".format(item.saldo) }}</span>
            </div>
        {% endfor %}
        <div class="item-row utilidad-row">
            <span>3605 - Utilidad (Pérdida) del Ejercicio</span>
            <span>{{ "{:,.2f}".format(reporte.utilidad_ejercicio) }}</span>
        </div>
        <div class="total-row">
            <span>TOTAL PATRIMONIO</span>
            <span>{{ "{:,.2f}".format(reporte.total_patrimonio) }}</span>
        </div>
    </div>

    <div class="grand-total-row">
        <span>TOTAL PASIVO + PATRIMONIO</span>
        <span>{{ "{:,.2f}".format(reporte.total_pasivo_patrimonio) }}</span>
    </div>

</body>
</html>

''',

    'reports/balance_general_report.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Balance General</title>
    <style>
        @page {
            size: letter;
            margin: 1.5cm;
        }
        body {
            font-family: Arial, sans-serif;
            font-size: 10pt;
            color: #333;
        }
        .header {
            text-align: center;
            margin-bottom: 2rem;
            border-bottom: 1px solid #ccc;
            padding-bottom: 1rem;
        }
        .header h1 {
            margin: 0;
            font-size: 16pt;
        }
        .header p {
            margin: 2px 0;
            font-size: 10pt;
        }
        .report-title {
            text-align: center;
            margin-bottom: 1.5rem;
        }
        .report-title h2 {
            margin: 0;
            font-size: 14pt;
        }
        .section {
            margin-bottom: 1.5rem;
        }
        .section-title {
            font-weight: bold;
            font-size: 12pt;
            border-bottom: 2px solid #333;
            padding-bottom: 4px;
            margin-bottom: 8px;
        }
        .item-row {
            display: flex;
            justify-content: space-between;
            padding: 4px 0;
        }
        .item-row span:last-child {
            font-family: monospace;
            text-align: right;
        }
        .total-row {
            display: flex;
            justify-content: space-between;
            font-weight: bold;
            border-top: 1px solid #666;
            margin-top: 8px;
            padding-top: 4px;
            font-size: 11pt;
        }
        .grand-total-row {
            display: flex;
            justify-content: space-between;
            font-weight: bold;
            font-size: 12pt;
            background-color: #f0f0f0;
            padding: 8px;
            margin-top: 1rem;
            border-top: 2px solid #333;
            border-bottom: 2px solid #333;
        }
        .utilidad-row {
            color: #0056b3;
        }
    </style>
</head>
<body>

    <div class="header">
        <h1>{{ empresa.razon_social or 'Nombre de Empresa no Disponible' }}</h1>
        <p>NIT: {{ empresa.nit or 'NIT no disponible' }}</p>
    </div>

    <div class="report-title">
        <h2>Balance General</h2>
        <p>Al {{ fecha_corte.strftime('%d de %B de %Y') }}</p>
    </div>

    <div class="section">
        <div class="section-title">Activos</div>
        {% for item in reporte.activos %}
            <div class="item-row">
                <span>{{ item.codigo }} - {{ item.nombre }}</span>
                <span>{{ "{:,.2f}".format(item.saldo) }}</span>
            </div>
        {% endfor %}
        <div class="total-row">
            <span>TOTAL ACTIVOS</span>
            <span>{{ "{:,.2f}".format(reporte.total_activos) }}</span>
        </div>
    </div>

    <div class="section">
        <div class="section-title">Pasivos</div>
        {% for item in reporte.pasivos %}
            <div class="item-row">
                <span>{{ item.codigo }} - {{ item.nombre }}</span>
                <span>{{ "{:,.2f}".format(item.saldo) }}</span>
            </div>
        {% endfor %}
        <div class="total-row">
            <span>TOTAL PASIVOS</span>
            <span>{{ "{:,.2f}".format(reporte.total_pasivos) }}</span>
        </div>
    </div>

    <div class="section">
        <div class="section-title">Patrimonio</div>
        {% for item in reporte.patrimonio %}
            <div class="item-row">
                <span>{{ item.codigo }} - {{ item.nombre }}</span>
                <span>{{ "{:,.2f}".format(item.saldo) }}</span>
            </div>
        {% endfor %}
        <div class="item-row utilidad-row">
            <span>3605 - Utilidad (Pérdida) del Ejercicio</span>
            <span>{{ "{:,.2f}".format(reporte.utilidad_ejercicio) }}</span>
        </div>
        <div class="total-row">
            <span>TOTAL PATRIMONIO</span>
            <span>{{ "{:,.2f}".format(reporte.total_patrimonio) }}</span>
        </div>
    </div>

    <div class="grand-total-row">
        <span>TOTAL PASIVO + PATRIMONIO</span>
        <span>{{ "{:,.2f}".format(reporte.total_pasivo_patrimonio) }}</span>
    </div>

</body>
</html>
''',

    'reports/cartilla_inventario_admin_report.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{{ titulo_reporte }}</title>
    <style>
        body { font-family: 'Helvetica', 'Arial', sans-serif; font-size: 10px; color: #333; }
        @page { size: Letter portrait; margin: 1cm; }
        h1 { font-size: 16px; text-align: center; margin-bottom: 5px; }
        .header-info { text-align: center; font-size: 11px; margin-bottom: 20px; }
        .header-info p { margin: 2px 0; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #ccc; padding: 4px 6px; }
        th { background-color: #f0f0f0; font-size: 10px; text-align: center; }
        .text-right { text-align: right; }
        .text-center { text-align: center; }
        .font-mono { font-family: 'Courier New', Courier, monospace; }
        .no-data { text-align: center; font-style: italic; padding: 20px; }
    </style>
</head>
<body>
    <div class="header-info">
        <p style="font-size: 14px; font-weight: bold;">{{ empresa_nombre }}</p>
        <h1>{{ titulo_reporte }}</h1>
        <p>Generado: {{ fecha_reporte }}</p>
    </div>

    {% if not productos %}
        <p class="no-data">No se encontraron productos para los filtros seleccionados.</p>
    {% else %}
        <table>
            <thead>
                <tr>
                    <th>Código</th>
                    <th>Producto / Servicio</th>
                    <th>Grupo</th>
                    <th class="text-right">Costo Promedio</th>
                    <th class="text-right">Precio Base Manual</th>
                    <th class="text-right">Stock Actual</th>
                </tr>
            </thead>
            <tbody>
                {% for p in productos %}
                <tr>
                    <td class="font-mono">{{ p.codigo }}</td>
                    <td>{{ p.nombre }} {% if p.es_servicio %} <span style="color: blue;">(Servicio)</span> {% endif %}</td>
                    <td>{{ p.grupo_nombre }}</td>
                    {# Usamos format_miles si está registrado, sino, forzamos 2 decimales #}
                    <td class="text-right font-mono">{{ p.costo_promedio | format_miles | default(p.costo_promedio | default(0) | round(2)) }}</td>
                    <td class="text-right font-mono">{{ p.precio_base_manual | format_miles | default(p.precio_base_manual | default(0) | round(2)) }}</td>
                    <td class="text-right font-mono">{{ p.stock_actual | round(2) }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    {% endif %}
</body>
</html>
''',

    'reports/estado_cuenta_cliente_report.html': r'''
<!DOCTYPE html>
<html>
<head>
    <title>Estado de Cuenta</title>
    <style>
        @page { size: letter portrait; margin: 1.5cm; }
        body { font-family: Arial, sans-serif; font-size: 10px; }
        h1, h2 { text-align: center; color: #333; margin: 0; }
        .company-info { text-align: center; margin-bottom: 20px; }
        .report-info { margin-bottom: 15px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #ddd; padding: 5px; text-align: left; }
        th { background-color: #f2f2f2; text-align: center; }
        .text-right { text-align: right; }
        .text-center { text-align: center; }
        tfoot td { font-weight: bold; background-color: #e0e0e0; }
        .aging-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-top: 20px; }
        .aging-box { border: 1px solid #ccc; padding: 8px; text-align: center; }
        .aging-box h4 { margin: 0 0 5px 0; font-size: 0.9em; }
        .aging-box p { margin: 0; font-size: 1.2em; font-weight: bold; }
        .vencida { color: #d9534f; }
        .por-vencer { color: #5cb85c; }
    </style>
</head>
<body>
    <div class="company-info">
        <h1>{{ empresa.razon_social }}</h1>
        <h2>NIT: {{ empresa.nit }}</h2>
    </div>
    <div class="report-info">
        <h2>Estado de Cuenta de Cliente</h2>
        <p><strong>Cliente:</strong> {{ reporte.clienteInfo.razon_social }} (NIT: {{ reporte.clienteInfo.nit }})</p>
        <p><strong>Fecha de Corte:</strong> {{ reporte.fechaCorte }}</p>
    </div>
    <table>
        <thead>
            <tr>
                <th>Documento</th>
                <th>Fecha Doc.</th>
                <th class="text-right">Valor Original</th>
                <th class="text-right">Abonos</th>
                <th class="text-right">Saldo</th>
                <th class="text-center">Mora / Vencimiento</th>
            </tr>
        </thead>
        <tbody>
            {% for factura in reporte.facturas %}
            <tr>
                <td>{{ factura.tipo_documento }}-{{ factura.numero }}</td>
                <td>{{ factura.fecha }}</td>
                <td class="text-right">{{ '{:,.2f}'.format(factura.valor_original) }}</td>
                <td class="text-right">({{ '{:,.2f}'.format(factura.abonos) }})</td>
                <td class="text-right">{{ '{:,.2f}'.format(factura.saldo_pendiente) }}</td>
                <td class="text-center">
                    {% if factura.estado == 'VENCIDA' %}
                        <span class="vencida">{{ factura.dias_mora }} días de mora</span>
                    {% else %}
                        <span class="por-vencer">Vence en {{ factura.dias_para_vencer }} días</span>
                    {% endif %}
                </td>
            </tr>
            {% else %}
            <tr><td colspan="6" class="text-center">Este cliente no tiene facturas con saldo pendiente.</td></tr>
            {% endfor %}
        </tbody>
        <tfoot>
            <tr>
                <td colspan="4" class="text-right"><strong>SALDO TOTAL CLIENTE:</strong></td>
                <td colspan="2" class="text-right"><strong>{{ '{:,.2f}'.format(reporte.saldoTotal) }}</strong></td>
            </tr>
        </tfoot>
    </table>

    <div class="aging-grid">
        <div class="aging-box"><h4 class="por-vencer">Por Vencer</h4><p>{{ '{:,.2f}'.format(reporte.edades.por_vencer) }}</p></div>
        <div class="aging-box"><h4 class="vencida">1-30 Días</h4><p>{{ '{:,.2f}'.format(reporte.edades.vencida_1_30) }}</p></div>
        <div class="aging-box"><h4 class="vencida">31-60 Días</h4><p>{{ '{:,.2f}'.format(reporte.edades.vencida_31_60) }}</p></div>
        <div class="aging-box"><h4 class="vencida">61-90 Días</h4><p>{{ '{:,.2f}'.format(reporte.edades.vencida_61_90) }}</p></div>
        <div class="aging-box"><h4 class="vencida">+90 Días</h4><p>{{ '{:,.2f}'.format(reporte.edades.vencida_mas_90) }}</p></div>
    </div>
</body>
</html>
''',

    'reports/estado_cuenta_proveedor_report.html': r'''
<!DOCTYPE html>
<html>
<head>
    <title>Estado de Cuenta de Proveedor</title>
    <style>
        @page { size: letter portrait; margin: 1.5cm; }
        body { font-family: Arial, sans-serif; font-size: 10px; }
        h1, h2 { text-align: center; color: #333; margin: 0; }
        .company-info { text-align: center; margin-bottom: 20px; }
        .report-info { margin-bottom: 15px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #ddd; padding: 5px; text-align: left; }
        th { background-color: #f2f2f2; text-align: center; }
        .text-right { text-align: right; }
        .text-center { text-align: center; }
        tfoot td { font-weight: bold; background-color: #e0e0e0; }
        .aging-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-top: 20px; }
        .aging-box { border: 1px solid #ccc; padding: 8px; text-align: center; }
        .aging-box h4 { margin: 0 0 5px 0; font-size: 0.9em; }
        .aging-box p { margin: 0; font-size: 1.2em; font-weight: bold; }
        .vencida { color: #d9534f; }
        .por-vencer { color: #5cb85c; }
    </style>
</head>
<body>
    <div class="company-info">
        <h1>{{ empresa.razon_social }}</h1>
        <h2>NIT: {{ empresa.nit }}</h2>
    </div>
    <div class="report-info">
        <h2>Estado de Cuenta de Proveedor</h2>
        <p><strong>Proveedor:</strong> {{ reporte.proveedorInfo.razon_social }} (NIT: {{ reporte.proveedorInfo.nit }})</p>
        <p><strong>Fecha de Corte:</strong> {{ reporte.fechaCorte }}</p>
    </div>
    <table>
        <thead>
            <tr>
                <th>Documento</th>
                <th>Fecha Doc.</th>
                <th class="text-right">Valor Original</th>
                <th class="text-right">Abonos</th>
                <th class="text-right">Saldo</th>
                <th class="text-center">Mora / Vencimiento</th>
            </tr>
        </thead>
        <tbody>
            {% for factura in reporte.facturas %}
            <tr>
                <td>{{ factura.tipo_documento }}-{{ factura.numero }}</td>
                <td>{{ factura.fecha }}</td>
                <td class="text-right">{{ '{:,.2f}'.format(factura.valor_original) }}</td>
                <td class="text-right">({{ '{:,.2f}'.format(factura.abonos) }})</td>
                <td class="text-right">{{ '{:,.2f}'.format(factura.saldo_pendiente) }}</td>
                <td class="text-center">
                    {% if factura.estado == 'VENCIDA' %}
                        <span class="vencida">{{ factura.dias_mora }} días de mora</span>
                    {% else %}
                        <span class="por-vencer">Vence en {{ factura.dias_para_vencer }} días</span>
                    {% endif %}
                </td>
            </tr>
            {% else %}
            <tr><td colspan="6" class="text-center">Este proveedor no tiene facturas con saldo pendiente.</td></tr>
            {% endfor %}
        </tbody>
        <tfoot>
            <tr>
                <td colspan="4" class="text-right"><strong>SALDO TOTAL PROVEEDOR:</strong></td>
                <td colspan="2" class="text-right"><strong>{{ '{:,.2f}'.format(reporte.saldoTotal) }}</strong></td>
            </tr>
        </tfoot>
    </table>

    <div class="aging-grid">
        <div class="aging-box"><h4 class="por-vencer">Por Vencer</h4><p>{{ '{:,.2f}'.format(reporte.edades.por_vencer) }}</p></div>
        <div class="aging-box"><h4 class="vencida">1-30 Días</h4><p>{{ '{:,.2f}'.format(reporte.edades.vencida_1_30) }}</p></div>
        <div class="aging-box"><h4 class="vencida">31-60 Días</h4><p>{{ '{:,.2f}'.format(reporte.edades.vencida_31_60) }}</p></div>
        <div class="aging-box"><h4 class="vencida">61-90 Días</h4><p>{{ '{:,.2f}'.format(reporte.edades.vencida_61_90) }}</p></div>
        <div class="aging-box"><h4 class="vencida">+90 Días</h4><p>{{ '{:,.2f}'.format(reporte.edades.vencida_mas_90) }}</p></div>
    </div>
</body>
</html>
''',

    'reports/estado_inventarios_report.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Estado General de Inventarios</title>
    <style>
        @page {
            size: letter landscape;
            margin: 1.5cm;
        }
        body {
            font-family: 'Helvetica', 'Arial', sans-serif;
            font-size: 8pt;
            color: #333;
        }
        .header {
            text-align: center;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .header h1 { margin: 0; font-size: 16pt; }
        .header h2 { margin: 0; font-size: 12pt; font-weight: normal; }
        .info {
            margin-bottom: 20px;
            text-align: center;
            font-size: 10pt;
        }
        .info p { margin: 2px 0; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            border: 1px solid #ccc;
            padding: 5px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
            text-align: center;
        }
        .text-right { text-align: right; }
        tfoot td {
            font-weight: bold;
            background-color: #e8e8e8;
            border-top: 2px solid #333;
        }
    </style>
</head>
<body>

    <div class="header">
        <h1>{{ empresa_nombre }}</h1>
        <h2>Estado General de Inventarios</h2>
    </div>

    <div class="info">
        <p><strong>Período Analizado:</strong> {{ filtros.fecha_inicio }} al {{ filtros.fecha_fin }}</p>
    </div>

    <table>
        <thead>
            <tr>
                <th>Código</th>
                <th>Producto</th>
                <th class="text-right">Cant. Inicial</th>
                <th class="text-right">Valor Inicial</th>
                <th class="text-right">Cant. Entradas</th>
                <th class="text-right">Valor Entradas</th>
                <th class="text-right">Cant. Salidas</th>
                <th class="text-right">Valor Salidas</th>
                <th class="text-right">Cant. Final</th>
                <th class="text-right">Valor Final</th>
            </tr>
        </thead>
        <tbody>

            {% for item in data['items'] %}
            <tr>
                <td>{{ item.producto_codigo }}</td>
                <td>{{ item.producto_nombre }}</td>
                <td class="text-right">{{ "%.2f"|format(item.saldo_inicial_cantidad) }}</td>
                <td class="text-right">{{ "${:,.0f}".format(item.saldo_inicial_valor|float) }}</td>
                <td class="text-right">{{ "%.2f"|format(item.entradas_cantidad) }}</td>
                <td class="text-right">{{ "${:,.0f}".format(item.entradas_valor|float) }}</td>
                <td class="text-right">{{ "%.2f"|format(item.salidas_cantidad) }}</td>
                <td class="text-right">{{ "${:,.0f}".format(item.salidas_valor|float) }}</td>
                <td class="text-right">{{ "%.2f"|format(item.saldo_final_cantidad) }}</td>
                <td class="text-right">{{ "${:,.0f}".format(item.saldo_final_valor|float) }}</td>
            </tr>
            {% else %}
            <tr>
                <td colspan="10" style="text-align:center;">No se encontraron productos con movimiento en el período seleccionado.</td>
            </tr>
            {% endfor %}
        </tbody>
        <tfoot>
            <tr>
                <td colspan="3" class="text-right"><strong>TOTALES</strong></td>
                <td class="text-right"><strong>{{ "${:,.0f}".format(data.totales.saldo_inicial_valor|float) }}</strong></td>
                <td colspan="1"></td>
                <td class="text-right"><strong>{{ "${:,.0f}".format(data.totales.entradas_valor|float) }}</strong></td>
                <td colspan="1"></td>
                <td class="text-right"><strong>{{ "${:,.0f}".format(data.totales.salidas_valor|float) }}</strong></td>
                <td colspan="1"></td>
                <td class="text-right"><strong>{{ "${:,.0f}".format(data.totales.saldo_final_valor|float) }}</strong></td>
            </tr>
        </tfoot>
    </table>

</body>
</html>
''',

    'reports/income_statement_cc_report.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Estado de Resultados por Centro de Costo</title>
    <style>
        body { font-family: sans-serif; font-size: 10px; }
        .header { text-align: center; margin-bottom: 20px; }
        .header h1, .header h2, .header h3 { margin: 0; }
        .header h3 { font-weight: normal; font-style: italic; }
        .report-info { margin-bottom: 20px; text-align: center; }
        .content-table { width: 100%; border-collapse: collapse; }
        .content-table td { padding: 4px; }
        .account-row td:first-child { padding-left: 20px; }
        .total-section-row td { font-weight: bold; border-top: 1px solid #000; border-bottom: 1px solid #000; }
        .final-total-row td { font-weight: bold; border-top: 2px solid #000; border-bottom: 3px double #000; background-color: #f2f2f2; }
        .text-right { text-align: right; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ empresa_nombre }}</h1>
        <h2>NIT: {{ empresa_nit }}</h2>
        <h2>Estado de Resultados por Centro de Costo</h2>
        <h3>{{ centro_costo_nombre_display }}</h3>
    </div>

    <div class="report-info">
        <strong>Periodo:</strong> Del {{ fecha_inicio }} al {{ fecha_fin }}
    </div>

    <table class="content-table">
        <tbody>
            <tr>
                <td colspan="2"><strong>INGRESOS OPERACIONALES</strong></td>
            </tr>
            {% for ingreso in ingresos %}
            <tr class="account-row">
                <td>{{ ingreso.codigo }} - {{ ingreso.nombre }}</td>
                <td class="text-right">{{ "{:,.2f}".format(ingreso.saldo) }}</td>
            </tr>
            {% endfor %}
            <tr class="total-section-row">
                <td><strong>TOTAL INGRESOS OPERACIONALES</strong></td>
                <td class="text-right"><strong>{{ "{:,.2f}".format(totales.total_ingresos) }}</strong></td>
            </tr>

            <tr><td colspan="2">&nbsp;</td></tr>

            <tr>
                <td colspan="2"><strong>COSTOS DE VENTA</strong></td>
            </tr>
            {% for costo in costos %}
            <tr class="account-row">
                <td>{{ costo.codigo }} - {{ costo.nombre }}</td>
                <td class="text-right">{{ "{:,.2f}".format(costo.saldo) }}</td>
            </tr>
            {% endfor %}
            <tr class="total-section-row">
                <td><strong>TOTAL COSTOS DE VENTA</strong></td>
                <td class="text-right"><strong>{{ "{:,.2f}".format(totales.total_costos) }}</strong></td>
            </tr>

            <tr class="final-total-row">
                <td><strong>UTILIDAD BRUTA</strong></td>
                <td class="text-right"><strong>{{ "{:,.2f}".format(totales.utilidad_bruta) }}</strong></td>
            </tr>

            <tr><td colspan="2">&nbsp;</td></tr>

            <tr>
                <td colspan="2"><strong>GASTOS OPERACIONALES</strong></td>
            </tr>
            {% for gasto in gastos %}
            <tr class="account-row">
                <td>{{ gasto.codigo }} - {{ gasto.nombre }}</td>
                <td class="text-right">{{ "{:,.2f}".format(gasto.saldo) }}</td>
            </tr>
            {% endfor %}
            <tr class="total-section-row">
                <td><strong>TOTAL GASTOS OPERACIONALES</strong></td>
                <td class="text-right"><strong>{{ "{:,.2f}".format(totales.total_gastos) }}</strong></td>
            </tr>

            <tr class="final-total-row">
                <td><strong>UTILIDAD (O PÉRDIDA) DEL EJERCICIO</strong></td>
                <td class="text-right"><strong>{{ "{:,.2f}".format(totales.utilidad_neta) }}</strong></td>
            </tr>
        </tbody>
    </table>
</body>
</html>
''',

    'reports/income_statement_report.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Estado de Resultados</title>
    <style>
        body { font-family: sans-serif; font-size: 10px; }
        .header { text-align: center; margin-bottom: 20px; }
        .header h1, .header h2 { margin: 0; }
        .report-info { margin-bottom: 20px; text-align: center; }
        .content-table { width: 100%; border-collapse: collapse; }
        .content-table td { padding: 4px; }
        .account-row td:first-child { padding-left: 20px; }
        .total-section-row td { font-weight: bold; border-top: 1px solid #000; border-bottom: 1px solid #000; }
        .final-total-row td { font-weight: bold; border-top: 2px solid #000; border-bottom: 3px double #000; background-color: #f2f2f2; }
        .text-right { text-align: right; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ empresa_nombre }}</h1>
        <h2>NIT: {{ empresa_nit }}</h2>
        <h2>Estado de Resultados</h2>
    </div>

    <div class="report-info">
        <strong>Periodo:</strong> Del {{ fecha_inicio }} al {{ fecha_fin }}
    </div>

    <table class="content-table">
        <tbody>
            <tr>
                <td colspan="2"><strong>INGRESOS OPERACIONALES</strong></td>
            </tr>
            {% for ingreso in ingresos %}
            <tr class="account-row">
                <td>{{ ingreso.codigo }} - {{ ingreso.nombre }}</td>
                <td class="text-right">{{ "{:,.2f}".format(ingreso.saldo) }}</td>
            </tr>
            {% endfor %}
            <tr class="total-section-row">
                <td><strong>TOTAL INGRESOS OPERACIONALES</strong></td>
                <td class="text-right"><strong>{{ "{:,.2f}".format(totales.total_ingresos) }}</strong></td>
            </tr>

            <tr><td colspan="2">&nbsp;</td></tr>

            <tr>
                <td colspan="2"><strong>COSTOS DE VENTA</strong></td>
            </tr>
            {% for costo in costos %}
            <tr class="account-row">
                <td>{{ costo.codigo }} - {{ costo.nombre }}</td>
                <td class="text-right">{{ "{:,.2f}".format(costo.saldo) }}</td>
            </tr>
            {% endfor %}
            <tr class="total-section-row">
                <td><strong>TOTAL COSTOS DE VENTA</strong></td>
                <td class="text-right"><strong>{{ "{:,.2f}".format(totales.total_costos) }}</strong></td>
            </tr>

            <tr class="final-total-row">
                <td><strong>UTILIDAD BRUTA</strong></td>
                <td class="text-right"><strong>{{ "{:,.2f}".format(totales.utilidad_bruta) }}</strong></td>
            </tr>

            <tr><td colspan="2">&nbsp;</td></tr>

            <tr>
                <td colspan="2"><strong>GASTOS OPERACIONALES</strong></td>
            </tr>
            {% for gasto in gastos %}
            <tr class="account-row">
                <td>{{ gasto.codigo }} - {{ gasto.nombre }}</td>
                <td class="text-right">{{ "{:,.2f}".format(gasto.saldo) }}</td>
            </tr>
            {% endfor %}
            <tr class="total-section-row">
                <td><strong>TOTAL GASTOS OPERACIONALES</strong></td>
                <td class="text-right"><strong>{{ "{:,.2f}".format(totales.total_gastos) }}</strong></td>
            </tr>

            <tr class="final-total-row">
                <td><strong>UTILIDAD (O PÉRDIDA) DEL EJERCICIO</strong></td>
                <td class="text-right"><strong>{{ "{:,.2f}".format(totales.utilidad_neta) }}</strong></td>
            </tr>
        </tbody>
    </table>
</body>
</html>
''',

    'reports/inventarios_y_balances_report.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Libro de Inventarios y Balances</title>
    <style>
        @page {
            size: letter;
            margin: 1.5cm;
            @bottom-center {
                content: "Página " counter(page) " de " counter(pages);
                font-size: 10px;
            }
        }
        body {
            font-family: 'Helvetica', 'Arial', sans-serif;
            font-size: 10px;
            color: #333;
        }
        .header {
            text-align: center;
            margin-bottom: 25px;
            border-bottom: 1px solid #333;
            padding-bottom: 10px;
        }
        .header h1, .header h2, .header p {
            margin: 0;
            padding: 2px 0;
        }
        .report-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 25px;
        }
        .report-table td {
            padding: 5px;
        }
        .account-name {
            padding-left: 15px;
        }
        .group-header {
            font-weight: bold;
            font-size: 12px;
            background-color: #e0e0e0;
            border-bottom: 2px solid #333;
            border-top: 2px solid #333;
        }
        .total-row {
            font-weight: bold;
            border-top: 1px solid #333;
        }
        .grand-total {
            font-size: 11px;
            background-color: #f2f2f2;
            border-top: 2px double #000;
        }
        .text-right {
            text-align: right;
        }
    </style>
</head>
<body>

    <div class="header">
        <h1>{{ empresa.razon_social }}</h1>
        <h2>NIT: {{ empresa.nit }}</h2>
        <p><strong>Libro de Inventarios y Balances (Estado de Situación Financiera)</strong></p>
        <p>Con corte al {{ fecha_corte.strftime('%d de %B de %Y') }}</p>
    </div>

    <table class="report-table">
        <tr>
            <td colspan="2" class="group-header">ACTIVOS</td>
        </tr>
        {% for activo in reporte.activos %}
        <tr>
            <td>{{ activo.codigo }} - {{ activo.nombre }}</td>
            <td class="text-right">{{ "${:,.2f}".format(activo.saldo) }}</td>
        </tr>
        {% endfor %}
        <tr class="total-row grand-total">
            <td><strong>TOTAL ACTIVOS</strong></td>
            <td class="text-right"><strong>{{ "${:,.2f}".format(reporte.total_activos) }}</strong></td>
        </tr>

        <tr>
            <td colspan="2" class="group-header" style="padding-top: 20px;">PASIVOS</td>
        </tr>
        {% for pasivo in reporte.pasivos %}
        <tr>
            <td>{{ pasivo.codigo }} - {{ pasivo.nombre }}</td>
            <td class="text-right">{{ "${:,.2f}".format(pasivo.saldo) }}</td>
        </tr>
        {% endfor %}
        <tr class="total-row">
            <td><strong>Total Pasivos</strong></td>
            <td class="text-right"><strong>{{ "${:,.2f}".format(reporte.total_pasivos) }}</strong></td>
        </tr>

        <tr>
            <td colspan="2" class="group-header" style="padding-top: 20px;">PATRIMONIO</td>
        </tr>
        {% for item in reporte.patrimonio %}
        <tr>
            <td>{{ item.codigo }} - {{ item.nombre }}</td>
            <td class="text-right">{{ "${:,.2f}".format(item.saldo) }}</td>
        </tr>
        {% endfor %}
        <tr>
            <td>Utilidad (o Pérdida) del Ejercicio</td>
            <td class="text-right">{{ "${:,.2f}".format(reporte.utilidad_ejercicio) }}</td>
        </tr>
        <tr class="total-row">
            <td><strong>Total Patrimonio</strong></td>
            <td class="text-right"><strong>{{ "${:,.2f}".format(reporte.total_patrimonio) }}</strong></td>
        </tr>
        
        <tr class="total-row grand-total">
            <td><strong>TOTAL PASIVO Y PATRIMONIO</strong></td>
            <td class="text-right"><strong>{{ "${:,.2f}".format(reporte.total_pasivo_patrimonio) }}</strong></td>
        </tr>
    </table>

</body>
</html>
''',

    'reports/journal_report.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Libro Diario</title>
    <style>
        @page {
            size: letter;
            margin: 1.5cm;
            @bottom-center {
                content: "Página " counter(page) " de " counter(pages);
                font-size: 10px;
            }
        }
        body {
            font-family: 'Helvetica', 'Arial', sans-serif;
            font-size: 10px;
            color: #333;
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
            border-bottom: 1px solid #333;
            padding-bottom: 10px;
        }
        .header h1, .header h2, .header p {
            margin: 0;
            padding: 2px 0;
        }
        .header h1 {
            font-size: 16px;
        }
        .header h2 {
            font-size: 14px;
        }
        .header p {
            font-size: 12px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            border: 1px solid #ccc;
            padding: 6px;
            text-align: left;
            vertical-align: top;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        .date-header {
            background-color: #e0e0e0;
            font-weight: bold;
            text-align: center;
        }
        .text-right {
            text-align: right;
        }
        .totals-row td {
            font-weight: bold;
            background-color: #f2f2f2;
            border-top: 2px solid #333;
        }
        .document-group {
            border-left: 3px solid #f2f2f2;
        }
    </style>
</head>
<body>

    <div class="header">
        <h1>{{ empresa_nombre }}</h1>
        <h2>NIT: {{ empresa_nit }}</h2>
        <p><strong>Libro Diario</strong></p>
        <p>Desde el {{ fecha_inicio }} hasta el {{ fecha_fin }}</p>
    </div>

    <table>
        <thead>
            <tr>
                <th>Documento</th>
                <th>Beneficiario</th>
                <th>Cuenta</th>
                <th>Concepto</th>
                {% if has_cost_centers %}
                <th>C. Costo</th>
                {% endif %}
                <th class="text-right">Débito</th>
                <th class="text-right">Crédito</th>
            </tr>
        </thead>

        <tbody>
            {% for fecha, movimientos in report_data_agrupado.items() %}
                <tr>
                    <td colspan="{{ 7 if has_cost_centers else 6 }}" class="date-header">
                        Fecha: {{ fecha }}
                    </td>
                </tr>
                {% for mov in movimientos %}
                <tr>
                    <td>{{ mov.tipo_documento }}-{{ mov.numero_documento }}</td>
                    <td>{{ mov.beneficiario_nombre or '' }}</td>
                    <td>{{ mov.cuenta_codigo }} - {{ mov.cuenta_nombre }}</td>
                    <td>{{ mov.concepto }}</td>
                    {% if has_cost_centers %}
                    <td>{{ mov.centro_costo_codigo or '' }}</td>
                    {% endif %}
                    {# --- MODIFICACIÓN: Usando el filtro 'currency' --- #}
                    <td class="text-right">{{ mov.debito | currency }}</td>
                    <td class="text-right">{{ mov.credito | currency }}</td>
                </tr>
                {% endfor %}
            {% else %}
                <tr>
                    <td colspan="{{ 7 if has_cost_centers else 6 }}" style="text-align:center;">No hay movimientos para el período seleccionado.</td>
                </tr>
            {% endfor %}
        </tbody>

        <tfoot>
            <tr class="totals-row">
                <td colspan="{{ 5 if has_cost_centers else 4 }}" class="text-right"><strong>TOTALES</strong></td>
                 {# --- MODIFICACIÓN: Usando el filtro 'currency' --- #}
                <td class="text-right"><strong>{{ total_debito | currency }}</strong></td>
                <td class="text-right"><strong>{{ total_credito | currency }}</strong></td>
            </tr>
        </tfoot>
    </table>

</body>
</html>
''',

    'reports/kardex_report.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Kardex de Producto</title>
    <style>
        @page {
            size: letter landscape;
            margin: 1.5cm;
        }
        body {
            font-family: 'Helvetica', 'Arial', sans-serif;
            font-size: 8pt;
            color: #333;
        }
        .header {
            text-align: center;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .header h1 { margin: 0; font-size: 16pt; }
        .header h2 { margin: 0; font-size: 12pt; font-weight: normal; }
        .info {
            margin-bottom: 20px;
            text-align: left;
            font-size: 10pt;
            border: 1px solid #ddd;
            padding: 10px;
            border-radius: 5px;
            background-color: #f9f9f9;
        }
        .info p { margin: 2px 0; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            border: 1px solid #ccc;
            padding: 4px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
            text-align: center;
            /* Ajuste de tamaño de fuente para cabecera */
            font-size: 7.5pt; 
        }
        .text-right { text-align: right; font-family: 'Courier New', monospace; }
        .saldo-anterior {
            font-weight: bold;
            background-color: #e8e8e8;
        }
        .entrada { background-color: #e8f5e9; }
        .salida { background-color: #ffebee; }
    </style>
</head>
<body>

    <div class="header">
        <h1>{{ empresa_nombre }}</h1>
        <h2>Kardex de Producto</h2>
    </div>

    <div class="info">
        <p><strong>Producto:</strong> {{ data.producto_codigo }} - {{ data.producto_nombre }}</p>
        <p><strong>Período Analizado:</strong> {{ filtros.fecha_inicio | truncate(10, True, '') }} al {{ filtros.fecha_fin | truncate(10, True, '') }}</p>
    </div>

    <table>
        <thead>
            <tr>
                {# Ajuste de anchos para liberar espacio en el centro #}
                <th style="width:7%">Fecha</th> 
                <th style="width:10%">Documento</th>
                <th style="width:10%">Tipo Mov.</th>
                <th class="text-right" style="width:8%">Ent. Cant.</th>
                <th class="text-right" style="width:10%">Ent. C. Unit.</th>
                <th class="text-right" style="width:10%">Ent. C. Total</th>
                <th class="text-right" style="width:8%">Sal. Cant.</th>
                <th class="text-right" style="width:10%">Sal. C. Unit.</th>
                <th class="text-right" style="width:10%">Sal. C. Total</th>
                <th class="text-right" style="width:9%">Saldo Cant.</th>
                <th class="text-right" style="width:9%">Costo Promedio</th>
                <th class="text-right" style="width:10%">Saldo Valorizado</th>
            </tr>
        </thead>
        <tbody>

            {# FIX CRÍTICO DE ALINEACIÓN: Fila de Saldo Anterior #}
            {% set saldo_inicial_cant = data.totales.saldo_inicial_cantidad | default(0) | float %}
            {% set saldo_inicial_valor = data.totales.saldo_inicial_valor | default(0) | float %}
            
            {# FIX CRÍTICO: Evitar División por Cero en Costo Promedio Inicial #}
            {% set costo_prom_inicial = saldo_inicial_valor / saldo_inicial_cant if saldo_inicial_cant else 0.00 %}
            
            <tr class="saldo-anterior">
                <td>{{ filtros.fecha_inicio | truncate(10, True, '') }}</td>
                <td colspan="8">SALDO ANTERIOR</td> {# ¡FIX DE ALINEACIÓN CRÍTICO! Fusiona 8 celdas (Col 2 a Col 9) #}

                {# Las últimas 3 columnas (Saldo, Costo Prom, Saldo Val) se mantienen alineadas #}
                <td class="text-right"><strong>{{ "%.2f"|format(saldo_inicial_cant) }}</strong></td>
                <td class="text-right"><strong>{{ costo_prom_inicial | float | format_miles }}</strong></td>
                <td class="text-right"><strong>{{ saldo_inicial_valor | float | format_miles }}</strong></td>
            </tr>

            {# Bucle de Movimientos: FIX CRÍTICO: Se usa 'data.movimientos' #}
            {% for item in data.movimientos | default([]) %}
                
                <tr class="{{ 'entrada' if item.entrada_cantidad else 'salida' }}">
                    {# Columna 1-3: Fecha, Documento, Tipo Movimiento #}
                    <td>{{ item.fecha | truncate(10, True, '') }}</td>
                    <td>{{ item.documento_ref }}</td>
                    <td>{{ item.tipo_movimiento }}</td>

                    {# Columna 4-6: Entradas (Cantidad, Costo Unitario, Costo Total) #}
                    <td class="text-right">{{ "%.2f"|format(item.entrada_cantidad) if item.entrada_cantidad else '' }}</td>
                    <td class="text-right">{{ item.entrada_costo_unit | float | format_miles if item.entrada_costo_unit else '' }}</td>
                    <td class="text-right">{{ item.entrada_costo_total | float | format_miles if item.entrada_costo_total else '' }}</td>
                    
                    {# Columna 7-9: Salidas (Cantidad, Costo Unitario, Costo Total) #}
                    <td class="text-right">{{ "%.2f"|format(item.salida_cantidad) if item.salida_cantidad else '' }}</td>
                    <td class="text-right">{{ item.salida_costo_unit | float | format_miles if item.salida_costo_unit else '' }}</td>
                    <td class="text-right">{{ item.salida_costo_total | float | format_miles if item.salida_costo_total else '' }}</td>

                    {# Columna 10-12: Saldos #}
                    <td class="text-right"><strong>{{ "%.2f"|format(item.saldo_cantidad) }}</strong></td>
                    <td class="text-right"><strong>{{ item.saldo_costo_promedio | float | format_miles }}</strong></td>
                    <td class="text-right"><strong>{{ item.saldo_valor_total | float | format_miles }}</strong></td>
                </tr>
                
            {% endfor %}
        </tbody>
    </table>
    
    {# Totales Finales #}
    <div class="info">
        <p><strong>Balance del Período:</strong></p>
        <p>Entradas (Cant.): {{ "%.2f"|format(data.totales.total_entradas_cantidad) }} | Salidas (Cant.): {{ "%.2f"|format(data.totales.total_salidas_cantidad) }}</p>
        <p><strong>Saldo Final:</strong> {{ "%.2f"|format(data.totales.saldo_final_cantidad) }} unidades con un valor total de <strong>${{ data.totales.saldo_final_valor | float | format_miles }}</strong></p>
    </div>

</body>
</html>
''',

    'reports/mayor_y_balances_report.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Libro Mayor y Balances</title>
    <style>
        @page {
            size: letter;
            margin: 1.5cm;
            @bottom-center {
                content: "Página " counter(page) " de " counter(pages);
                font-size: 10px;
            }
        }
        body {
            font-family: 'Helvetica', 'Arial', sans-serif;
            font-size: 9px;
            color: #333;
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
            border-bottom: 1px solid #333;
            padding-bottom: 10px;
        }
        .header h1, .header h2, .header p {
            margin: 0;
            padding: 2px 0;
        }
        .account-block {
            margin-bottom: 25px;
            page-break-inside: avoid;
        }
        .account-header {
            background-color: #e0e0e0;
            padding: 5px;
            font-weight: bold;
            font-size: 11px;
            border: 1px solid #ccc;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 5px;
        }
        th, td {
            border: 1px solid #ccc;
            padding: 5px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        .text-right {
            text-align: right;
        }
        .summary-row td {
            font-weight: bold;
            background-color: #f2f2f2;
            border-top: 2px solid #333;
        }
    </style>
</head>
<body>

    <div class="header">
        <h1>{{ empresa_nombre }}</h1>
        <h2>NIT: {{ empresa_nit }}</h2>
        <p><strong>Libro Mayor y Balances</strong></p>
        <p>Desde el {{ fecha_inicio }} hasta el {{ fecha_fin }}</p>
    </div>

    {% for cuenta in reporte.cuentas %}
    <div class="account-block">
        <div class="account-header">
            CUENTA: {{ cuenta.cuenta_codigo }} - {{ cuenta.cuenta_nombre }}
        </div>
        <table>
            <thead>
                <tr>
                    <th>Fecha</th>
                    <th>Documento</th>
                    <th>Beneficiario</th>
                    <th>Concepto</th>
                    <th class="text-right">Débito</th>
                    <th class="text-right">Crédito</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td colspan="4"><strong>Saldo Inicial</strong></td>
                    <td colspan="2" class="text-right"><strong>{{ "${:,.2f}".format(cuenta.saldo_inicial) }}</strong></td>
                </tr>
                {% for mov in cuenta.movimientos %}
                <tr>
                    <td>{{ mov.fecha.strftime('%Y-%m-%d') }}</td>
                    <td>{{ mov.documento }}</td>
                    <td>{{ mov.beneficiario or '' }}</td>
                    <td>{{ mov.concepto }}</td>
                    <td class="text-right">{{ "${:,.2f}".format(mov.debito) }}</td>
                    <td class="text-right">{{ "${:,.2f}".format(mov.credito) }}</td>
                </tr>
                {% endfor %}
            </tbody>
            <tfoot>
                <tr class="summary-row">
                    <td colspan="4" class="text-right"><strong>Totales del Período</strong></td>
                    <td class="text-right"><strong>{{ "${:,.2f}".format(cuenta.total_debito) }}</strong></td>
                    <td class="text-right"><strong>{{ "${:,.2f}".format(cuenta.total_credito) }}</strong></td>
                </tr>
                <tr class="summary-row">
                    <td colspan="4" class="text-right"><strong>Nuevo Saldo</strong></td>
                    <td colspan="2" class="text-right"><strong>{{ "${:,.2f}".format(cuenta.nuevo_saldo) }}</strong></td>
                </tr>
            </tfoot>
        </table>
    </div>
    {% else %}
        <p style="text-align:center;">No se encontraron cuentas con movimiento para el período seleccionado.</p>
    {% endfor %}

</body>
</html>
''',

    'reports/movimiento_analitico_report.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Reporte Analítico de Movimientos</title>
    <style>
        body { font-family: 'Helvetica', sans-serif; font-size: 10px; color: #333; margin: 0; }
        @page { size: letter portrait; margin: 1.5cm; }
        
        .header { text-align: center; margin-bottom: 20px; border-bottom: 2px solid #333; padding-bottom: 10px; }
        .header h1 { margin: 0; font-size: 16px; }
        .header h2 { margin: 5px 0; font-size: 12px; font-weight: normal; }
        
        .filters { margin-bottom: 15px; background-color: #f9f9f9; padding: 10px; border-radius: 5px; }
        .filters p { margin: 2px 0; font-size: 9px; }
        
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #ccc; padding: 4px; text-align: left; }
        th { background-color: #f2f2f2; font-weight: bold; text-align: center; font-size: 9px; }
        
        .text-right { text-align: right; }
        .font-mono { font-family: 'Courier New', monospace; }
        .total-row { font-weight: bold; background-color: #e8e8e8; }
        
        .positive { color: green; }
        .negative { color: red; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ empresa_nombre }}</h1>
        <h2>Reporte Analítico de Movimientos</h2>
        <p>Período: {{ filtros.fecha_inicio }} al {{ filtros.fecha_fin }}</p>
    </div>

    <div class="filters">
        <p><strong>Bodega:</strong> {{ bodega_nombre | default('Todas', true) }}</p>
        <p><strong>Vista:</strong> {{ 'VALORIZADA ($)' if filtros.vista_por_valor else 'CANTIDADES' }}</p>
    </div>

    <table>
        <thead>
            <tr>
                <th style="width: 35%;">Producto</th>
                <th class="text-right" style="width: 15%;">Saldo Inicial</th>
                <th class="text-right" style="width: 15%;">Entradas</th>
                <th class="text-right" style="width: 15%;">Salidas</th>
                <th class="text-right" style="width: 20%;">Saldo Final</th>
            </tr>
        </thead>
        <tbody>
            {# Definimos el sufijo del campo según la vista seleccionada #}
            {% set suffix = '_valor' if filtros.vista_por_valor else '_cantidad' %}
            
            {% if data['items'] %}
                {% for item in data['items'] %}
                <tr>
                    <td>
                        <span class="font-mono" style="font-size: 9px; color: #666;">{{ item.producto_codigo }}</span><br>
                        {{ item.producto_nombre }}
                    </td>
                    
                    {# Accedemos dinámicamente al campo correcto (ej: saldo_inicial_cantidad o saldo_inicial_valor) #}
                    <td class="text-right font-mono">
                        {{ item['saldo_inicial' ~ suffix] | format_value(filtros.vista_por_valor) }}
                    </td>
                    <td class="text-right font-mono positive">
                        {{ item['total_entradas' ~ suffix] | format_value(filtros.vista_por_valor) }}
                    </td>
                    <td class="text-right font-mono negative">
                        {{ item['total_salidas' ~ suffix] | format_value(filtros.vista_por_valor) }}
                    </td>
                    <td class="text-right font-mono font-bold">
                        {{ item['saldo_final' ~ suffix] | format_value(filtros.vista_por_valor) }}
                    </td>
                </tr>
                {% endfor %}
            {% else %}
                <tr>
                    <td colspan="5" style="text-align: center; padding: 20px;">No se encontraron movimientos.</td>
                </tr>
            {% endif %}
        </tbody>
        
        {% if data['items'] %}
        <tfoot class="total-row">
            <tr>
                <td class="text-right">TOTALES GENERALES</td>
                <td class="text-right font-mono">
                    {{ data['totales']['saldo_inicial' ~ suffix] | format_value(filtros.vista_por_valor) }}
                </td>
                <td class="text-right font-mono">
                    {{ data['totales']['total_entradas' ~ suffix] | format_value(filtros.vista_por_valor) }}
                </td>
                <td class="text-right font-mono">
                    {{ data['totales']['total_salidas' ~ suffix] | format_value(filtros.vista_por_valor) }}
                </td>
                <td class="text-right font-mono">
                    {{ data['totales']['saldo_final' ~ suffix] | format_value(filtros.vista_por_valor) }}
                </td>
            </tr>
        </tfoot>
        {% endif %}
    </table>
</body>
</html>
''',


    
    
    'reports/rentabilidad_documento_report.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Análisis de Rentabilidad de Factura</title>


    <style>
        /* Usamos px para un control más preciso y compacto, igual al modelo */
        body { font-family: 'Helvetica', sans-serif; font-size: 11px; margin: 0; padding: 20px; }
        .container { width: 100%; margin: 0 auto; }
        
        /* Encabezado Central */
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { margin: 0; font-size: 12px; font-weight: normal; } /* NIT arriba */
        .header h2 { margin: 5px 0 0 0; font-size: 14px; font-weight: bold; } /* Nombre Empresa */
        .report-title { margin-top: 10px; font-size: 16px; font-weight: bold; }

        /* Tabla de Información */
        .info-table { width: 100%; margin-bottom: 15px; border-collapse: collapse; font-size: 11px; }
        .info-table td { padding: 3px 5px; vertical-align: top; }
        .label { font-weight: bold; width: 130px; }

        /* Tabla Principal de Datos */
        .main-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 10px; }
        .main-table th { 
            background-color: #f8f8f8; /* Un gris más claro, como el modelo */
            font-weight: bold; 
            text-align: center; /* Encabezados centrados */
            border: 1px solid #ccc; 
            padding: 5px 4px;
            text-transform: capitalize;
        }
        .main-table td { 
            border: 1px solid #ccc; 
            padding: 4px; 
            vertical-align: middle;
        }

        /* Alineaciones y Formatos */
        .text-center { text-align: center; }
        .text-right { text-align: right; }
        .currency { font-family: 'Courier New', monospace; white-space: nowrap; } /* Evita que se parta la cifra */
        
        /* Sección de Totales (Flotante a la derecha) */
        .totals-container { width: 100%; overflow: hidden; margin-top: 15px; }
        .totals-table { float: right; width: auto; min-width: 35%; border-collapse: collapse; font-size: 11px; }
        .totals-table td { padding: 4px 5px; }
        .totals-table .label { font-weight: bold; text-align: left; }
        .totals-table .value { text-align: right; font-family: 'Courier New', monospace; white-space: nowrap; }
        
        /* Líneas de totales */
        .border-top { border-top: 1px solid #000; }
        .border-bottom { border-bottom: 1px solid #000; }
        
        .negative { color: #dc3545; }
    </style>


</head>
<body>
    <div class="container">
        
        <div class="header">
            <h1>NIT: {{ empresa.nit }}</h1>
            <h2>{{ empresa.razon_social }}</h2>
            <div class="report-title">Análisis de Rentabilidad de Factura</div>
        </div>

        <table class="info-table">
            <tr>
                <td class="label">Documento:</td>
                <td>
                    {% if data.documento_ref.startswith('FV') %}
                        Factura de Venta N° {{ data.documento_ref.split('-')[1] }}
                    {% else %}
                        {{ data.documento_ref }}
                    {% endif %}
                </td>
                <td class="label" style="padding-left: 40px;">Cliente:</td>
                <td>{{ data.tercero_nombre }}</td>
            </tr>
            <tr>
                <td class="label">Fecha Emisión:</td>
                <td>{{ data.fecha|date("%Y-%m-%d") }}</td>
                
                <td class="label" style="padding-left: 40px;">NIT Cliente:</td>
                <td>{{ data.tercero_nit if data.tercero_nit else 'N/A' }}</td>
            </tr>
        </table>

        <table class="main-table">
            <thead>
                <tr>
                    <th style="width: 25%;">Producto</th>
                    <th class="text-center" style="width: 8%;">Cant.</th>
                    <th class="text-right" style="width: 12%;">V/r Unitario</th>
                    <th class="text-right" style="width: 12%;">Total Venta</th>
                    <th class="text-right" style="width: 12%;">Costo Unit.</th>
                    <th class="text-right" style="width: 12%;">Costo Total</th>
                    <th class="text-right" style="width: 12%;">Util. Bruta</th>
                    <th class="text-right" style="width: 7%;">% Margen</th>
                </tr>
            </thead>
            <tbody>
                {% for item in data.detalle %}
                <tr>
                    <td>{{ item.producto_nombre }}</td>
                    <td class="text-center">{{ item.cantidad|format_decimal(2) }}</td>
                    
                    <td class="text-right currency">{{ item.valor_venta_unitario|format_currency(0) }}</td>
                    <td class="text-right currency">{{ item.valor_venta_total|format_currency(0) }}</td>
                    <td class="text-right currency">{{ item.costo_unitario|format_currency(0) }}</td>
                    <td class="text-right currency">{{ item.costo_total|format_currency(0) }}</td>
                    
                    <td class="text-right currency {% if item.utilidad_bruta_valor < 0 %}negative{% endif %}">
                        {{ item.utilidad_bruta_valor|format_currency(0) }}
                    </td>
                    <td class="text-right {% if item.utilidad_bruta_porcentaje < 0 %}negative{% endif %}">
                        {{ item.utilidad_bruta_porcentaje|format_decimal(2) }}%
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <div class="totals-container">
            <table class="totals-table">
                <tr>
                    <td class="label">Total Venta:</td>
                    <td class="value">{{ data.totales.total_venta|format_currency(0) }}</td>
                </tr>
                <tr>
                    <td class="label">Total Costo:</td>
                    <td class="value border-bottom">{{ data.totales.total_costo|format_currency(0) }}</td>
                </tr>
                <tr>
                    <td class="label border-top" style="padding-top: 10px;">Utilidad Bruta:</td>
                    <td class="value border-top" style="padding-top: 10px;">{{ data.totales.total_utilidad_bruta_valor|format_currency(0) }}</td>
                </tr>
                <tr>
                    <td class="label">Margen de la Factura:</td>
                    <td class="value">{{ data.totales.total_utilidad_bruta_porcentaje|format_decimal(2) }}%</td>
                </tr>
            </table>
        </div>

    </div>
</body>
</html>
''',



    'reports/rentabilidad_factura_report.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Análisis de Rentabilidad de Factura</title>
    <style>
        body { font-family: sans-serif; font-size: 10px; }
        .container { width: 100%; margin: 0 auto; }
        .header, .footer { text-align: center; }
        .header h1 { margin: 0; font-size: 16px; }
        .header p { margin: 2px 0; }
        .info-table { width: 100%; margin-top: 15px; margin-bottom: 15px; border-collapse: collapse; }
        .info-table td { padding: 3px; }
        .main-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        .main-table th, .main-table td { border: 1px solid #ddd; padding: 4px; text-align: left; }
        .main-table th { background-color: #f2f2f2; font-size: 9px; }
        .main-table td { font-size: 9px; }
        .text-right { text-align: right; }
        .totals-section { width: 40%; margin-left: 60%; margin-top: 15px; }
        .totals-table { width: 100%; border-collapse: collapse; }
        .totals-table td { padding: 4px; }
        .label { font-weight: bold; }
        .currency::before { content: "$ "; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ empresa.nombre }}</h1>
            <p>NIT: {{ empresa.nit }}</p>
            <h2>Análisis de Rentabilidad de Factura</h2>
        </div>

        <table class="info-table">
            <tr>
                <td width="15%"><strong class="label">Documento:</strong></td>
                <td width="35%">{{ doc.tipo_documento.nombre }} N° {{ doc.numero }}</td>
                <td width="15%"><strong class="label">Cliente:</strong></td>
                <td width="35%">{{ doc.beneficiario.razon_social }}</td>
            </tr>
            <tr>
                <td><strong class="label">Fecha Emisión:</strong></td>
                <td>{{ doc.fecha.strftime('%Y-%m-%d') }}</td>
                <td><strong class="label">NIT Cliente:</strong></td>
                <td>{{ doc.beneficiario.nit }}</td>
            </tr>
        </table>

        <table class="main-table">
            <thead>
                <tr>
                    <th>Producto</th>
                    <th class="text-right">Cant.</th>
                    <th class="text-right">V/r Unitario</th>
                    <th class="text-right">Total Venta</th>
                    <th class="text-right">Costo Unit.</th>
                    <th class="text-right">Costo Total</th>
                    <th class="text-right">Util. Bruta</th>
                    <th class="text-right">% Margen</th>
                </tr>
            </thead>
            <tbody>
                {% for item in detalle_productos %}
                <tr>
                    <td>{{ item.nombre_producto }}</td>
                    <td class="text-right">{{ "%.2f"|format(item.cantidad) }}</td>
                    <td class="text-right currency">{{ "{:,.0f}".format(item.precio_unitario) }}</td>
                    <td class="text-right currency">{{ "{:,.0f}".format(item.total_linea) }}</td>
                    <td class="text-right currency">{{ "{:,.0f}".format(item.costo_unitario) }}</td>
                    <td class="text-right currency">{{ "{:,.0f}".format(item.costo_total) }}</td>
                    <td class="text-right currency">{{ "{:,.0f}".format(item.utilidad_bruta) }}</td>
                    <td class="text-right">{{ "%.2f"|format(item.margen_rentabilidad * 100) }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <div class="totals-section">
            <table class="totals-table">
                <tr>
                    <td class="label">Total Venta:</td>
                    <td class="text-right currency">{{ "{:,.0f}".format(totales.venta) }}</td>
                </tr>
                <tr>
                    <td class="label">Total Costo:</td>
                    <td class="text-right currency">{{ "{:,.0f}".format(totales.costo) }}</td>
                </tr>
                <tr>
                    <td class="label" style="border-top: 1px solid black; padding-top: 5px;">Utilidad Bruta:</td>
                    <td class="text-right currency" style="border-top: 1px solid black; padding-top: 5px;">{{ "{:,.0f}".format(totales.utilidad) }}</td>
                </tr>
                <tr>
                    <td class="label">Margen de la Factura:</td>
                    <td class="text-right">{{ "%.2f"|format(totales.margen * 100) }}%</td>
                </tr>
            </table>
        </div>
    </div>
</body>
</html>
''',

    'reports/rentabilidad_producto.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Reporte de Rentabilidad por Producto</title>
    <style>
        @page {
            size: letter portrait;
            margin: 1.5cm;
        }
        body {
            font-family: 'Helvetica', 'Arial', sans-serif;
            font-size: 9pt;
            color: #333;
        }
        .header {
            text-align: center;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .header h1 {
            margin: 0;
            font-size: 16pt;
        }
        .header h2 {
            margin: 0;
            font-size: 12pt;
            font-weight: normal;
        }
        .info {
            margin-bottom: 20px;
            border: 1px solid #ddd;
            padding: 10px;
            border-radius: 5px;
            background-color: #f9f9f9;
        }
        .info p {
            margin: 2px 0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            border: 1px solid #ccc;
            padding: 5px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
            font-size: 8pt;
        }
        .text-right {
            text-align: right;
        }
        .summary-table {
            width: 50%;
            margin-left: 50%;
            border-top: 2px solid #333;
        }
        .summary-table td {
            border: none;
            padding: 4px;
        }
        .summary-table .label {
            font-weight: bold;
        }
        .footer {
            position: fixed;
            bottom: -1cm;
            left: 0;
            right: 0;
            text-align: center;
            font-size: 8pt;
            color: #777;
        }
    </style>
</head>
<body>

    <div class="header">
        <h1>Reporte de Rentabilidad por Producto</h1>
        <h2>{{ empresa_nombre }}</h2>
    </div>

    <div class="info">
        <p><strong>Producto:</strong> {{ producto_info.codigo }} - {{ producto_info.nombre }}</p>
        <p><strong>Período Analizado:</strong> {{ filtros.fecha_inicio }} al {{ filtros.fecha_fin }}</p>
        <p><strong>Fecha de Generación:</strong> {{ fecha_generacion }}</p>
    </div>

    <table>
        <thead>
            <tr>
                <th>Fecha</th>
                <th>Documento</th>
                <th class="text-right">Cant.</th>
                <th class="text-right">Venta Unit.</th>
                <th class="text-right">Venta Total</th>
                <th class="text-right">Costo Unit.</th>
                <th class="text-right">Costo Total</th>
                <th class="text-right">Utilidad Bruta</th>
                <th class="text-right">% Margen</th>
            </tr>
        </thead>
        <tbody>
            {% for item in data.items %}
            <tr>
                <td>{{ item.fecha }}</td>
                <td>{{ item.documento_ref }}</td>
                <td class="text-right">{{ "%.2f"|format(item.cantidad) }}</td>
                <td class="text-right">{{ "${:,.0f}".format(item.venta_unitaria|float) }}</td>
                <td class="text-right">{{ "${:,.0f}".format(item.venta_total|float) }}</td>
                <td class="text-right">{{ "${:,.0f}".format(item.costo_unitario_promedio|float) }}</td>
                <td class="text-right">{{ "${:,.0f}".format(item.costo_total|float) }}</td>
                <td class="text-right">{{ "${:,.0f}".format(item.utilidad_bruta|float) }}</td>
                <td class="text-right">{{ "%.2f"|format(item.margen_rentabilidad * 100) }}%</td>
            </tr>
            {% else %}
            <tr>
                <td colspan="9" style="text-align:center;">No se encontraron ventas para este producto en el período seleccionado.</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <table class="summary-table">
        <tr>
            <td class="label">Venta Total:</td>
            <td class="text-right">{{ "${:,.0f}".format(data.total_venta|float) }}</td>
        </tr>
        <tr>
            <td class="label">Costo Total:</td>
            <td class="text-right">{{ "${:,.0f}".format(data.total_costo|float) }}</td>
        </tr>
        <tr>
            <td class="label">Utilidad Bruta Total:</td>
            <td class="text-right">{{ "${:,.0f}".format(data.total_utilidad|float) }}</td>
        </tr>
        <tr>
            <td class="label">Margen de Rentabilidad:</td>
            <td class="text-right"><strong>{{ "%.2f"|format(data.margen_total_porcentaje) }}%</strong></td>
        </tr>
    </table>

</body>
</html>
''',

    'reports/rentabilidad_producto_grupo_report.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Análisis de Rentabilidad por Producto/Grupo</title>
    <style>
        @page {
            size: letter landscape; /* Paisaje para más columnas */
            margin: 1.5cm;
        }
        body {
            font-family: 'Helvetica', 'Arial', sans-serif;
            font-size: 8pt; /* Tamaño reducido para caber más info */
            color: #333;
        }
        .header {
            text-align: center;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
            margin-bottom: 15px; /* Reducido margen */
        }
        .header h1 { margin: 0; font-size: 14pt; } /* Reducido tamaño */
        .header h2 { margin: 0; font-size: 11pt; font-weight: normal; } /* Reducido tamaño */
        .info {
            margin-bottom: 15px; /* Reducido margen */
            text-align: center;
            font-size: 9pt; /* Reducido tamaño */
        }
        .info p { margin: 1px 0; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 15px;
        }
        th, td {
            border: 1px solid #ccc;
            padding: 4px; /* Reducido padding */
            text-align: left;
            word-wrap: break-word; /* Para nombres largos */
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
            text-align: center;
        }
        .text-right { text-align: right; }
        .nowrap { white-space: nowrap; } /* Para columnas de ID/Código */
        tfoot td {
            font-weight: bold;
            background-color: #e8e8e8;
            border-top: 2px solid #333;
        }
        /* Clases para formato numérico */
        .currency { text-align: right; }
        .percentage { text-align: right; }
    </style>
</head>
<body>

    <div class="header">
        <h1>{{ empresa.razon_social if empresa else 'Empresa Desconocida' }}</h1>
        <h2>{{ titulo_reporte | default('Análisis de Rentabilidad') }}</h2>
    </div>

    <div class="info">
        <p><strong>Período Analizado:</strong> {{ filtros.fecha_inicio }} al {{ filtros.fecha_fin }}</p>
        {% if filtros.grupos_nombres %}
        <p><strong>Grupos:</strong> {{ filtros.grupos_nombres | join(', ') }}</p>
        {% elif filtros.producto_nombre %}
        <p><strong>Producto:</strong> {{ filtros.producto_nombre }}</p>
        {% else %}
        <p><strong>Filtro:</strong> Todos los productos/grupos</p>
        {% endif %}
    </div>

    <table>
        <thead>
            <tr>
                <th class="nowrap">Código</th>
                <th>Producto</th>
                <th class="currency">Venta Total</th>
                <th class="currency">Costo Total</th>
                <th class="currency">Utilidad Bruta</th>
                <th class="percentage">Margen %</th>
            </tr>
        </thead>
        <tbody>
            {# Iteramos sobre data.items que viene del RentabilidadProductoResponse #}
            {% for item in data.items %}
            <tr>
                <td class="nowrap">{{ item.producto_codigo }}</td>
                <td>{{ item.producto_nombre }}</td>
                <td class="currency">{{ "${:,.0f}".format(item.total_venta|float) }}</td>
                <td class="currency">{{ "${:,.0f}".format(item.total_costo|float) }}</td>
                <td class="currency">{{ "${:,.0f}".format(item.total_utilidad|float) }}</td>
                <td class="percentage">{{ "%.2f%%"|format(item.margen_rentabilidad_porcentaje|float) }}</td>
            </tr>
            {% else %}
            <tr>
                <td colspan="6" style="text-align:center;">No se encontraron productos con rentabilidad para los filtros seleccionados.</td>
            </tr>
            {% endfor %}
        </tbody>
        {# Mostramos los totales generales que vienen en data.totales #}
        {% if data.items and data.totales %}
        <tfoot>
            <tr>
                <td colspan="2" class="text-right"><strong>TOTALES GENERALES</strong></td>
                <td class="currency"><strong>{{ "${:,.0f}".format(data.totales.total_venta_general|float) }}</strong></td>
                <td class="currency"><strong>{{ "${:,.0f}".format(data.totales.total_costo_general|float) }}</strong></td>
                <td class="currency"><strong>{{ "${:,.0f}".format(data.totales.total_utilidad_general|float) }}</strong></td>
                <td class="percentage"><strong>{{ "%.2f%%"|format(data.totales.margen_general_porcentaje|float) }}</strong></td>
            </tr>
        </tfoot>
        {% endif %}
    </table>

</body>
</html>
''',

    'reports/reporte_facturacion_detallado.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Explorador de Transacciones</title>
    <style>
        body { font-family: 'Helvetica', sans-serif; font-size: 9px; }
        .header { text-align: center; margin-bottom: 20px; }
        .header h1 { margin: 0; }
        .header h3 { margin: 5px 0; color: #555; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #ddd; padding: 5px; text-align: left; }
        th { background-color: #f2f2f2; }
        .text-right { text-align: right; }
        .kpi-table { width: 50%; margin-bottom: 20px; }
        .kpi-table td { font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ empresa.razon_social }}</h1>
        <h3>NIT: {{ empresa.nit }}</h3>
        <h2>Explorador de Transacciones de {{ filtros.tipo_reporte.capitalize() }}</h2>
        <p>Período del {{ filtros.fecha_inicio }} al {{ filtros.fecha_fin }}</p>
    </div>

    <h4>Resumen del Período</h4>
    <table class="kpi-table">
        <tr>
            <td>{{ 'Total Facturado' if filtros.tipo_reporte == 'ventas' else 'Total Comprado' }}</td>
            <td class="text-right">$ {{ "{:,.0f}".format(data.kpis.total_valor) }}</td>
        </tr>
        {% if filtros.tipo_reporte == 'ventas' %}
        <tr>
            <td>Costo Total</td>
            <td class="text-right">$ {{ "{:,.0f}".format(data.kpis.total_costo) }}</td>
        </tr>
        <tr>
            <td>Utilidad Bruta</td>
            <td class="text-right">$ {{ "{:,.0f}".format(data.kpis.utilidad_bruta_valor_total) }}</td>
        </tr>
        <tr>
            <td>Margen Promedio</td>
            <td class="text-right">{{ "%.2f"|format(data.kpis.utilidad_bruta_porcentaje_promedio) }}%</td>
        </tr>
        {% endif %}
    </table>

    <h4>Detalle de Transacciones</h4>
    <table>
        <thead>
            <tr>
                <th>Fecha</th>
                <th>Documento</th>
                <th>Tercero</th>
                <th>Producto</th>
                <th class="text-right">Cantidad</th>
                <th class="text-right">Vr. Unitario</th>
                <th class="text-right">Vr. Total</th>
                {% if filtros.tipo_reporte == 'ventas' %}
                    <th class="text-right">Costo Total</th>
                    <th class="text-right">Utilidad</th>
                    <th class="text-right">% Margen</th>
                {% endif %}
            </tr>
        </thead>
        <tbody>
            {% for item in data.items %}
            <tr>
                <td>{{ item.fecha }}</td>
                <td>{{ item.documento_ref }}</td>
                <td>{{ item.tercero_nombre }}</td>
                <td>{{ item.producto_nombre }}</td>
                <td class="text-right">{{ "%.2f"|format(item.cantidad) }}</td>
                <td class="text-right">$ {{ "{:,.0f}".format(item.valor_unitario) }}</td>
                <td class="text-right">$ {{ "{:,.0f}".format(item.valor_total_linea) }}</td>
                {% if filtros.tipo_reporte == 'ventas' %}
                    <td class="text-right">$ {{ "{:,.0f}".format(item.costo_total_linea) }}</td>
                    <td class="text-right">$ {{ "{:,.0f}".format(item.utilidad_bruta_valor) }}</td>
                    <td class="text-right">{{ "%.2f"|format(item.utilidad_bruta_porcentaje) }}%</td>
                {% endif %}
            </tr>
            {% else %}
            <tr>
                <td colspan="{{ 10 if filtros.tipo_reporte == 'ventas' else 7 }}">No se encontraron transacciones para los filtros seleccionados.</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
''',

    'reports/reporte_gestion_ventas.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Reporte de Gestión de Ventas</title>
    <style>
        body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 10px; color: #333; }
        .header { text-align: center; margin-bottom: 20px; }
        .header h1 { margin: 0; font-size: 18px; }
        .header h2 { margin: 5px 0; font-size: 14px; color: #555; }
        .header p { margin: 5px 0; font-size: 12px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 6px; text-align: left; }
        th { background-color: #f2f2f2; font-weight: bold; }
        .text-right { text-align: right; }
        .total-row { font-weight: bold; background-color: #f9f9f9; }
        .badge { display: inline-block; padding: 3px 7px; font-size: 9px; font-weight: bold; line-height: 1; color: #fff; text-align: center; white-space: nowrap; vertical-align: baseline; border-radius: 10px; }
        .badge-success { background-color: #28a745; }
        .badge-warning { background-color: #ffc107; color: #212529; }
        .badge-danger { background-color: #dc3545; }
        .badge-secondary { background-color: #6c757d; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ data.empresa_nombre }}</h1>
        <h2>Reporte de Gestión de Ventas</h2>
        <p>Período del {{ data.filtros.fecha_inicio }} al {{ data.filtros.fecha_fin }}</p>
    </div>

    <h3>Resumen General</h3>
    <table>
        <tr>
            <th>Total Facturado</th>
            <td class="text-right">{{ "${:,.2f}".format(data.kpis.total_facturado) }}</td>
        </tr>
        <tr>
            <th>Total Cobrado</th>
            <td class="text-right">{{ "${:,.2f}".format(data.kpis.total_cobrado) }}</td>
        </tr>
        <tr>
            <th>Saldo Pendiente</th>
            <td class="text-right">{{ "${:,.2f}".format(data.kpis.saldo_pendiente) }}</td>
        </tr>
         <tr>
            <th>Cartera Vencida</th>
            <td class="text-right">{{ "${:,.2f}".format(data.kpis.cartera_vencida) }}</td>
        </tr>
    </table>

    <h3>Detalle de Facturas</h3>
    <table>
        <thead>
            <tr>
                <th>Fecha</th>
                <th>Documento</th>
                <th>Cliente</th>
                <th>Vencimiento</th>
                <th class="text-right">Total Factura</th>
                <th class="text-right">Saldo</th>
                <th>Estado</th>
            </tr>
        </thead>
        <tbody>

            {% for doc in data['items'] %}
            <tr>
                <td>{{ doc.fecha }}</td>
                <td>{{ doc.tipo_documento }}-{{ doc.numero }}</td>
                <td>{{ doc.beneficiario_nombre }}</td>
                <td>{{ doc.fecha_vencimiento }}</td>
                <td class="text-right">{{ "${:,.2f}".format(doc.total) }}</td>
                <td class="text-right">{{ "${:,.2f}".format(doc.saldo_pendiente) }}</td>
                <td>
                    {% if doc.estado == 'Pagada' %}
                        <span class="badge badge-success">Pagada</span>
                    {% elif doc.estado == 'Pendiente' %}
                        <span class="badge badge-warning">Pendiente</span>
                    {% elif doc.estado == 'Vencida' %}
                        <span class="badge badge-danger">Vencida</span>
                    {% else %}
                        <span class="badge badge-secondary">{{ doc.estado }}</span>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
''',

    'reports/super_informe_inventarios_report.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{{ titulo_reporte }}</title>
    <style>
        body { font-family: 'Helvetica', 'Arial', sans-serif; font-size: 10px; color: #333; }
        /* FORZAR ORIENTACIÓN HORIZONTAL PARA MOVIMIENTOS DETALLADOS */
        @page { size: Letter landscape; margin: 1cm; } 
        h1 { font-size: 16px; text-align: center; margin-bottom: 5px; }
        h2 { font-size: 14px; text-align: center; margin-bottom: 15px; }
        .header-info { text-align: center; font-size: 11px; margin-bottom: 20px; }
        .header-info p { margin: 2px 0; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #ccc; padding: 4px 6px; text-align: left; }
        th { background-color: #f0f0f0; font-size: 10px; text-align: center; }
        .text-right { text-align: right; }
        .font-mono { font-family: 'Courier New', Courier, monospace; }
        .total-row { background-color: #f0f0f0; font-weight: bold; }
        .total-row td { padding-top: 6px; padding-bottom: 6px; }
        .no-data { text-align: center; font-style: italic; padding: 20px; }

        /* --- Estilos Específicos para cada Vista --- */

        /* Vista Movimientos */
        .vista-movimientos th { font-size: 9px; }
        .vista-movimientos td { font-size: 9px; }

        /* Vista Estado General */
        .vista-estado th { font-size: 10px; }
        .vista-estado .header-group { text-align: center; border-bottom: 1px solid #ccc; }
        .vista-estado .subheader { text-align: right; }

        /* Vista Rentabilidad */
        .vista-rentabilidad th { font-size: 10px; }
        .vista-rentabilidad .header-group { text-align: center; }

    </style>
</head>
<body>
    <div class="header-info">
        <p style="font-size: 14px; font-weight: bold;">{{ empresa_nombre }}</p>
        <p>NIT: (pendiente)</p>
        <p>Teléfono: (pendiente)</p>
    </div>

    <h1>{{ titulo_reporte }}</h1>
   
    <h2>
        {% if filtros.fecha_inicio and filtros.fecha_fin %}
            Del {{ filtros.fecha_inicio }} al {{ filtros.fecha_fin }}
        {% elif filtros.fecha_fin %}
            Hasta el {{ filtros.fecha_fin }}
        {% else %}
            A la fecha actual
        {% endif %}
    </h2>

    
    <hr style="border: 0; border-top: 1px solid #999;">

    {% if not data.items %}
        <p class="no-data">No se encontraron resultados para los filtros seleccionados.</p>
    {% else %}
        
        {% if data.vista_reporte == 'MOVIMIENTOS' %}
        <table class="vista-movimientos">
            <thead>
                <tr>
                    <th>Fecha</th>
                    <th>Documento</th>
                    <th>Tercero</th>
                    <th>Bodega</th>
                    <th>Código</th>
                    <th>Producto</th>
                    <th>Tipo Mov.</th>
                    <th class="text-right">Cantidad</th>
                    <th class="text-right">Costo Unit.</th>
                    <th class="text-right">Costo Total</th>
                </tr>
            </thead>
            <tbody>

                {% for item in data['items'] %}
                <tr>

                    <td>{{ item.fecha | string }}</td> 
                    <td>{{ item.documento_ref or 'N/A' }}</td>
                    <td>{{ item.tercero_nombre or 'N/A' }}</td>
                    <td>{{ item.bodega_nombre }}</td>
                    <td class="font-mono">{{ item.producto_codigo }}</td>
                    <td>{{ item.producto_nombre }}</td>
                    <td>{{ item.tipo_movimiento }}</td>
                    <td class="text-right font-mono">{{ "%.2f"|format(item.cantidad) }}</td>
                    {# --- CAMBIO: Costo unitario sin filtro de miles --- #}
                    <td class="text-right font-mono">{{ "%.2f"|format(item.costo_unitario) }}</td>
                    {# --- CAMBIO: Costo total con filtro de miles --- #}
                    <td class="text-right font-mono">{{ item.costo_total | format_miles }}</td>
                </tr>
                {% endfor %}
            </tbody>
            {# --- INICIO CAMBIO: Totales para MOVIMIENTOS con filtro de miles --- #}
            {% if data.totales and data.totales.total_cantidad %}
            <tfoot class="total-row">
                <tr>
                    <td colspan="7" class="text-right"><strong>TOTALES GENERALES</strong></td> 
                    <td class="text-right font-mono">{{ "%.2f"|format(data.totales.total_cantidad) }}</td>
                    <td class="text-right"></td> 
                    {# --- CAMBIO: Aplicando format_miles al total de costo --- #}
                    <td class="text-right font-mono">{{ data.totales.total_costo | format_miles }}</td>
                </tr>
            </tfoot>
            {% endif %}
            {# --- FIN CAMBIO --- #}
            </table>
        {% endif %}


        {% if data.vista_reporte == 'ESTADO_GENERAL' %}
        <table class="vista-estado">
            <thead>
                <tr>
                    <th rowspan="2" style="vertical-align: bottom;">Producto</th>
                    <th colspan="2" class="header-group">Saldo Inicial</th>
                    <th colspan="2" class="header-group">Entradas</th>
                    <th colspan="2" class="header-group">Salidas</th>
                    <th colspan="2" class="header-group">Saldo Final</th>
                </tr>
                <tr>
                    <th class="subheader">Cant.</th>
                    <th class="subheader">Valor</th>
                    <th class="subheader">Cant.</th>
                    <th class="subheader">Valor</th>
                    <th class="subheader">Cant.</th>
                    <th class="subheader">Valor</th>
                    <th class="subheader">Cant.</th>
                    <th class="subheader">Valor</th>
                </tr>
            </thead>
            <tbody>

                {% for item in data['items'] %}
                <tr>
                    <td>({{ item.producto_codigo }}) {{ item.producto_nombre }}</td>
                    <td class="text-right font-mono">{{ "%.2f"|format(item.saldo_inicial_cantidad) }}</td>
                    {# --- CAMBIO: Valor con filtro de miles --- #}
                    <td class="text-right font-mono">{{ item.saldo_inicial_valor | format_miles }}</td>
                    <td class="text-right font-mono">{{ "%.2f"|format(item.total_entradas_cantidad) }}</td>
                    {# --- CAMBIO: Valor con filtro de miles --- #}
                    <td class="text-right font-mono">{{ item.total_entradas_valor | format_miles }}</td>
                    <td class="text-right font-mono">{{ "%.2f"|format(item.total_salidas_cantidad) }}</td>
                    {# --- CAMBIO: Valor con filtro de miles --- #}
                    <td class="text-right font-mono">{{ item.total_salidas_valor | format_miles }}</td>
                    <td class="text-right font-mono">{{ "%.2f"|format(item.saldo_final_cantidad) }}</td>
                    {# --- CAMBIO: Valor con filtro de miles --- #}
                    <td class="text-right font-mono">{{ item.saldo_final_valor | format_miles }}</td>
                </tr>
                {% endfor %}
            </tbody>
            {% if data.totales %}
            <tfoot class="total-row">
                <tr>
                    <td>TOTALES GENERALES</td>
                    <td class="text-right font-mono">{{ "%.2f"|format(data.totales.saldo_inicial_cantidad) }}</td>
                    {# --- CAMBIO: Aplicando format_miles al total de saldo inicial valor --- #}
                    <td class="text-right font-mono">{{ data.totales.saldo_inicial_valor | format_miles }}</td>
                    <td class="text-right font-mono">{{ "%.2f"|format(data.totales.total_entradas_cantidad) }}</td>
                    {# --- CAMBIO: Aplicando format_miles al total de entradas valor --- #}
                    <td class="text-right font-mono">{{ data.totales.total_entradas_valor | format_miles }}</td>
                    <td class="text-right font-mono">{{ "%.2f"|format(data.totales.total_salidas_cantidad) }}</td>
                    {# --- CAMBIO: Aplicando format_miles al total de salidas valor --- #}
                    <td class="text-right font-mono">{{ data.totales.total_salidas_valor | format_miles }}</td>
                    <td class="text-right font-mono">{{ "%.2f"|format(data.totales.saldo_final_cantidad) }}</td>
                    {# --- CAMBIO: Aplicando format_miles al total de saldo final valor --- #}
                    <td class="text-right font-mono">{{ data.totales.saldo_final_valor | format_miles }}</td>
                </tr>
            </tfoot>
            {% endif %}
        </table>
        {% endif %}


        {% if data.vista_reporte == 'RENTABILIDAD' %}
        <table class="vista-rentabilidad">
            <thead>
                <tr>
                    <th>Producto</th>
                    <th class="header-group text-right">Venta Total</th>
                    <th class="header-group text-right">Costo Total</th>
                    <th class="header-group text-right">Utilidad Bruta</th>
                    <th class="header-group text-right">Margen %</th>
                </tr>
            </thead>
            <tbody>
                {% for item in data['items'] %}
                <tr>
                    <td>({{ item.producto_codigo }}) {{ item.producto_nombre }}</td>
                    {# --- CAMBIO: Valores de Venta, Costo, Utilidad con filtro de miles --- #}
                    <td class="text-right font-mono">{{ item.total_venta | format_miles }}</td>
                    <td class="text-right font-mono">{{ item.total_costo | format_miles }}</td>
                    <td class="text-right font-mono">{{ item.total_utilidad | format_miles }}</td>
                    <td class="text-right font-mono">{{ "%.2f"|format(item.margen_rentabilidad_porcentaje) }} %</td>
                </tr>
                {% endfor %}
            </tbody>
            {% if data.totales %}
            <tfoot class="total-row">
                <tr>
                    <td>TOTALES GENERALES</td>
                    {# --- CAMBIO: Totales de Rentabilidad con filtro de miles --- #}
                    <td class="text-right font-mono">{{ data.totales.total_venta_general | format_miles }}</td>
                    <td class="text-right font-mono">{{ data.totales.total_costo_general | format_miles }}</td>
                    <td class="text-right font-mono">{{ data.totales.total_utilidad_general | format_miles }}</td>
                    <td class="text-right font-mono">{{ "%.2f"|format(data.totales.margen_general_porcentaje) }} %</td>
                </tr>
            </tfoot>
            {% endif %}
        </table>
        {% endif %}
    {% endif %}
</body>
</html>
''',

    'reports/super_informe_report.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <title>Super Informe</title>
    <meta charset="UTF-8">
    <style>
        @page { 
            size: letter landscape; 
            margin: 1.5cm; 
        }
        body { 
            font-family: Arial, sans-serif; 
            font-size: 8px;
            color: #333;
        }
        .header {
            text-align: center;
            border-bottom: 1px solid #ccc;
            padding-bottom: 10px;
            margin-bottom: 15px;
        }
        h1, h2 { 
            margin: 0;
        }
        h1 { font-size: 14px; }
        h2 { font-size: 12px; font-weight: normal; }
        .report-info {
            margin-bottom: 15px;
            font-size: 9px;
        }
        table { 
            width: 100%; 
            border-collapse: collapse; 
        }
        th, td { 
            border: 1px solid #ddd; 
            padding: 4px; 
            text-align: left; 
            word-wrap: break-word;
        }
        th { 
            background-color: #f2f2f2; 
            text-align: center;
            font-weight: bold;
        }
        .text-right { text-align: right; }
        .text-center { text-align: center; }

        /* Estilos para filas basados en el estado pre-procesado */
        .ANULADO { background-color: #fffbe6; }
        .ELIMINADO { background-color: #ffebee; } /* Se eliminó el tachado */

        tfoot td {
            font-weight: bold;
            background-color: #f2f2f2;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ empresa.razon_social or 'Nombre de Empresa no Disponible' }}</h1>
        <h2>NIT: {{ empresa.nit or 'N/A' }}</h2>
    </div>

    <div class="report-info">

        <h2>{{ report_title }}</h2>
        <p>Generado el: {{ fecha_generacion }}</p>
    </div>

    <table>
        <thead>
            <tr>
                {% for header in headers %}
                    <th>{{ header }}</th>
                {% endfor %}
            </tr>
        </thead>
        <tbody>
            {% for row_data in processed_rows %}
                <tr class="{{ row_data.estado }}">

                    {% for cell in row_data.cells %}
                    
                        <td>{{ cell|default('', true) }}</td>
                    {% endfor %}
                </tr>
            {% else %}
                <tr>
                    <td colspan="{{ headers|length }}">No se encontraron resultados que coincidan con los criterios de búsqueda.</td>
                </tr>
            {% endfor %}
        </tbody>

       {% if show_totals %}
<tfoot>
    <tr>
        <td colspan="{{ headers|length - 2 }}" class="text-right"><strong>TOTALES:</strong></td>
        <td class="text-right"><strong>{{ totales.debito }}</strong></td>
        <td class="text-right"><strong>{{ totales.credito }}</strong></td>
    </tr>
    <tr>
        <td colspan="{{ headers|length - 2 }}" class="text-right"><strong>DIFERENCIA:</strong></td>
        <td colspan="2" class="text-center"><strong>{{ totales.diferencia }}</strong></td>
    </tr>
</tfoot>
{% endif %}

    </table>
</body>
</html>
''',

    'reports/tercero_account_ledger_report.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Auxiliar por Tercero y Cuenta</title>
    <style>
        @page { 
            size: letter landscape; 
            margin: 1.5cm; 
        }
        body { 
            font-family: Arial, sans-serif; 
            font-size: 8px;
            color: #333;
        }
        .header {
            text-align: center;
            border-bottom: 1px solid #ccc;
            padding-bottom: 10px;
            margin-bottom: 15px;
        }
        h1, h2 { 
            margin: 0;
        }
        h1 { font-size: 14px; }
        h2 { font-size: 12px; font-weight: normal; }
        .report-info {
            margin-bottom: 15px;
            font-size: 9px;
        }
        table { 
            width: 100%; 
            border-collapse: collapse; 
        }
        th, td { 
            border: 1px solid #ddd; 
            padding: 4px; 
            text-align: left; 
            word-wrap: break-word;
        }
        th { 
            background-color: #f2f2f2; 
            text-align: center;
            font-weight: bold;
        }
        .text-right { text-align: right; }
        .text-center { text-align: center; }
        .total-global-row td {
            font-weight: bold;
            background-color: #e0e0e0;
            border-top: 2px solid #333;
        }
        .cuenta-header-row td {
            font-weight: bold;
            background-color: #f2f2f2;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ empresa_nombre }}</h1>
        <h2>NIT: {{ empresa_nit }}</h2>
    </div>

    <div class="report-info">
        <h2>Auxiliar por Tercero y Cuenta</h2>
        <p>
            <strong>Tercero:</strong> {{ tercero_info.nit }} - {{ tercero_info.razon_social }}<br>
            <strong>Periodo:</strong> Del {{ fecha_inicio }} al {{ fecha_fin }}
        </p>
    </div>

    <table>
        <thead>
            <tr>
                <th>Fecha</th>
                <th>Documento</th>
                <th>Concepto</th>
                {% if has_cost_centers %}
                <th>C. Costo</th>
                {% endif %}
                <th class="text-right">Débito</th>
                <th class="text-right">Crédito</th>
                <th class="text-right">Saldo Parcial</th>
            </tr>
        </thead>
        <tbody>
            <tr class="total-global-row">
                <td colspan="{{ 6 if has_cost_centers else 5 }}"><strong>SALDO ANTERIOR GLOBAL</strong></td>
                <td class="text-right"><strong>{{ "{:,.2f}".format(saldo_anterior_global) }}</strong></td>
            </tr>

            {% for cuenta_id, grupo_movimientos in movimientos | groupby('cuenta_id') %}
                {% set movimientos_lista = list(grupo_movimientos) %}
                {% set primer_mov = movimientos_lista[0] %}
                <tr class="cuenta-header-row">
                    <td colspan="{{ 7 if has_cost_centers else 6 }}">
                        <strong>Cuenta: {{ primer_mov.cuenta_codigo }} - {{ primer_mov.cuenta_nombre }}</strong>
                    </td>
                </tr>
                <tr style="background-color: #fafafa;">
                    <td colspan="{{ 6 if has_cost_centers else 5 }}"><i>Saldo Anterior de la Cuenta</i></td>
                    <td class="text-right">
                        <i>{{ "{:,.2f}".format(saldos_iniciales_por_cuenta.get(cuenta_id | string, 0)) }}</i>
                    </td>
                </tr>

                {% for mov in movimientos_lista %}
                <tr>
                    <td>{{ mov.fecha.strftime('%Y-%m-%d') if mov.fecha else '' }}</td>
                    <td>{{ mov.tipo_documento }}-{{ mov.numero_documento }}</td>
                    <td>{{ mov.concepto }}</td>
                    {% if has_cost_centers %}
                    <td>{{ mov.centro_costo_codigo or '' }}</td>
                    {% endif %}
                    <td class="text-right">{{ "{:,.2f}".format(mov.debito) }}</td>
                    <td class="text-right">{{ "{:,.2f}".format(mov.credito) }}</td>
                    <td class="text-right">{{ "{:,.2f}".format(mov.saldo_parcial) }}</td>
                </tr>
                {% endfor %}
            {% endfor %}

            <tr class="total-global-row">
                <td colspan="{{ 6 if has_cost_centers else 5 }}"><strong>SALDO FINAL GLOBAL</strong></td>
                {% set saldo_final_global = (movimientos[-1].saldo_parcial if movimientos else saldo_anterior_global) %}
                <td class="text-right"><strong>{{ "{:,.2f}".format(saldo_final_global) }}</strong></td>
            </tr>
        </tbody>
    </table>
</body>
</html>
''',

    'reports/topes_inventario_report.html': r'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ titulo_reporte }}</title>
    <style>
        /* Estilos esenciales para WeasyPrint (Generador de PDF) */
        body { font-family: 'Arial', sans-serif; font-size: 10pt; margin: 0.75in; }
        h1 { font-size: 16pt; color: #007bff; border-bottom: 2px solid #ddd; padding-bottom: 5px; margin-bottom: 15px; text-align: center; }
        h2 { font-size: 12pt; margin-top: 15px; color: #333; }
        .header-info { font-size: 9pt; margin-bottom: 20px; background-color: #f9f9f9; padding: 10px; border-radius: 5px; }
        .header-info span { font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #e0e0e0; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; font-weight: bold; text-transform: uppercase; font-size: 9pt; }
        td { font-size: 9pt; }
        .text-right { text-align: right; }
        .text-center { text-align: center; }
        /* Clases para colores de alerta */
        .minimo-alerta { color: #FFA500; font-weight: bold; } /* Naranja/Advertencia */
        .maximo-alerta { color: #DC3545; font-weight: bold; } /* Rojo/Error */
    </style>
</head>
<body>
    <h1>{{ empresa_nombre }}</h1>
    <h2>{{ titulo_reporte }}</h2>
    
    <div class="header-info">
        <span>Fecha de Corte:</span> {{ filtros.fecha_corte }} <br>
        <span>Alerta Activa:</span> {{ filtros.tipo_alerta }} <br>
        <span>Bodegas Consolidadas:</span> {{ bodegas_seleccionadas }} <br>
        <span>Grupos Consolidados:</span> {{ grupos_seleccionados }} <br>
    </div>

    <table>
        <thead>
            <tr>
                <th style="width: 10%;">Cód.</th>
                <th style="width: 30%;">Producto</th>
                <th style="width: 15%;" class="text-right">Saldo Actual</th>
                <th style="width: 10%;" class="text-right">Stock Mín.</th>
                <th style="width: 10%;" class="text-right">Stock Máx.</th>
                <th style="width: 15%;" class="text-right">Diferencia</th>
                <th style="width: 10%;" class="text-center">Decisión</th>
            </tr>
        </thead>
        <tbody>
            {% for item in data %}
            {% set estado_class = '' %}
            {% if item.estado_tope == 'MINIMO' %}
                {% set estado_class = 'minimo-alerta' %}
            {% elif item.estado_tope == 'MAXIMO' %}
                {% set estado_class = 'maximo-alerta' %}
            {% endif %}
            
            <tr>
                <td>{{ item.producto_codigo }}</td>
                <td>{{ item.producto_nombre }} ({{ item.bodega_nombre }})</td>
                <td class="text-right">{{ "%.2f"|format(item.saldo_actual) }}</td>
                <td class="text-right">{{ "%.2f"|format(item.stock_minimo) }}</td>
                <td class="text-right">{{ "%.2f"|format(item.stock_maximo) }}</td>
                
                <td class="text-right {{ estado_class }}">{{ "%.2f"|format(item.diferencia) }}</td>
                <td class="text-center {{ estado_class }}">
                    {% if item.estado_tope == 'MINIMO' %}
                        PEDIDO
                    {% elif item.estado_tope == 'MAXIMO' %}
                        SOBRE-STOCK
                    {% else %}
                        OK
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <h2>Total Artículos en Alerta: {{ data | length }}</h2>

</body>
</html>
''',

    'reports/detalle_facturacion_report.html': r'''
<!DOCTYPE html>
<html>
<head>
    <title>Detalle de Facturación PH</title>
    <style>
        @page { size: letter portrait; margin: 1.5cm; }
        body { font-family: Arial, sans-serif; font-size: 10px; }
        h1, h2, h3 { text-align: center; color: #333; margin: 0; }
        h1 { font-size: 1.4em; margin-bottom: 5px; }
        h2 { font-size: 1.1em; font-weight: normal; margin-bottom: 10px; }
        .company-info { text-align: center; margin-bottom: 20px; }
        .report-info { margin-bottom: 15px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #ddd; padding: 6px; text-align: left; }
        th { background-color: #4CAF50; color: white; text-align: center; font-weight: bold; }
        .text-right { text-align: right; }
        .text-center { text-align: center; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .estado-activo { color: green; font-weight: bold; }
        .estado-anulado { color: red; font-weight: bold; }
    </style>
</head>
<body>
    <div class="company-info">
        <h1>{{ empresa.razon_social }}</h1>
        <h2>NIT: {{ empresa.nit }}</h2>
    </div>
    
    <div class="report-info">
        <h3>Detalle de Facturación - Propiedad Horizontal</h3>
        <p style="text-align: center; margin-top: 5px;"><strong>Periodo:</strong> {{ periodo }}</p>
    </div>

    <table>
        <thead>
            <tr>
                <th style="width: 10%;">Factura</th>
                <th style="width: 15%;">Fecha</th>
                <th style="width: 30%;">Tercero / Propietario</th>
                <th style="width: 15%;">Unidad</th>
                <th style="width: 15%;">Total</th>
                <th style="width: 15%;">Estado</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr>
                <td class="text-center">{{ item.consecutivo }}</td>
                <td class="text-center">{{ item.fecha }}</td>
                <td>{{ item.tercero_nombre }}</td>
                <td class="text-center">{{ item.unidad }}</td>
                <td class="text-right">{{ "{:,.0f}".format(item.total).replace(",", ".") }}</td>
                <td class="text-center">
                    <span class="{{ 'estado-activo' if item.estado == 'ACTIVO' else 'estado-anulado' }}">
                        {{ item.estado }}
                    </span>
                </td>
            </tr>
            {% endfor %}
        </tbody>
        <tfoot>
            <tr>
                <td colspan="4" class="text-right"><strong>TOTAL FACTURADO:</strong></td>
                <td class="text-right"><strong>{{ "{:,.0f}".format(total_general).replace(",", ".") }}</strong></td>
                <td></td>
            </tr>
        </tfoot>
    </table>
</body>
</html>
''',
}


