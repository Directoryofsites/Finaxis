# -*- coding: utf-8 -*-
# ¡¡¡ ARCHIVO AUTO-GENERADO !!!
# No editar este archivo manualmente. Ejecutar precompile_templates.py para actualizar.

TEMPLATES_EMPAQUETADOS = {
    'reports/account_ledger_report.html': r'''
﻿<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-g">
    <title>Auxiliar por Cuenta</title>
    <style>
        body {
            font-family: sans-serif;
            font-size: 10px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th,
        td {
            border: 1px solid #ccc;
            padding: 4px;
            text-align: left;
        }

        th {
            background-color: #f2f2f2;
        }

        .header {
            text-align: center;
            margin-bottom: 20px;
        }

        .header h1 {
            margin: 0;
        }

        .header h2 {
            margin: 0;
            font-weight: normal;
        }

        .report-info {
            margin-bottom: 15px;
        }

        .text-right {
            text-align: right;
        }

        .total-row td {
            font-weight: bold;
            background-color: #f8f8f8;
        }
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
            <tr class="total-row" style="background-color: #f1f5f9;">
                <td colspan="{{ 5 if has_cost_centers else 4 }}"><strong>TOTALES MOVIMIENTOS DEL PERIODO</strong></td>
                <td class="text-right"><strong>{{ "{:,.2f}".format(total_debito_periodo) }}</strong></td>
                <td class="text-right"><strong>{{ "{:,.2f}".format(total_credito_periodo) }}</strong></td>
                <td></td>
            </tr>
            <tr class="total-row" style="background-color: #1e293b; color: white;">
                <td colspan="{{ 5 if has_cost_centers else 4 }}"><strong>SALDO FINAL ACUMULADO AL {{ fecha_fin
                        }}</strong></td>
                {% set saldo_final = movimientos[-1].saldo_parcial if movimientos else saldo_anterior %}
                <td colspan="3" class="text-right"><strong>{{ "{:,.2f}".format(saldo_final) }}</strong></td>
            </tr>
        </tbody>
    </table>
</body>

</html>

''',

    'reports/analisis_cuenta_doc_report.html': r'''
﻿<!DOCTYPE html>
<html lang="es">

<head>
    <title>Análisis de Cuenta por Documento</title>
    <meta charset="UTF-8">
    <style>
        @page {
            size: letter;
            margin: 1.5cm;
        }

        body {
            font-family: Arial, sans-serif;
            font-size: 10px;
            color: #333;
        }

        .header {
            text-align: center;
            margin-bottom: 20px;
        }

        h1 {
            font-size: 16px;
            margin: 0;
        }

        h2 {
            font-size: 12px;
            font-weight: normal;
            margin: 2px 0;
        }

        .account-block {
            margin-bottom: 25px;
            page-break-inside: avoid;
        }

        .account-header {
            background-color: #f0f0f0;
            padding: 5px;
            font-weight: bold;
            border: 1px solid #ccc;
            display: flex;
            justify-content: space-between;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 5px;
        }

        th,
        td {
            border: 1px solid #ddd;
            padding: 4px;
            text-align: right;
        }

        th {
            background-color: #fafafa;
            text-align: center;
            font-weight: bold;
        }

        .text-left {
            text-align: left;
        }

        .text-center {
            text-align: center;
        }

        .account-footer {
            background-color: #f9f9f9;
            padding: 5px;
            border: 1px solid #ccc;
            border-top: none;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
        }

        .grand-total {
            margin-top: 30px;
            border-top: 2px solid #333;
            padding-top: 10px;
            font-size: 11px;
        }
    </style>
</head>

<body>
    <div class="header">
        <h1>{{ empresa_nombre }}</h1>
        <h2>NIT: {{ empresa_nit }}</h2>
        <h2>ANÁLISIS DE CUENTA POR DOCUMENTO</h2>
        <p>Periodo: {{ fecha_inicio }} - {{ fecha_fin }}</p>
    </div>

    {% for cuenta in reporte.cuentas %}
    <div class="account-block">
        <div class="account-header">
            <span>{{ cuenta.cuenta_codigo }} - {{ cuenta.cuenta_nombre }}</span>
            <span>Saldo Inicial: ${{ "{:,.0f}".format(cuenta.saldo_inicial) }}</span>
        </div>

        <table>
            <thead>
                <tr>
                    <th class="text-left" style="width: 15%">Cód. Tipo</th>
                    <th class="text-left" style="width: 45%">Tipo de Documento</th>
                    <th style="width: 20%">Débitos</th>
                    <th style="width: 20%">Créditos</th>
                </tr>
            </thead>
            <tbody>
                {% for mov in cuenta.movimientos_por_tipo %}
                <tr>
                    <td class="text-left">{{ mov.tipo_codigo }}</td>
                    <td class="text-left">{{ mov.tipo_nombre }}</td>
                    <td>${{ "{:,.0f}".format(mov.debito) }}</td>
                    <td>${{ "{:,.0f}".format(mov.credito) }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <div class="account-footer">
            <span>Totales Cuenta:</span>
            <span>Nuevo Saldo: ${{ "{:,.0f}".format(cuenta.nuevo_saldo) }}</span>
        </div>
    </div>
    {% endfor %}

    <div class="grand-total">
        <table>
            <tr>
                <td class="text-left"><strong>TOTALES GENERALES</strong></td>
                <td><strong>Débitos: ${{ "{:,.0f}".format(reporte.totales_generales.debito) }}</strong></td>
                <td><strong>Créditos: ${{ "{:,.0f}".format(reporte.totales_generales.credito) }}</strong></td>
            </tr>
        </table>
    </div>
</body>

</html>

''',

    'reports/auxiliar_cartera_report.html': r'''
﻿<!DOCTYPE html>
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
                                <span>Abonado por {{ app.afectado_por }} por valor de {{ '{:,.2f}'.format(app.valor) }}</span><br>
                            {% elif app.afecta_a %}
                                <span>Abona a {{ app.afecta_a }} por valor de {{ '{:,.2f}'.format(app.valor) }}</span><br>
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
﻿<!DOCTYPE html>
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
﻿<!DOCTYPE html>
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
                    <span>Abonado por {{ abono.documento }} por valor de {{ '{:,.2f}'.format(abono.valor) }}</span><br>
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
﻿<!DOCTYPE html>
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
                    <span>Abona a {{ f.documento }} por valor de {{ '{:,.2f}'.format(f.valor) }}</span><br>
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
﻿<!DOCTYPE html>
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
                    <span>Pagado por {{ abono.documento }} por valor de {{ '{:,.2f}'.format(abono.valor) }}</span><br>
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
﻿<!DOCTYPE html>
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
                    <span>Paga a {{ f.documento }} por valor de {{ '{:,.2f}'.format(f.valor) }}</span><br>
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
﻿<!DOCTYPE html>
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
                                <span>Pagado por {{ app.afectado_por }} por valor de {{ '{:,.2f}'.format(app.valor) }}</span><br>
                            {% elif app.afecta_a %}
                                <span>Paga a {{ app.afecta_a }} por valor de {{ '{:,.2f}'.format(app.valor) }}</span><br>
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
﻿<!DOCTYPE html>
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
﻿<!DOCTYPE html>
<html>
<head>
    <title>Balance de Prueba</title>
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=DM+Sans:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --green-inst: #2D6A26;
            --green-light: #6BAD5E;
            --blue-slate: #4A6FA5;
            --gold-soft: #C9A84C;
            --white: #FFFFFF;
            --bg-page: #FAFAF7;
            --text-main: #1A1A1A;
            --text-muted: #BBBBBB;
            --text-labels: #444444;
            --bg-grand-total: #F5FAF4;
        }

        @page {
            size: A4;
            margin: 0;
        }

        body {
            margin: 0;
            padding: 0;
            background-color: var(--white);
            color: var(--text-main);
            font-family: 'DM Sans', sans-serif;
            -webkit-print-color-adjust: exact;
        }

        .page-container {
            width: 210mm;
            height: 297mm;
            margin: 0 auto;
            position: relative;
            box-sizing: border-box;
            overflow: hidden;
        }

        .top-bar {
            height: 4px;
            background: linear-gradient(90deg, var(--green-inst), var(--green-light), var(--gold-soft), var(--green-light), var(--green-inst));
            width: 100%;
        }

        .bottom-bar {
            height: 3px;
            background: linear-gradient(90deg, var(--green-inst), var(--green-light), var(--gold-soft));
            width: 100%;
            position: absolute;
            bottom: 0;
        }

        header {
            padding: 40px 50px 20px 50px;
            display: table;
            width: 100%;
            box-sizing: border-box;
            border-bottom: 1px solid #F0F0F0;
        }

        .header-left { display: table-cell; vertical-align: middle; text-align: left; }
        .header-right { display: table-cell; vertical-align: middle; text-align: right; }

        .badge {
            font-size: 9px;
            font-weight: 700;
            color: var(--green-inst);
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 5px;
            display: block;
        }
        .badge::before { content: "•"; margin-right: 6px; }

        .company-name {
            font-family: 'Cormorant Garamond', serif;
            font-size: 36px;
            font-weight: 700;
            line-height: 1;
            margin: 0;
        }
        .company-name span { color: var(--green-inst); }

        .doc-title {
            font-family: 'Cormorant Garamond', serif;
            font-size: 20px;
            font-style: italic;
            color: #555;
            margin-bottom: 8px;
        }

        .date-box {
            display: inline-block;
            border: 1.5px solid var(--green-inst);
            border-radius: 4px;
            padding: 5px 12px;
        }
        .date-value { font-size: 14px; font-weight: 700; }

        main { padding: 30px 50px; }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }

        thead th {
            background: #F8F9FA;
            color: var(--text-labels);
            font-size: 9px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 10px;
            border-bottom: 2px solid #EEE;
            text-align: left;
        }

        .text-right { text-align: right !important; }

        tbody td {
            padding: 8px 10px;
            font-size: 11px;
            border-bottom: 1px solid #F0F0F0;
            color: var(--text-labels);
        }

        .acc-code { font-weight: 700; color: #999; font-size: 10px; }
        .nivel-1 { background: #F2F8F1; font-weight: 700; color: var(--green-inst); }
        .nivel-2 { font-weight: 700; }

        tfoot td {
            background: var(--bg-grand-total);
            border-top: 2px solid var(--green-inst);
            padding: 12px 10px;
            font-weight: 700;
            font-size: 13px;
            color: var(--green-inst);
        }
    </style>
</head>
<body>

    <div class="page-container">
        <div class="top-bar"></div>
        <header>
            <div class="header-left">
                <span class="badge">Informe Financiero Oficial</span>
                <h1 class="company-name">Verduras <span>La 21</span></h1>
                <div style="font-size: 10px; color: #999; margin-top: 4px; letter-spacing: 1px;">NIT {{ empresa.nit if empresa else 'N/A' }}</div>
            </div>
            <div class="header-right">
                <div class="doc-title">{{ titulo_reporte }}</div>
                <div class="date-box">
                    <div class="date-value">{{ periodo }}</div>
                </div>
            </div>
        </header>

        <main>
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
                <td class="acc-code">{{ fila.codigo }}</td>
                <td>{{ fila.nombre }}</td>
                <td class="text-right">{{ "{:,.0f}".format(fila.saldo_inicial).replace(',', '.') }}</td>
                <td class="text-right">{{ "{:,.0f}".format(fila.debito).replace(',', '.') }}</td>
                <td class="text-right">{{ "{:,.0f}".format(fila.credito).replace(',', '.') }}</td>
                <td class="text-right">{{ "{:,.0f}".format(fila.nuevo_saldo).replace(',', '.') }}</td>
            </tr>
            {% endfor %}
        </tbody>
        <tfoot>
            <tr>
                <td colspan="2">TOTALES GENERALES</td>
                <td class="text-right">{{ "{:,.0f}".format(totales.saldo_inicial).replace(',', '.') }}</td>
                <td class="text-right">{{ "{:,.0f}".format(totales.debito).replace(',', '.') }}</td>
                <td class="text-right">{{ "{:,.0f}".format(totales.credito).replace(',', '.') }}</td>
                <td class="text-right">{{ "{:,.0f}".format(totales.nuevo_saldo).replace(',', '.') }}</td>
            </tr>
        </tfoot>
    </table>
    </main>
    <div class="bottom-bar"></div>
    </div>
</body>
</html>

''',

    'reports/balance_general_cc_report.html': r'''
﻿<!DOCTYPE html>
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

    'reports/balance_general_gerencial.html': r'''
﻿<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Estado de Situación Financiera - Gerencial</title>
    <!-- WeasyPrint renders local fonts if installed, or we can use webfonts if connected -->
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=DM+Sans:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            /* Colores Primarios */
            --green-inst: #2D6A26;
            --green-light: #6BAD5E;
            --blue-slate: #4A6FA5;
            --gold-soft: #C9A84C;
            --green-text: #1A3D17;
            --blue-text: #1F3560;
            --gold-text: #6B5010;
            
            /* Fondos */
            --white: #FFFFFF;
            --bg-activos: #F2F8F1;
            --bg-pasivos: #F3F5F8;
            --bg-patrimonio: #FBF8F1;
            --row-activos: #EEF5ED;
            --row-pasivos: #EEF1F8;
            --row-patrimonio: #FAF5E9;
            --subrow-activos: #F7F9F7;
            --subrow-pasivos: #F3F6FB;
            --gray-light: #FAFAFA;
            --bg-grand-total: #F5FAF4;
            
            /* Texto */
            --text-main: #1A1A1A;
            --text-muted: #BBBBBB;
            --text-labels: #444444;
            --red-contable: #C0392B;
        }

        @page {
            size: A4;
            margin: 0;
        }

        body {
            margin: 0;
            padding: 0;
            background-color: var(--white);
            color: var(--text-main);
            font-family: 'DM Sans', sans-serif;
            -webkit-print-color-adjust: exact;
        }

        .page-container {
            width: 210mm;
            height: 297mm; /* Forced A4 height to ensure everything fits */
            margin: 0 auto;
            position: relative;
            background: var(--white);
            box-sizing: border-box;
            overflow: hidden; /* Prevent spillover */
        }

        /* Barras Decorativas */
        .top-bar {
            height: 4px; /* Reduced */
            background: linear-gradient(90deg, var(--green-inst), var(--green-light), var(--gold-soft), var(--green-light), var(--green-inst));
            width: 100%;
        }

        .bottom-bar {
            height: 3px;
            background: linear-gradient(90deg, var(--green-inst), var(--green-light), var(--gold-soft));
            width: 100%;
            position: absolute;
            bottom: 0;
        }

        /* Cabecera */
        header {
            padding: 30px 56px 20px 56px; /* Reduced padding */
            display: table;
            width: 100%;
            box-sizing: border-box;
            border-bottom: 1px solid #F0F0F0;
        }

        .header-left {
            display: table-cell;
            vertical-align: middle;
            text-align: left;
        }

        .header-right {
            display: table-cell;
            vertical-align: middle;
            text-align: right;
        }

        .badge {
            font-size: 9px; /* Reduced */
            font-weight: 700;
            color: var(--green-inst);
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 5px;
            display: block;
        }
        .badge::before {
            content: "•";
            margin-right: 6px;
            font-size: 12px;
        }

        .company-name {
            font-family: 'Cormorant Garamond', serif;
            font-size: 38px; /* Reduced */
            font-weight: 700;
            line-height: 1;
            margin: 0;
            color: var(--text-main);
        }
        .company-name span {
            color: var(--green-inst);
        }

        .company-nit {
            font-size: 10px;
            color: var(--text-muted);
            letter-spacing: 1.5px;
            margin-top: 4px;
            font-weight: 400;
        }

        .doc-title {
            font-family: 'Cormorant Garamond', serif;
            font-size: 18px;
            font-style: italic;
            color: #555555;
            margin-bottom: 10px;
        }

        .date-box {
            display: inline-block;
            border: 1.5px solid var(--green-inst);
            border-radius: 4px;
            padding: 6px 14px;
            text-align: center;
        }

        .date-label {
            font-size: 8px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: var(--green-inst);
            margin-bottom: 1px;
        }

        .date-value {
            font-size: 14px;
            font-weight: 700;
            color: var(--text-main);
        }

        /* Cuerpo */
        main {
            padding: 20px 56px; /* Reduced */
        }

        .grid-container {
            display: table;
            width: 100%;
            border-collapse: separate;
            border-spacing: 24px 0;
            margin-left: -24px;
        }

        .col {
            display: table-cell;
            width: 50%;
            vertical-align: top;
        }

        /* Tarjetas de Sección */
        .section-card {
            border: 1.5px solid #E4E4E4;
            border-radius: 8px;
            overflow: hidden;
            background: var(--white);
            margin-bottom: 15px; /* Reduced from 24px */
        }

        .card-header {
            padding: 10px 16px;
            display: flex;
            align-items: center;
            border-bottom: 1.5px solid #E4E4E4;
        }
        .card-header.activos { background: var(--bg-activos); }
        .card-header.pasivos { background: var(--bg-pasivos); }
        .card-header.patrimonio { background: var(--bg-patrimonio); }

        .header-stripe {
            width: 3px;
            height: 16px;
            border-radius: 2px;
            margin-right: 10px;
        }
        .activos .header-stripe { background: var(--green-inst); }
        .pasivos .header-stripe { background: var(--blue-slate); }
        .patrimonio .header-stripe { background: var(--gold-soft); }

        .card-title {
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: var(--text-labels);
        }

        /* Tablas */
        .report-table {
            width: 100%;
            border-collapse: collapse;
        }

        .sub-header {
            background: var(--gray-light);
            border-bottom: 1px solid #F0F0F0;
        }
        .sub-header td {
            padding: 4px 16px; /* Reduced */
            font-size: 9px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: #AAAAAA;
        }

        .row-item td {
            padding: 6px 16px; /* Reduced */
            border-bottom: 1px solid #F8F8F8;
            vertical-align: middle; /* Fix for alignment */
        }
        .acc-code { font-size: 9px; font-weight: 700; color: var(--text-muted); letter-spacing: 0.5px; width: 40px; }
        .acc-name { font-size: 12px; color: var(--text-labels); padding-right: 10px; }
        .acc-value { 
            font-size: 12px; 
            font-weight: 500; 
            text-align: right; 
            font-variant-numeric: tabular-nums; 
            white-space: nowrap; /* CRITICAL FIX: No wrapping for currency */
            min-width: 90px;
        }

        .negativo { color: var(--red-contable) !important; }

        .row-subtotal td { padding: 8px 16px; font-weight: 700; font-size: 13px; }
        .activos .row-subtotal { background: var(--subrow-activos); border-top: 1.5px solid #D8E8D6; color: var(--green-inst); }
        .pasivos .row-subtotal { background: var(--subrow-pasivos); border-top: 1.5px solid #C0CEDF; color: var(--blue-slate); }

        .row-total td { padding: 10px 16px; font-weight: 700; font-size: 13.5px; }
        .activos .row-total { background: var(--row-activos); border-top: 2px solid var(--green-inst); color: var(--green-text); }
        .pasivos .row-total { background: var(--row-pasivos); border-top: 2px solid var(--blue-slate); color: var(--blue-text); }
        .patrimonio .row-total { background: var(--row-patrimonio); border-top: 2px solid var(--gold-soft); color: var(--gold-text); }

        /* KPIs */
        .kpi-container {
            display: table;
            width: 100%;
            border-spacing: 15px 0;
            margin-top: 5px;
            margin-left: -15px;
        }

        .kpi-card {
            display: table-cell;
            width: 33.33%;
            border: 1.5px solid #E4E4E4;
            border-radius: 8px;
            padding: 15px; /* Reduced */
            position: relative;
            background: var(--white);
        }
        .kpi-card::before {
            content: "";
            position: absolute;
            left: 0;
            top: 15%;
            bottom: 15%;
            width: 4px;
            border-radius: 0 2px 2px 0;
        }
        .kpi-activos::before { background: var(--green-inst); }
        .kpi-pasivos::before { background: var(--red-contable); }
        .kpi-patrimonio::before { background: var(--gold-soft); }

        .kpi-label {
            font-size: 9px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: var(--text-muted);
            margin-bottom: 5px;
        }

        .kpi-value {
            font-size: 16px; /* Reduced */
            font-weight: 700;
            color: var(--text-main);
            font-variant-numeric: tabular-nums;
            white-space: nowrap;
        }

        /* Grand Total */
        .grand-total-bar {
            background: var(--bg-grand-total);
            border: 2px solid var(--green-inst);
            border-radius: 8px;
            padding: 15px 25px; /* Reduced */
            margin-top: 15px; /* Reduced */
            display: table;
            width: 100%;
            box-sizing: border-box;
        }

        .gt-left {
            display: table-cell;
            vertical-align: middle;
            width: 40px;
        }

        .pulse-circle {
            width: 32px;
            height: 32px;
            background: var(--green-inst);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }

        .gt-center {
            display: table-cell;
            vertical-align: middle;
            padding-left: 15px;
        }

        .gt-label {
            font-family: 'Cormorant Garamond', serif;
            font-size: 16px;
            font-style: italic;
            font-weight: 600;
            color: var(--text-main);
        }

        .gt-right {
            display: table-cell;
            vertical-align: middle;
            text-align: right;
        }

        .gt-val-prefix {
            font-size: 11px;
            color: #888888;
            margin-right: 5px;
        }

        .gt-value {
            font-size: 22px; /* Reduced */
            font-weight: 700;
            color: var(--green-text);
            white-space: nowrap;
        }

        .equation-note {
            text-align: center;
            font-size: 10px;
            color: #AAAAAA;
            font-style: italic;
            margin-top: 8px;
        }

        /* Firmas */
        .signatures {
            margin-top: 30px; /* Reduced from 60px */
            display: table;
            width: 100%;
        }

        .sig-col {
            display: table-cell;
            width: 50%;
            text-align: center;
            padding: 0 40px;
        }

        .sig-line {
            height: 1.5px;
            background: linear-gradient(90deg, transparent, var(--gold-soft), transparent);
            width: 80%;
            margin: 0 auto 10px auto;
        }

        .sig-name {
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: var(--text-main);
        }

        .sig-meta {
            font-size: 9px;
            color: var(--text-muted);
            margin-top: 4px;
        }

    </style>
</head>
<body>
    <div class="page-container">
        <div class="top-bar"></div>
        
        <header>
            <div class="header-left">
                <span class="badge">Informe Financiero Oficial</span>
                <h1 class="company-name">Verduras <span>La 21</span></h1>
                <div class="company-nit">NIT {{ empresa.nit or '942.807.497' }}</div>
            </div>
            <div class="header-right">
                <div class="doc-title">Estado de Situación Financiera</div>
                <div class="date-box">
                    <div class="date-label">Fecha de Corte</div>
                    <div class="date-value">{{ fecha_corte.strftime('%d de %B de %Y') }}</div>
                </div>
                <div style="font-size: 9px; color: #BBBBBB; margin-top: 8px; letter-spacing: 1px;">Cifras en Pesos Colombianos (COP)</div>
            </div>
        </header>

        <main>
            <div class="grid-container">
                <!-- COLUMNA ACTIVOS -->
                <div class="col">
                    <div class="section-card">
                        <div class="card-header activos">
                            <div class="header-stripe"></div>
                            <span class="card-title">Activos</span>
                        </div>
                        <table class="report-table activos">
                            {% if reporte.clasificado_activo.corriente %}
                            <tr class="sub-header">
                                <td colspan="3">▸ Activo Corriente</td>
                            </tr>
                            {% for it in reporte.clasificado_activo.corriente %}
                            <tr class="row-item">
                                <td class="acc-code">{{ it.codigo }}</td>
                                <td class="acc-name">{{ it.nombre }}</td>
                                <td class="acc-value {% if it.saldo < 0 %}negativo{% endif %}">
                                    {% if it.saldo < 0 %}$ -{% else %}$ {% endif %}{{ "{:,.0f}".format(it.saldo | abs).replace(',', '.') }}
                                </td>
                            </tr>
                            {% endfor %}
                            <tr class="row-subtotal">
                                <td colspan="2">Total Activo Corriente</td>
                                <td class="acc-value">
                                    {% if reporte.clasificado_activo.total_corriente < 0 %}$ -{% else %}$ {% endif %}{{ "{:,.0f}".format(reporte.clasificado_activo.total_corriente | abs).replace(',', '.') }}
                                </td>
                            </tr>
                            {% endif %}

                            {% if reporte.clasificado_activo.no_corriente %}
                            <tr class="sub-header">
                                <td colspan="3">▸ Activo No Corriente</td>
                            </tr>
                            {% for it in reporte.clasificado_activo.no_corriente %}
                            <tr class="row-item">
                                <td class="acc-code">{{ it.codigo }}</td>
                                <td class="acc-name">{{ it.nombre }}</td>
                                <td class="acc-value {% if it.saldo < 0 %}negativo{% endif %}">
                                    {% if it.saldo < 0 %}$ -{% else %}$ {% endif %}{{ "{:,.0f}".format(it.saldo | abs).replace(',', '.') }}
                                </td>
                            </tr>
                            {% endfor %}
                            {% endif %}

                            <tr class="row-total">
                                <td colspan="2">TOTAL ACTIVOS</td>
                                <td class="acc-value">
                                    {% if reporte.total_activos < 0 %}$ -{% else %}$ {% endif %}{{ "{:,.0f}".format(reporte.total_activos | abs).replace(',', '.') }}
                                </td>
                            </tr>
                        </table>
                    </div>
                </div>

                <!-- COLUMNA PASIVOS Y PATRIMONIO -->
                <div class="col">
                    <!-- PASIVOS -->
                    <div class="section-card">
                        <div class="card-header pasivos">
                            <div class="header-stripe"></div>
                            <span class="card-title">Pasivos</span>
                        </div>
                        <table class="report-table pasivos">
                            <tr class="sub-header">
                                <td colspan="3">▸ Pasivo Corriente</td>
                            </tr>
                            {% for it in reporte.clasificado_pasivo.corriente %}
                            <tr class="row-item">
                                <td class="acc-code">{{ it.codigo }}</td>
                                <td class="acc-name">{{ it.nombre }}</td>
                                <td class="acc-value {% if it.saldo < 0 %}negativo{% endif %}">
                                    {% if it.saldo < 0 %}$ -{% else %}$ {% endif %}{{ "{:,.0f}".format(it.saldo | abs).replace(',', '.') }}
                                </td>
                            </tr>
                            {% endfor %}
                            <tr class="row-subtotal">
                                <td colspan="2">Total Pasivo Corriente</td>
                                <td class="acc-value">
                                    {% if reporte.clasificado_pasivo.total_corriente < 0 %}$ -{% else %}$ {% endif %}{{ "{:,.0f}".format(reporte.clasificado_pasivo.total_corriente | abs).replace(',', '.') }}
                                </td>
                            </tr>
                            <tr class="row-total">
                                <td colspan="2">TOTAL PASIVOS</td>
                                <td class="acc-value">
                                    {% if reporte.total_pasivos < 0 %}$ -{% else %}$ {% endif %}{{ "{:,.0f}".format(reporte.total_pasivos | abs).replace(',', '.') }}
                                </td>
                            </tr>
                        </table>
                    </div>

                    <!-- PATRIMONIO -->
                    <div class="section-card">
                        <div class="card-header patrimonio">
                            <div class="header-stripe"></div>
                            <span class="card-title">Patrimonio</span>
                        </div>
                        <table class="report-table patrimonio">
                            {% for it in reporte.patrimonio %}
                            <tr class="row-item">
                                <td class="acc-code">{{ it.codigo }}</td>
                                <td class="acc-name">{{ it.nombre }}</td>
                                <td class="acc-value {% if it.saldo < 0 %}negativo{% endif %}">
                                    {% if it.saldo < 0 %}$ -{% else %}$ {% endif %}{{ "{:,.0f}".format(it.saldo | abs).replace(',', '.') }}
                                </td>
                            </tr>
                            {% endfor %}
                            <!-- Utilidad -->
                            <tr class="row-item">
                                <td class="acc-code">3605</td>
                                <td class="acc-name">{{ reporte.nombre_utilidad }}</td>
                                <td class="acc-value {% if reporte.utilidad_ejercicio < 0 %}negativo{% endif %}">
                                    {% if reporte.utilidad_ejercicio < 0 %}$ -{% else %}$ {% endif %}{{ "{:,.0f}".format(reporte.utilidad_ejercicio | abs).replace(',', '.') }}
                                </td>
                            </tr>
                            <tr class="row-total">
                                <td colspan="2">TOTAL PATRIMONIO</td>
                                <td class="acc-value">
                                    {% if reporte.total_patrimonio < 0 %}$ -{% else %}$ {% endif %}{{ "{:,.0f}".format(reporte.total_patrimonio | abs).replace(',', '.') }}
                                </td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>

            <!-- KPIs -->
            <div class="kpi-container">
                <div class="kpi-card kpi-activos">
                    <div class="kpi-label">Total Activos</div>
                    <div class="kpi-value">$ {{ "{:,.0f}".format(reporte.total_activos | abs).replace(',', '.') }}</div>
                </div>
                <div class="kpi-card kpi-pasivos">
                    <div class="kpi-label">Total Pasivos</div>
                    <div class="kpi-value">$ {{ "{:,.0f}".format(reporte.total_pasivos | abs).replace(',', '.') }}</div>
                </div>
                <div class="kpi-card kpi-patrimonio">
                    <div class="kpi-label">Patrimonio Neto</div>
                    <div class="kpi-value">$ {{ "{:,.0f}".format(reporte.total_patrimonio | abs).replace(',', '.') }}</div>
                </div>
            </div>

            <!-- Grand Total -->
            <div class="grand-total-bar">
                <div class="gt-left">
                    <div class="pulse-circle">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
                    </div>
                </div>
                <div class="gt-center">
                    <div class="gt-label">Verificación Contable: Total Pasivo + Patrimonio</div>
                </div>
                <div class="gt-right">
                    <span class="gt-val-prefix">COP</span>
                    <span class="gt-value">$ {{ "{:,.0f}".format(reporte.total_pasivo_patrimonio | abs).replace(',', '.') }}</span>
                </div>
            </div>

            <div class="equation-note">
                Activos = Pasivos + Patrimonio · Ecuación contable verificada
            </div>

            <!-- Signatures -->
            <div class="signatures">
                <div class="sig-col">
                    <div class="sig-line"></div>
                    <div class="sig-name">Representante Legal</div>
                    <div class="sig-meta">C.C. _______________________</div>
                </div>
                <div class="sig-col">
                    <div class="sig-line"></div>
                    <div class="sig-name">Contador Público</div>
                    <div class="sig-meta">T.P. _______________________</div>
                </div>
            </div>
        </main>

        <div class="bottom-bar"></div>
    </div>
</body>
</html>

''',

    'reports/balance_general_report.html': r'''
﻿<!DOCTYPE html>
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

    'reports/cartera_detallada_ph_report.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Relación Detallada de Cartera</title>
    <style>
        @page { size: letter portrait; margin: 1.5cm; }
        body { font-family: 'Helvetica', 'Arial', sans-serif; font-size: 10px; color: #333; line-height: 1.4; }
        .header { text-align: center; margin-bottom: 25px; border-bottom: 2px solid #2c3e50; padding-bottom: 10px; }
        .header h1 { margin: 0; font-size: 16px; color: #2c3e50; text-transform: uppercase; }
        .header h2 { margin: 2px 0; font-size: 12px; font-weight: normal; }
        
        .report-info { background: #f8f9fa; padding: 12px; margin-bottom: 20px; border: 1px solid #dee2e6; border-radius: 4px; }
        .report-info h3 { margin: 0 0 10px 0; font-size: 14px; color: #2c3e50; text-align: center; }
        
        .details-box { margin-bottom: 20px; border-left: 4px solid #0d6efd; padding-left: 15px; }
        .details-box p { margin: 4px 0; }
        .label { font-weight: bold; width: 80px; display: inline-block; color: #555; }

        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th { background-color: #2c3e50; color: white; padding: 10px 6px; text-align: left; font-size: 9px; text-transform: uppercase; }
        td { padding: 10px 6px; border-bottom: 1px solid #eee; }
        .text-right { text-align: right; }
        .text-center { text-align: center; }
        
        .badge { padding: 3px 8px; border-radius: 12px; font-size: 8px; font-weight: bold; color: white; text-transform: uppercase; }
        .bg-INTERES { background-color: #dc3545; }
        .bg-MULTA { background-color: #fd7e14; }
        .bg-CAPITAL { background-color: #0d6efd; }
        
        .total-row { background-color: #f8f9fa; font-weight: bold; font-size: 12px; color: #000; }
        .total-row td { border-top: 2px solid #2c3e50; padding: 12px 6px; }
        
        .legal-note { margin-top: 20px; padding: 10px; font-size: 9px; background: #fff3cd; border: 1px solid #ffeeba; border-radius: 4px; color: #856404; }
        .footer { margin-top: 30px; font-size: 8px; color: #777; text-align: center; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ empresa.razon_social }}</h1>
        <h2>NIT: {{ empresa.nit }}</h2>
    </div>

    <div class="report-info">
        <h3>Relación Detallada de Cartera por Conceptos</h3>
        <div class="details-box">
            <p><span class="label">Unidad:</span> <span style="font-weight: bold;">{{ unidad.codigo }}</span></p>
            <p><span class="label">Fecha:</span> {{ fecha_impresion }}</p>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th style="width: 50%;">Concepto de Cobro</th>
                <th class="text-center" style="width: 20%;">Clasificación</th>
                <th class="text-right" style="width: 30%;">Saldo Pendiente</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr>
                <td style="font-weight: 500;">{{ item.concepto }}</td>
                <td class="text-center">
                    <span class="badge bg-{{ item.tipo }}">{{ item.tipo }}</span>
                </td>
                <td class="text-right" style="font-family: monospace; font-weight: bold; font-size: 11px;">
                    ${{ "{:,.0f}".format(item.saldo) }}
                </td>
            </tr>
            {% else %}
            <tr>
                <td colspan="3" class="text-center" style="padding: 30px; color: #999;">
                    No existen deudas pendientes por conceptos para esta unidad.
                </td>
            </tr>
            {% endfor %}
            <tr class="total-row">
                <td colspan="2" class="text-right">TOTAL CARTERA PENDIENTE:</td>
                <td class="text-right">${{ "{:,.0f}".format(total) }}</td>
            </tr>
        </tbody>
    </table>

    <div class="legal-note">
        <strong>Nota de Prelación Legal:</strong> Los pagos recibidos se aplican siguiendo el orden legal establecido: 
        1. Intereses de mora, 2. Sanciones/Multas, 3. Capital (Administración y otros conceptos).
    </div>

    <div class="footer">
        Generado por Finaxis PH - Estado de cuenta consolidado basado en simulación de prelación legal.
    </div>
</body>
</html>

''',

    'reports/cartilla_inventario_admin_report.html': r'''
﻿<!DOCTYPE html>
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
                    <td>
                        {{ p.nombre }} 
                        {% if p.es_servicio %} <span style="color: blue;">(Servicio)</span> {% endif %}
                    </td>
                    <td>{{ p.grupo_nombre }}</td>
                    
                    <td class="text-right font-mono">{{ p.costo_calculado | format_miles }}</td>
                    <td class="text-right font-mono">{{ p.precio_base_manual | format_miles }}</td>
                    <td class="text-right font-mono" style="font-weight: bold;">{{ p.stock_calculado | format_miles }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    {% endif %}
</body>
</html>

''',

    'reports/comprobante_egreso_template.html': r'''
﻿<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">
    <title>Comprobante de Egreso</title>
    <style>
        @page {
            size: letter;
            margin: 2cm;
        }

        body {
            font-family: 'Helvetica', 'Arial', sans-serif;
            font-size: 10pt;
            color: #333;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #ccc;
            padding-bottom: 10px;
        }

        .header h1 {
            margin: 0;
            font-size: 18pt;
            text-transform: uppercase;
            color: #000;
        }

        .header h2 {
            margin: 5px 0 0;
            font-size: 12pt;
            font-weight: normal;
        }

        .header p {
            margin: 2px 0;
            font-size: 10pt;
            color: #666;
        }

        .doc-title {
            text-align: right;
            margin-bottom: 20px;
        }

        .doc-title h3 {
            margin: 0;
            font-size: 14pt;
            color: #444;
            text-transform: uppercase;
            background-color: #f9f9f9;
            display: inline-block;
            padding: 5px 15px;
            border: 1px solid #ddd;
        }

        .info-grid {
            display: table;
            width: 100%;
            margin-bottom: 20px;
        }

        .info-row {
            display: table-row;
        }

        .info-cell {
            display: table-cell;
            padding: 4px;
            border-bottom: 1px solid #eee;
        }

        .label {
            font-weight: bold;
            color: #555;
            width: 120px;
        }

        .items-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }

        .items-table tr {
            page-break-inside: avoid;
        }

        .items-table th {
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            padding: 8px;
            font-weight: bold;
            text-align: left;
            font-size: 9pt;
        }

        .items-table td {
            border: 1px solid #ddd;
            padding: 8px;
            font-size: 9pt;
        }

        .text-right {
            text-align: right;
        }

        .text-center {
            text-align: center;
        }

        .totals-section {
            width: 40%;
            margin-left: auto;
            margin-bottom: 30px;
        }

        .total-row {
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            border-bottom: 1px solid #eee;
        }

        .total-row.final {
            font-weight: bold;
            font-size: 11pt;
            border-bottom: 2px solid #000;
            border-top: 1px solid #000;
            margin-top: 5px;
            padding-top: 5px;
        }

        .footer {
            margin-top: 50px;
            border-top: 1px solid #ccc;
            padding-top: 10px;
            font-size: 8pt;
            color: #888;
            text-align: center;
        }

        .signatures {
            margin-top: 60px;
            display: table;
            width: 100%;
        }

        .sig-box {
            display: table-cell;
            width: 33%;
            text-align: center;
            vertical-align: bottom;
            height: 60px;
        }

        .sig-line {
            border-top: 1px solid #000;
            margin: 0 20px;
            padding-top: 5px;
            font-weight: bold;
        }
    </style>
</head>

<body>
    <div class="header">
        <h1>{{ empresa.razon_social }}</h1>
        <h2>NIT: {{ empresa.nit }}</h2>
        <p>{{ empresa.direccion }} - {{ empresa.telefono }}</p>
    </div>

    <div class="doc-title">
        <h3>{{ documento.tipo_nombre }} N° {{ documento.consecutivo }}</h3>
    </div>

    <div class="info-grid">
        <div class="info-row">
            <div class="info-cell label">Fecha:</div>
            <div class="info-cell">{{ documento.fecha_emision }}</div>
            <div class="info-cell label">Ciudad:</div>
            <div class="info-cell">Bogotá D.C.</div> <!-- Placeholder city -->
        </div>
        <div class="info-row">
            <div class="info-cell label">Pagado a:</div>
            <div class="info-cell"><strong>{{ tercero.razon_social }}</strong></div>
            <div class="info-cell label">NIT/CC:</div>
            <div class="info-cell">{{ tercero.nit }}</div>
        </div>
        <div class="info-row">
            <div class="info-cell label">Concepto:</div>
            <div class="info-cell" colspan="3">{{ documento.observaciones }}</div>
        </div>
    </div>

    <table class="items-table">
        <thead>
            <tr>
                <th style="width: 15%;">Código</th>
                <th style="width: 45%;">Descripción</th>
                <th style="width: 20%;" class="text-right">Débito</th>
                <th style="width: 20%;" class="text-right">Crédito</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr>
                <td>{{ item.producto_codigo }}</td>
                <td>{{ item.producto_nombre }}</td>
                <td class="text-right">{{ item.debito_fmt }}</td>
                <td class="text-right">{{ item.credito_fmt }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <div class="totals-section">
        <div class="total-row final">
            <span>TOTAL PAGADO</span>
            <span>{{ totales.total }}</span>
        </div>
        <div style="font-size: 9pt; font-style: italic; margin-top: 5px; text-align: right;">
            Son: {{ totales.valor_letras }}
        </div>
    </div>

    <div class="signatures">
        <div class="sig-box">
            <div class="sig-line">Elaboró</div>
        </div>
        <div class="sig-box">
            <div class="sig-line">Aprobó</div>
        </div>
        <div class="sig-box">
            <div class="sig-line">Recibí Conforme</div>
            <div style="font-size: 8pt;">C.C.</div>
        </div>
    </div>

    <div class="footer">
        Generado automáticamente por Finaxis Cloud
    </div>
</body>

</html>

''',

    'reports/detalle_facturacion_report.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Detalle de Facturación - PH</title>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #1C3A18;
            --primary-light: #2D5A27;
            --accent: #C9A84C;
            --bg-soft: #F9FAF8;
            --text-main: #2D3436;
            --text-light: #636E72;
            --white: #FFFFFF;
            --border: #E0E0E0;
        }

        @page {
            size: letter;
            margin: 0;
        }

        body {
            margin: 0;
            padding: 0;
            font-family: 'Montserrat', sans-serif;
            color: var(--text-main);
            background-color: var(--white);
            -webkit-print-color-adjust: exact;
        }

        .container {
            width: 100%;
            padding: 40px;
            box-sizing: border-box;
        }

        /* Encabezado Premium */
        header {
            border-bottom: 3px solid var(--primary);
            padding-bottom: 20px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
        }

        .company-info h1 {
            margin: 0;
            font-size: 24px;
            color: var(--primary);
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .company-info p {
            margin: 4px 0 0 0;
            font-size: 12px;
            color: var(--text-light);
            font-weight: 500;
        }

        .report-title {
            text-align: right;
        }

        .report-title h2 {
            margin: 0;
            font-size: 18px;
            color: var(--text-main);
            font-weight: 600;
        }

        .period-badge {
            background-color: var(--primary);
            color: var(--white);
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            margin-top: 8px;
            display: inline-block;
        }

        /* Resumen Ejecutivo */
        .summary-box {
            background-color: var(--bg-soft);
            border-left: 5px solid var(--accent);
            padding: 15px 20px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .summary-item label {
            display: block;
            font-size: 10px;
            text-transform: uppercase;
            color: var(--text-light);
            letter-spacing: 1px;
            margin-bottom: 4px;
        }

        .summary-item span {
            font-size: 18px;
            font-weight: 700;
            color: var(--primary);
        }

        /* Tabla de Detalle */
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            table-layout: fixed;
        }

        thead th {
            background-color: var(--primary);
            color: var(--white);
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            padding: 12px 10px;
            text-align: left;
            letter-spacing: 0.5px;
        }

        tbody tr {
            border-bottom: 1px solid var(--border);
        }

        tbody tr:nth-child(even) {
            background-color: #FAFAFA;
        }

        tbody td {
            padding: 12px 10px;
            font-size: 11px;
            vertical-align: top;
            word-wrap: break-word;
        }

        .col-idx { width: 80px; font-weight: 600; color: var(--primary-light); }
        .col-date { width: 85px; color: var(--text-light); }
        .col-tercero { width: auto; }
        .col-unidad { width: 100px; font-weight: 500; }
        .col-total { width: 110px; text-align: right; font-weight: 700; color: var(--primary); }

        .tercero-nit {
            display: block;
            font-size: 9px;
            color: var(--text-light);
            margin-top: 2px;
        }

        /* Sub-items (Desglose) */
        .sub-items-container {
            margin-top: 6px;
            padding-top: 4px;
            border-top: 1px dashed #EEE;
        }

        .sub-item {
            display: flex;
            justify-content: space-between;
            font-size: 9px;
            color: var(--text-light);
            margin-bottom: 2px;
            font-style: italic;
        }

        .sub-item-val {
            font-weight: 500;
        }

        /* Footer del Reporte */
        .footer-totals {
            margin-top: 30px;
            display: flex;
            justify-content: flex-end;
        }

        .total-card {
            background-color: var(--primary);
            color: var(--white);
            padding: 20px 40px;
            text-align: right;
            border-radius: 4px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .total-card label {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 2px;
            opacity: 0.8;
        }

        .total-card h3 {
            margin: 5px 0 0 0;
            font-size: 28px;
            font-weight: 700;
        }

        .legal-notice {
            margin-top: 50px;
            font-size: 8px;
            color: var(--text-light);
            text-align: center;
            line-height: 1.5;
        }

        .page-number:after { content: counter(page); }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="company-info">
                <h1>{{ empresa.razon_social }}</h1>
                <p>NIT: {{ empresa.nit }}</p>
            </div>
            <div class="report-title">
                <h2>Detalle de Facturación Masiva</h2>
                <div class="period-badge">PERIODO: {{ periodo }}</div>
            </div>
        </header>

        <div class="summary-box">
            <div class="summary-item">
                <label>Total Documentos</label>
                <span>{{ items|length }}</span>
            </div>
            <div class="summary-item">
                <label>Gran Total Facturado</label>
                <span>$ {{ "{:,.0f}".format(total_periodo).replace(',', '.') }}</span>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th class="col-idx">Nro. Factura</th>
                    <th class="col-date">Fecha</th>
                    <th class="col-tercero">Residente / Tercero</th>
                    <th class="col-unidad">{{ labels.entidad_secundaria_short or 'Unidad' }}</th>
                    <th class="col-total">Valor Total</th>
                </tr>
            </thead>
            <tbody>
                {% for item in items %}
                <tr>
                    <td class="col-idx"># {{ item.consecutivo }}</td>
                    <td class="col-date">{{ item.fecha.strftime('%Y-%m-%d') if item.fecha else '-' }}</td>
                    <td class="col-tercero">
                        <strong>{{ item.tercero_nombre }}</strong>
                        <span class="tercero-nit">NIT/CC: {{ item.tercero_nit }}</span>
                        
                        {% if item.sub_items %}
                        <div class="sub-items-container">
                            {% for sub in item.sub_items %}
                            <div class="sub-item">
                                <span>{{ sub.nombre }}</span>
                                <span class="sub-item-val">$ {{ "{:,.0f}".format(sub.valor).replace(',', '.') }}</span>
                            </div>
                            {% endfor %}
                        </div>
                        {% endif %}
                    </td>
                    <td class="col-unidad">{{ item.detalle }}</td>
                    <td class="col-total">$ {{ "{:,.0f}".format(item.total).replace(',', '.') }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <div class="footer-totals">
            <div class="total-card">
                <label>Total Consolidado</label>
                <h3>$ {{ "{:,.0f}".format(total_periodo).replace(',', '.') }}</h3>
            </div>
        </div>

        <div class="legal-notice">
            Este documento es un reporte informativo del proceso de facturación masiva.<br>
            Generado digitalmente por Finaxis Intelligence.
        </div>
    </div>
</body>
</html>

''',

    'reports/estado_cuenta_cliente_report.html': r'''
﻿<!DOCTYPE html>
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

    'reports/estado_cuenta_ph_historico_report.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{{ labels.titulo_reporte_historico }}</title>
    <style>
        @page { size: letter portrait; margin: 1cm; }
        body { font-family: 'Helvetica', 'Arial', sans-serif; font-size: 9px; color: #333; line-height: 1.3; }
        .header { text-align: center; margin-bottom: 15px; border-bottom: 2px solid #2c3e50; padding-bottom: 8px; }
        .header h1 { margin: 0; font-size: 14px; color: #2c3e50; text-transform: uppercase; }
        .header h2 { margin: 2px 0; font-size: 11px; font-weight: normal; }
        
        .report-header { background: #f8f9fa; padding: 10px; margin-bottom: 15px; border: 1px solid #dee2e6; border-radius: 4px; }
        .report-header h3 { margin: 0; font-size: 12px; color: #2c3e50; text-align: center; text-transform: uppercase; }
        
        .summary-grid { display: table; width: 100%; border: 1px solid #dee2e6; margin-bottom: 15px; background: #fff; }
        .summary-box { display: table-cell; width: 25%; padding: 8px; text-align: center; border-right: 1px solid #dee2e6; }
        .summary-box:last-child { border-right: none; }
        .summary-label { font-size: 8px; color: #666; text-transform: uppercase; margin-bottom: 3px; display: block; }
        .summary-value { font-size: 11px; font-weight: bold; color: #2c3e50; }
        .summary-value.positive { color: #28a745; }
        .summary-value.negative { color: #dc3545; }

        .info-section { display: table; width: 100%; margin-bottom: 15px; }
        .info-box { display: table-cell; width: 50%; padding: 5px; }
        .info-box p { margin: 2px 0; }
        .info-label { font-weight: bold; color: #555; width: 90px; display: inline-block; }

        table { width: 100%; border-collapse: collapse; margin-top: 5px; }
        th { background-color: #2c3e50; color: white; padding: 6px 4px; text-align: left; font-weight: 600; text-transform: uppercase; font-size: 8px; }
        td { padding: 6px 4px; border-bottom: 1px solid #eee; vertical-align: top; }
        .text-right { text-align: right; }
        .text-center { text-align: center; }
        
        .doc-num { font-family: monospace; font-weight: bold; font-size: 9px; }
        .sub-detalle { font-size: 8px; color: #666; margin-top: 2px; font-style: italic; }
        
        .footer { margin-top: 20px; font-size: 8px; color: #777; text-align: center; border-top: 1px solid #eee; padding-top: 8px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ empresa.razon_social }}</h1>
        <h2>NIT: {{ empresa.nit }}</h2>
    </div>

    <div class="report-header">
        <h3>{{ labels.titulo_reporte_historico }}</h3>
        <p style="text-align: center; margin: 3px 0 0 0; font-size: 8px;">
            Periodo: {{ fecha_inicio if fecha_inicio else 'Desde el inicio' }} al {{ fecha_fin }}
        </p>
    </div>

    <div class="info-section">
        <div class="info-box">
            <p><span class="info-label">{{ labels.entidad_principal }}:</span> {{ propietario.nombre }}</p>
            <p><span class="info-label">NIT/CC:</span> {{ propietario.documento }}</p>
        </div>
        <div class="info-box">
            <p><span class="info-label">{{ labels.entidad_secundaria }}:</span> {{ unidad_codigo }}</p>
            <p><span class="info-label">Fecha Impresión:</span> {{ fecha_impresion }}</p>
        </div>
    </div>

    <div class="summary-grid">
        <div class="summary-box">
            <span class="summary-label">Saldo Anterior</span>
            <span class="summary-value">${{ "{:,.0f}".format(saldo_anterior) }}</span>
        </div>
        <div class="summary-box">
            <span class="summary-label">Total Cargos (+)</span>
            <span class="summary-value negative">${{ "{:,.0f}".format(total_cargos if total_cargos else 0) }}</span>
        </div>
        <div class="summary-box">
            <span class="summary-label">Total Abonos (-)</span>
            <span class="summary-value positive">${{ "{:,.0f}".format(total_abonos if total_abonos else 0) }}</span>
        </div>
        <div class="summary-box" style="background: #e9ecef;">
            <span class="summary-label">Saldo Final</span>
            <span class="summary-value" style="font-size: 13px;">${{ "{:,.0f}".format(saldo_final) }}</span>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th style="width: 10%;">Fecha</th>
                <th style="width: 15%;">Documento</th>
                <th>Concepto / Detalle</th>
                <th class="text-right" style="width: 12%;">Cargo (+)</th>
                <th class="text-right" style="width: 12%;">Abono (-)</th>
                <th class="text-right" style="width: 15%;">Nuevo Saldo</th>
            </tr>
        </thead>
        <tbody>
            {% if saldo_anterior != 0 %}
            <tr style="background: #fafafa;">
                <td colspan="5" class="text-right" style="font-weight: bold;">SALDO ANTERIOR AL {{ fecha_inicio }}:</td>
                <td class="text-right" style="font-weight: bold;">${{ "{:,.0f}".format(saldo_anterior) }}</td>
            </tr>
            {% endif %}
            
            {% for t in transacciones %}
            <tr>
                <td>{{ t.fecha }}</td>
                <td class="doc-num">{{ t.documento }}</td>
                <td>
                    {{ t.detalle }}
                    {% if t.detalle_pago %}
                    <div class="sub-detalle">
                        Aplicado a: {{ t.detalle_pago | join(', ') }}
                    </div>
                    {% endif %}
                </td>
                <td class="text-right">{{ "${:,.0f}".format(t.debito) if t.debito > 0 else '-' }}</td>
                <td class="text-right">{{ "${:,.0f}".format(t.credito) if t.credito > 0 else '-' }}</td>
                <td class="text-right" style="font-weight: 600;">${{ "{:,.0f}".format(t.saldo) }}</td>
            </tr>
            {% else %}
            <tr>
                <td colspan="6" class="text-center" style="padding: 15px; color: #888;">No se registraron movimientos en el periodo seleccionado.</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <div class="footer">
        <p>Software de Gestión Contable Finaxis PH - Desarrollado para ambientes de alta eficiencia.</p>
        <p>Este reporte muestra el historial contable de su unidad basado en documentos oficiales procesados.</p>
    </div>
</body>
</html>

''',

    'reports/estado_cuenta_ph_pendientes_report.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{{ labels.titulo_reporte_cobro }}</title>
    <style>
        @page { size: letter portrait; margin: 1.5cm; }
        body { font-family: 'Helvetica', 'Arial', sans-serif; font-size: 10px; color: #333; line-height: 1.4; }
        .header { text-align: center; margin-bottom: 20px; border-bottom: 2px solid #2c3e50; padding-bottom: 10px; }
        .header h1 { margin: 0; font-size: 16px; color: #2c3e50; text-transform: uppercase; }
        .header h2 { margin: 2px 0; font-size: 12px; font-weight: normal; }
        .report-title { text-align: center; background: #f8f9fa; padding: 10px; margin-bottom: 20px; border: 1px solid #dee2e6; border-radius: 4px; }
        .report-title h3 { margin: 0; font-size: 14px; color: #2c3e50; }
        
        .info-section { display: table; width: 100%; margin-bottom: 20px; border-collapse: collapse; }
        .info-box { display: table-cell; width: 50%; vertical-align: top; padding: 5px; }
        .info-box p { margin: 3px 0; }
        .info-label { font-weight: bold; color: #555; width: 100px; display: inline-block; }

        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th { background-color: #2c3e50; color: white; padding: 8px 5px; text-align: left; font-weight: 600; text-transform: uppercase; font-size: 9px; }
        td { padding: 8px 5px; border-bottom: 1px solid #eee; vertical-align: middle; }
        .text-right { text-align: right; }
        .text-center { text-align: center; }
        
        .total-row { background-color: #f8f9fa; font-weight: bold; font-size: 11px; }
        .total-row td { border-top: 2px solid #2c3e50; border-bottom: 2px solid #2c3e50; }
        
        .footer { margin-top: 30px; font-size: 8px; color: #777; text-align: center; border-top: 1px solid #eee; padding-top: 10px; }
        
        .badge { padding: 2px 5px; border-radius: 3px; font-size: 8px; font-weight: bold; color: white; text-transform: uppercase; }
        .bg-factura { background-color: #0d6efd; }
        .bg-interes { background-color: #dc3545; }
        .bg-ajuste { background-color: #6c757d; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ empresa.razon_social }}</h1>
        <h2>NIT: {{ empresa.nit }}</h2>
    </div>

    <div class="report-title">
        <h3>{{ labels.titulo_reporte_cobro }}</h3>
        <p style="margin: 5px 0 0 0; font-size: 9px;">Fecha de Generación: {{ fecha_impresion }}</p>
    </div>

    <div class="info-section">
        <div class="info-box" style="border-right: 1px solid #eee;">
            <p><span class="info-label">{{ labels.entidad_principal }}:</span> {{ propietario.nombre }}</p>
            <p><span class="info-label">NIT/CC:</span> {{ propietario.documento }}</p>
        </div>
        <div class="info-box" style="padding-left: 15px;">
            <p><span class="info-label">{{ labels.entidad_secundaria }}:</span> {{ unidad_codigo }}</p>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th style="width: 12%;">Fecha</th>
                <th style="width: 15%;">Documento</th>
                <th style="width: 18%;">Tipo</th>
                <th>{{ labels.entidad_secundaria_short }}</th>
                <th class="text-right" style="width: 15%;">Valor Original</th>
                <th class="text-right" style="width: 15%;">Saldo Pendiente</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr>
                <td>{{ item.fecha_fmt }}</td>
                <td style="font-family: monospace; font-weight: bold;">{{ item.numero }}</td>
                <td>{{ item.tipo }}</td>
                <td class="text-center">{{ item.unidad_codigo }}</td>
                <td class="text-right">${{ "{:,.0f}".format(item.valor_total) }}</td>
                <td class="text-right" style="font-weight: bold;">${{ "{:,.0f}".format(item.saldo_pendiente) }}</td>
            </tr>
            {% else %}
            <tr>
                <td colspan="6" class="text-center" style="padding: 20px; color: #888;">No se encontraron saldos pendientes para esta unidad/propietario.</td>
            </tr>
            {% endfor %}
        </tbody>
        <tfoot>
            <tr class="total-row">
                <td colspan="5" class="text-right">TOTAL PENDIENTE A LA FECHA:</td>
                <td class="text-right" style="color: #c00;">${{ "{:,.0f}".format(total_pendiente) }}</td>
            </tr>
        </tfoot>
    </table>

    <div class="footer">
        <p>Este documento es una relación informativa de saldos y no constituye una factura de venta.</p>
        <p>Generado automáticamente por Finaxis - Software de Gestión PH</p>
    </div>
</body>
</html>

''',

    'reports/estado_cuenta_proveedor_report.html': r'''
﻿<!DOCTYPE html>
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
﻿<!DOCTYPE html>
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

    'reports/estado_resultados_gerencial.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Estado de Resultados Gerencial - {{ empresa_nombre }}</title>
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=DM+Sans:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            /* Colores Primarios (Sincronizados con Balance Gerencial) */
            --green-inst: #2D6A26;
            --green-light: #6BAD5E;
            --blue-slate: #4A6FA5;
            --gold-soft: #C9A84C;
            --green-text: #1A3D17;
            --blue-text: #1F3560;
            --gold-text: #6B5010;
            
            /* Fondos */
            --white: #FFFFFF;
            --bg-ingresos: #F2F8F1;
            --bg-gastos: #FDF5F5;
            --bg-resultado: #FBF8F1;
            --row-ingresos: #EEF5ED;
            --row-gastos: #F9EEEE;
            --row-resultado: #FAF5E9;
            --gray-light: #FAFAFA;
            --bg-grand-total: #1A3D17; /* Verde oscuro para el total final */
            
            /* Texto */
            --text-main: #1A1A1A;
            --text-muted: #BBBBBB;
            --text-labels: #444444;
            --red-contable: #C0392B;
        }

        @page {
            size: A4;
            margin: 0.5cm; /* Margen mínimo de seguridad */
        }

        body {
            margin: 0;
            padding: 0;
            background-color: var(--white);
            color: var(--text-main);
            font-family: 'DM Sans', sans-serif;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }

        .page-container {
            width: 190mm; /* A4 width (210) - margin (10*2) */
            min-height: 277mm; 
            margin: 0 auto;
            position: relative;
            background: var(--white);
            box-sizing: border-box;
        }

        /* Barras Decorativas */
        .top-bar {
            height: 4px;
            background: linear-gradient(90deg, var(--green-inst), var(--green-light), var(--gold-soft), var(--green-light), var(--green-inst));
            width: 100%;
        }

        .bottom-bar {
            height: 3px;
            background: linear-gradient(90deg, var(--green-inst), var(--green-light), var(--gold-soft));
            width: 100%;
            position: absolute;
            bottom: 0;
        }

        /* Cabecera */
        header {
            padding: 30px 56px 20px 56px;
            display: table;
            width: 100%;
            box-sizing: border-box;
            border-bottom: 1px solid #F0F0F0;
        }

        .header-left {
            display: table-cell;
            vertical-align: middle;
            text-align: left;
        }

        .header-right {
            display: table-cell;
            vertical-align: middle;
            text-align: right;
        }

        .badge {
            font-size: 9px;
            font-weight: 700;
            color: var(--green-inst);
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 5px;
            display: block;
        }
        .badge::before {
            content: "•";
            margin-right: 6px;
            font-size: 12px;
        }

        .company-name {
            font-family: 'Cormorant Garamond', serif;
            font-size: 38px;
            font-weight: 700;
            line-height: 1;
            margin: 0;
            color: var(--text-main);
        }
        .company-name span { color: var(--green-inst); }

        .company-nit {
            font-size: 10px;
            color: var(--text-muted);
            letter-spacing: 1.5px;
            margin-top: 4px;
            font-weight: 400;
        }

        .doc-title {
            font-family: 'Cormorant Garamond', serif;
            font-size: 18px;
            font-style: italic;
            color: #555555;
            margin-bottom: 10px;
        }

        .date-box {
            display: inline-block;
            border: 1.5px solid var(--green-inst);
            border-radius: 4px;
            padding: 6px 14px;
            text-align: center;
        }

        .date-label {
            font-size: 8px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: var(--green-inst);
            margin-bottom: 1px;
        }

        .date-value {
            font-size: 14px;
            font-weight: 700;
            color: var(--text-main);
        }

        /* Cuerpo */
        main {
            padding: 20px 56px;
        }

        /* Tarjetas de Sección */
        .section-card {
            border: 1.5px solid #E4E4E4;
            border-radius: 8px;
            overflow: hidden;
            background: var(--white);
            margin-bottom: 15px;
        }

        .card-header {
            padding: 10px 16px;
            display: flex;
            align-items: center;
            border-bottom: 1.5px solid #E4E4E4;
        }
        .card-header.ingresos { background: var(--bg-ingresos); }
        .card-header.gastos { background: var(--bg-gastos); }
        .card-header.resultado { background: var(--bg-resultado); }

        .header-stripe {
            width: 3px;
            height: 16px;
            border-radius: 2px;
            margin-right: 10px;
        }
        .ingresos .header-stripe { background: var(--green-inst); }
        .gastos .header-stripe { background: var(--red-contable); }
        .resultado .header-stripe { background: var(--gold-soft); }

        .card-title {
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: var(--text-labels);
        }

        /* Tablas */
        .report-table {
            width: 100%;
            border-collapse: collapse;
        }

        .sub-header {
            background: var(--gray-light);
            border-bottom: 1px solid #F0F0F0;
        }
        .sub-header td {
            padding: 4px 16px;
            font-size: 9px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: #AAAAAA;
        }

        .row-item td {
            padding: 6px 16px;
            border-bottom: 1px solid #F8F8F8;
            vertical-align: middle;
        }
        .acc-code { font-size: 9px; font-weight: 700; color: var(--text-muted); letter-spacing: 0.5px; width: 40px; }
        .acc-name { font-size: 12px; color: var(--text-labels); padding-right: 10px; }
        .acc-value { 
            font-size: 12px; 
            font-weight: 500; 
            text-align: right; 
            font-variant-numeric: tabular-nums; 
            white-space: nowrap;
            min-width: 100px;
        }

        .negativo { color: var(--red-contable) !important; }

        .row-subtotal td { padding: 8px 16px; font-weight: 700; font-size: 13px; }
        .ingresos .row-subtotal { background: #EEF5ED; border-top: 1.5px solid #D8E8D6; color: var(--green-inst); }
        .gastos .row-subtotal { background: #F9EEEE; border-top: 1.5px solid #E8D6D6; color: var(--red-contable); }

        .row-total td { padding: 10px 16px; font-weight: 700; font-size: 13.5px; }
        .ingresos .row-total { background: var(--row-ingresos); border-top: 2px solid var(--green-inst); color: var(--green-text); }
        .gastos .row-total { background: var(--row-gastos); border-top: 2px solid var(--red-contable); color: var(--red-contable); }
        .resultado .row-total { background: var(--row-resultado); border-top: 2px solid var(--gold-soft); color: var(--gold-text); }

        /* KPIs */
        .kpi-container {
            display: table;
            width: 100%;
            border-spacing: 15px 0;
            margin-top: 5px;
            margin-left: -15px;
        }

        .kpi-card {
            display: table-cell;
            width: 33.33%;
            border: 1.5px solid #E4E4E4;
            border-radius: 8px;
            padding: 15px;
            position: relative;
            background: var(--white);
        }
        .kpi-card::before {
            content: "";
            position: absolute;
            left: 0;
            top: 15%;
            bottom: 15%;
            width: 4px;
            border-radius: 0 2px 2px 0;
        }
        .kpi-ingresos::before { background: var(--green-inst); }
        .kpi-gastos::before { background: var(--red-contable); }
        .kpi-resultado::before { background: var(--gold-soft); }

        .kpi-label {
            font-size: 9px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: var(--text-muted);
            margin-bottom: 5px;
        }

        .kpi-value {
            font-size: 16px;
            font-weight: 700;
            color: var(--text-main);
            font-variant-numeric: tabular-nums;
            white-space: nowrap;
        }

        /* Grand Total */
        .grand-total-bar {
            background: var(--bg-grand-total);
            border: 2px solid var(--green-inst);
            border-radius: 8px;
            padding: 15px 25px;
            margin-top: 15px;
            display: table;
            width: 100%;
            box-sizing: border-box;
            color: white;
        }

        .gt-left {
            display: table-cell;
            vertical-align: middle;
            width: 40px;
        }

        .pulse-circle {
            width: 32px;
            height: 32px;
            background: var(--gold-soft);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--green-text);
        }

        .gt-center {
            display: table-cell;
            vertical-align: middle;
            padding-left: 15px;
        }

        .gt-label {
            font-family: 'Cormorant Garamond', serif;
            font-size: 16px;
            font-style: italic;
            font-weight: 600;
        }

        .gt-right {
            display: table-cell;
            vertical-align: middle;
            text-align: right;
        }

        .gt-val-prefix {
            font-size: 11px;
            color: #CBD5E1;
            margin-right: 5px;
        }

        .gt-value {
            font-size: 22px;
            font-weight: 700;
            color: var(--gold-soft);
            white-space: nowrap;
        }

        /* Gráficos */
        .charts-container {
            display: table;
            width: 100%;
            margin-top: 25px;
            page-break-inside: avoid;
        }

        .chart-box {
            display: table-cell;
            width: 50%;
            padding: 15px;
            border: 1px solid #E4E4E4;
            border-radius: 8px;
            vertical-align: top;
            background: white;
        }

        .chart-box:first-child { border-right: none; border-top-right-radius: 0; border-bottom-right-radius: 0; }
        .chart-box:last-child { border-top-left-radius: 0; border-bottom-left-radius: 0; }

        .chart-title {
            font-family: 'Cormorant Garamond', serif;
            font-size: 13px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-labels);
            margin-bottom: 15px;
            border-bottom: 1px solid #F0F0F0;
            padding-bottom: 5px;
        }

        /* Donut Chart */
        .donut-wrap {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .donut-legend {
            list-style: none;
            padding: 0;
            margin: 0;
            font-size: 10px;
        }
        .legend-item {
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            white-space: nowrap;
        }
        .swatch {
            width: 8px;
            height: 8px;
            border-radius: 2px;
            margin-right: 6px;
        }

        /* Bar Chart */
        .hbar-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        .hbar-item {
            margin-bottom: 10px;
        }
        .hbar-label {
            display: flex;
            justify-content: space-between;
            font-size: 9px;
            color: var(--text-labels);
            margin-bottom: 3px;
        }
        .hbar-name { font-weight: 600; }
        .hbar-track {
            height: 6px;
            background: #F0F0F0;
            border-radius: 3px;
            overflow: hidden;
        }
        .hbar-fill {
            height: 100%;
            border-radius: 3px;
        }

        /* Firmas */
        .signatures {
            margin-top: 30px;
            display: table;
            width: 100%;
        }

        .sig-col {
            display: table-cell;
            width: 50%;
            text-align: center;
            padding: 0 40px;
        }

        .sig-line {
            height: 1.5px;
            background: linear-gradient(90deg, transparent, var(--gold-soft), transparent);
            width: 80%;
            margin: 0 auto 10px auto;
        }

        .sig-name {
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: var(--text-main);
        }

        .sig-meta {
            font-size: 9px;
            color: var(--text-muted);
            margin-top: 4px;
        }

    </style>
</head>
<body>
    <div class="page-container">
        <div class="top-bar"></div>
        
        <header>
            <div class="header-left">
                <span class="badge">Informe Financiero Oficial</span>
                <h1 class="company-name">Verduras <span>La 21</span></h1>
                <div class="company-nit">NIT {{ empresa_nit or '942.807.497' }}</div>
            </div>
            <div class="header-right">
                <div class="doc-title">Estado de Resultados Gerencial</div>
                <div class="date-box">
                    <div class="date-label">Período</div>
                    <div class="date-value">{{ fecha_inicio }} — {{ fecha_fin }}</div>
                </div>
                <div style="font-size: 9px; color: #BBBBBB; margin-top: 8px; letter-spacing: 1px;">Cifras en Pesos Colombianos (COP)</div>
            </div>
        </header>

        <main>
            <!-- INGRESOS OPERACIONALES -->
            <div class="section-card">
                <div class="card-header ingresos">
                    <div class="header-stripe"></div>
                    <span class="card-title">Ingresos Operacionales</span>
                </div>
                <table class="report-table ingresos">
                    <tr class="sub-header">
                        <td colspan="3">▸ Detalle de Ingresos</td>
                    </tr>
                    {% for ing in report_data.ingresos %}
                    <tr class="row-item">
                        <td class="acc-code">{{ ing.codigo }}</td>
                        <td class="acc-name">{{ ing.nombre }}</td>
                        <td class="acc-value">
                            $ {{ "{:,.0f}".format(ing.saldo).replace(',', '.') }}
                        </td>
                    </tr>
                    {% endfor %}
                    <tr class="row-total">
                        <td colspan="2">TOTAL INGRESOS OPERACIONALES</td>
                        <td class="acc-value">
                            $ {{ "{:,.0f}".format(report_data.totales.total_ingresos).replace(',', '.') }}
                        </td>
                    </tr>
                </table>
            </div>

            <!-- COSTO DE VENTAS -->
            <div class="section-card">
                <div class="card-header gastos">
                    <div class="header-stripe" style="background: var(--gold-soft);"></div>
                    <span class="card-title">Costo de Ventas</span>
                </div>
                <table class="report-table gastos">
                    <tr class="sub-header">
                        <td colspan="3">▸ Costos Directos</td>
                    </tr>
                    {% for costo in report_data.costos %}
                    <tr class="row-item">
                        <td class="acc-code">{{ costo.codigo }}</td>
                        <td class="acc-name">{{ costo.nombre }}</td>
                        <td class="acc-value">
                            $ {{ "{:,.0f}".format(costo.saldo).replace(',', '.') }}
                        </td>
                    </tr>
                    {% endfor %}
                    <tr class="row-total" style="background: #FBF8F1; color: var(--gold-text); border-top-color: var(--gold-soft);">
                        <td colspan="2">TOTAL COSTO DE VENTAS</td>
                        <td class="acc-value">
                            $ {{ "{:,.0f}".format(report_data.totales.total_costos).replace(',', '.') }}
                        </td>
                    </tr>
                </table>
            </div>

            <!-- RESULTADO BRUTO -->
            <div class="section-card" style="border: 2px solid var(--green-inst); background: var(--bg-ingresos);">
                <table class="report-table">
                    <tr class="row-total" style="font-size: 16px; color: var(--green-inst);">
                        <td style="padding: 12px 16px;">UTILIDAD BRUTA</td>
                        <td class="acc-value" style="padding: 12px 16px;">
                            $ {{ "{:,.0f}".format(report_data.totales.utilidad_bruta).replace(',', '.') }}
                            <div style="font-size: 10px; font-weight: 400; color: var(--green-light);">MARGEN BRUTO: {{ "{:.1f}%".format(report_data.totales.porcentaje_margen_bruto) }}</div>
                        </td>
                    </tr>
                </table>
            </div>

            <!-- GASTOS OPERACIONALES -->
            <div class="section-card">
                <div class="card-header gastos">
                    <div class="header-stripe"></div>
                    <span class="card-title">Gastos Operacionales</span>
                </div>
                <table class="report-table gastos">
                    {% if report_data.gastos_nomina %}
                    <tr class="sub-header">
                        <td colspan="3">▸ Nómina y Carga Prestacional</td>
                    </tr>
                    {% for gasto in report_data.gastos_nomina %}
                    <tr class="row-item">
                        <td class="acc-code">{{ gasto.codigo }}</td>
                        <td class="acc-name">{{ gasto.nombre }}</td>
                        <td class="acc-value">$ {{ "{:,.0f}".format(gasto.saldo).replace(',', '.') }}</td>
                    </tr>
                    {% endfor %}
                    {% endif %}

                    {% if report_data.gastos_operativos %}
                    <tr class="sub-header">
                        <td colspan="3">▸ Gastos Operativos</td>
                    </tr>
                    {% for gasto in report_data.gastos_operativos %}
                    <tr class="row-item">
                        <td class="acc-code">{{ gasto.codigo }}</td>
                        <td class="acc-name">{{ gasto.nombre }}</td>
                        <td class="acc-value">$ {{ "{:,.0f}".format(gasto.saldo).replace(',', '.') }}</td>
                    </tr>
                    {% endfor %}
                    {% endif %}

                    <tr class="row-total">
                        <td colspan="2">TOTAL GASTOS ADMINISTRATIVOS Y VENTAS</td>
                        <td class="acc-value">
                            $ {{ "{:,.0f}".format(report_data.totales.total_gastos).replace(',', '.') }}
                        </td>
                    </tr>
                </table>
            </div>

            <!-- KPIs -->
            <div class="kpi-container">
                <div class="kpi-card kpi-ingresos">
                    <div class="kpi-label">Margen Bruto</div>
                    <div class="kpi-value">{{ "{:.1f}%".format(report_data.totales.porcentaje_margen_bruto) }}</div>
                </div>
                <div class="kpi-card kpi-gastos">
                    <div class="kpi-label">Margen Neto</div>
                    <div class="kpi-value">{{ "{:.1f}%".format(report_data.totales.porcentaje_margen_neto) }}</div>
                </div>
                <div class="kpi-card kpi-resultado">
                    <div class="kpi-label">Utilidad Ejercicio</div>
                    <div class="kpi-value {% if report_data.totales.utilidad_neta < 0 %}negativo{% endif %}">
                        {% if report_data.totales.utilidad_neta < 0 %}$ -{% else %}$ {% endif %}{{ "{:,.0f}".format(report_data.totales.utilidad_neta | abs).replace(',', '.') }}
                    </div>
                </div>
            </div>

            <!-- Grand Total Bar -->
            <div class="grand-total-bar">
                <div class="gt-left">
                    <div class="pulse-circle">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
                    </div>
                </div>
                <div class="gt-center">
                    <div class="gt-label">Resultado Final del Período</div>
                </div>
                <div class="gt-right">
                    <span class="gt-val-prefix">COP</span>
                    <span class="gt-value">{% if report_data.totales.utilidad_neta < 0 %}$ -{% else %}$ {% endif %}{{ "{:,.0f}".format(report_data.totales.utilidad_neta | abs).replace(',', '.') }}</span>
                </div>
            </div>

            <!-- ANÁLISIS VISUAL -->
            <div class="charts-container">
                <!-- Composición de Ingresos -->
                <div class="chart-box">
                    <div class="chart-title">Composición de Ingresos</div>
                    <div class="donut-wrap">
                        <div style="width: 80px;">
                            <svg viewBox="0 0 36 36" style="width: 80px; height: 80px;">
                                <circle r="15.9155" cx="18" cy="18" fill="none" stroke="#F0F0F0" stroke-width="4"></circle>
                                {% set ns = namespace(offset=25) %}
                                {% set colors = ['#2D6A26', '#6BAD5E', '#9ECFB5', '#C8E6D6', '#E0F0E6'] %}
                                {% for ing in report_data.ingresos[:5] %}
                                    {% if ing.porcentaje > 0 %}
                                    <circle r="15.9155" cx="18" cy="18" fill="none" 
                                            stroke="{{ colors[loop.index0] }}" 
                                            stroke-width="5" 
                                            stroke-dasharray="{{ ing.porcentaje }} {{ 100 - ing.porcentaje }}" 
                                            stroke-dashoffset="{{ ns.offset }}"></circle>
                                    {% set ns.offset = ns.offset - ing.porcentaje %}
                                    {% endif %}
                                {% endfor %}
                            </svg>
                        </div>
                        <ul class="donut-legend">
                            {% for ing in report_data.ingresos[:5] %}
                            <li class="legend-item">
                                <div class="swatch" style="background: {{ colors[loop.index0] }}"></div>
                                <span style="flex: 1;">{{ ing.nombre[:25] }}...</span>
                                <span style="font-weight: 700; margin-left: 8px;">{{ "{:.1f}%".format(ing.porcentaje) }}</span>
                            </li>
                            {% endfor %}
                        </ul>
                    </div>
                </div>

                <!-- Top Impactos -->
                <div class="chart-box">
                    <div class="chart-title">Top 5 Rubros de Impacto</div>
                    <ul class="hbar-list">
                        {% set bar_colors = ['#C0392B', '#E67E22', '#F39C12', '#D35400', '#2D6A26'] %}
                        {% for impacto in report_data.top_10_impactos[:5] %}
                        <li class="hbar-item">
                            <div class="hbar-label">
                                <span class="hbar-name">{{ impacto.nombre[:30] }}</span>
                                <span style="font-weight: 700;">$ {{ "{:,.0f}".format(impacto.saldo).replace(',', '.') }}</span>
                            </div>
                            <div class="hbar-track">
                                <div class="hbar-fill" style="width: {{ impacto.porcentaje }}%; background: {{ bar_colors[loop.index0] }}"></div>
                            </div>
                            <div style="font-size: 7px; text-align: right; color: #999; margin-top: 1px;">Impacto: {{ "{:.1f}%".format(impacto.porcentaje) }}</div>
                        </li>
                        {% endfor %}
                    </ul>
                </div>
            </div>

            <!-- Signatures -->
            <div class="signatures">
                <div class="sig-col">
                    <div class="sig-line"></div>
                    <div class="sig-name">Representante Legal</div>
                    <div class="sig-meta">C.C. _______________________</div>
                </div>
                <div class="sig-col">
                    <div class="sig-line"></div>
                    <div class="sig-name">Contador Público</div>
                    <div class="sig-meta">T.P. _______________________</div>
                </div>
            </div>
        </main>

        <div class="bottom-bar"></div>
    </div>
</body>
</html>

''',

    'reports/exito_fe_template.html': r'''
﻿<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">
    <title>Factura Electrónica de Venta - Estilo Exito</title>
    <style>
        /* RESET & BASE */
        * {
            box-sizing: border-box;
        }

        body {
            font-family: 'Helvetica', 'Arial', sans-serif;
            color: #000;
            font-size: 10px;
            margin: 0;
            padding: 0;
            line-height: 1.2;
            background: #ffffff;
        }

        @page {
            size: letter;
            margin: 1cm;
        }

        /* UTILIDADES */
        .text-right {
            text-align: right;
        }

        .text-center {
            text-align: center;
        }

        .text-bold {
            font-weight: bold;
        }

        .text-uppercase {
            text-transform: uppercase;
        }

        /* HEADER CENTRADO */
        .header {
            text-align: center;
            margin-bottom: 20px;
        }

        .company-name {
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 2px;
        }

        .company-nit {
            font-size: 11px;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .company-details {
            font-size: 9px;
            margin-bottom: 2px;
        }

        /* SECCIÓN TIPO DOCUMENTO Y NÚMERO (IZQUIERDA) */
        .doc-info {
            position: absolute;
            top: 0;
            left: 0;
            text-align: left;
            width: 200px;
        }

        .doc-title {
            font-size: 11px;
            font-weight: bold;
        }

        .doc-number {
            font-size: 12px;
            font-weight: bold;
        }

        .doc-dates {
            font-size: 8px;
            margin-top: 5px;
        }

        /* CLIENTE Y DIRECCIÓN */
        .client-section {
            width: 100%;
            border-top: 1px solid #000;
            border-bottom: 1px solid #000;
            padding: 10px 0;
            margin-bottom: 15px;
            display: table;
        }

        .client-col {
            display: table-cell;
            width: 50%;
            vertical-align: top;
        }

        .row {
            display: table;
            width: 100%;
            margin-bottom: 3px;
        }

        .label {
            display: table-cell;
            width: 80px;
            font-weight: bold;
        }

        .value {
            display: table-cell;
        }

        /* TABLA DE ITEMS */
        .items-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 15px;
        }

        .items-table th {
            border-top: 1px solid #000;
            border-bottom: 1px solid #000;
            padding: 5px;
            text-align: center;
            background: #f2f2f2;
            font-weight: bold;
        }

        .items-table td {
            padding: 5px;
            border-bottom: 1px solid #eee;
        }

        /* SECCIÓN TOTALES E IMPUESTOS */
        .summary-section {
            display: table;
            width: 100%;
            margin-top: 10px;
        }

        .taxes-box {
            display: table-cell;
            width: 60%;
            vertical-align: top;
        }

        .totals-box {
            display: table-cell;
            width: 40%;
            vertical-align: top;
        }

        .summary-table {
            width: 100%;
            border-collapse: collapse;
        }

        .summary-table th,
        .summary-table td {
            border: 1px solid #ddd;
            padding: 4px;
            text-align: right;
        }

        .summary-table th {
            background: #f2f2f2;
        }

        .total-pay-row {
            background: #eee;
            font-weight: bold;
            font-size: 12px;
        }

        /* PIE DE PÁGINA (DIAN) */
        .dian-section {
            margin-top: 20px;
            padding: 10px;
            border: 1px solid #000;
            display: table;
            width: 100%;
        }

        .qr-col {
            display: table-cell;
            width: 120px;
            text-align: center;
            vertical-align: middle;
        }

        .dian-info-col {
            display: table-cell;
            padding-left: 15px;
            vertical-align: top;
            font-size: 8px;
        }

        .amount-words {
            margin: 10px 0;
            font-weight: bold;
            font-style: italic;
        }
    </style>
</head>

<body>

    <div class="header">
        <div class="company-name">{{empresa.razon_social}}</div>
        <div class="company-nit">NIT: {{empresa.nit}}</div>
        <div class="company-details">Responsable de IVA</div>
        <div class="company-details">{{empresa.direccion}} - {{empresa.ciudad}} - Colombia</div>
        <div class="company-details">Teléfono - {{empresa.telefono}}</div>
        <div class="company-details">E-mail: {{empresa.email}}</div>
        <div class="company-details text-bold">REPRESENTACION GRAFICA DE FACTURA ELECTRONICA</div>
    </div>

    <div class="doc-info">
        <div class="doc-title">FACTURA ELECTRONICA DE VENTA</div>
        <div class="doc-number">{{documento.tipo_documento_codigo}} - {{documento.numero}}</div>
        <div class="doc-dates">
            Fecha Validación DIAN: {{documento.fecha_emision}}<br>
            Hora Validación DIAN: {{documento.hora_emision|default('00:00:00')}}
        </div>
    </div>

    <div class="client-section">
        <div class="client-col">
            <div class="row">
                <div class="label">Cliente:</div>
                <div class="value text-bold">{{tercero.razon_social}}</div>
            </div>
            <div class="row">
                <div class="label">CC o NIT:</div>
                <div class="value">{{tercero.nit}}</div>
            </div>
            <div class="row">
                <div class="label">Régimen:</div>
                <div class="value">{{tercero.regimen|default('No responsable de IVA')}}</div>
            </div>
            <div class="row">
                <div class="label">Obligación:</div>
                <div class="value">{{tercero.responsabilidad|default('No responsable')}}</div>
            </div>
            <div class="row">
                <div class="label">Email:</div>
                <div class="value">{{tercero.email}}</div>
            </div>
            <div class="row">
                <div class="label">Forma de Pago:</div>
                <div class="value">{{documento.forma_pago|default('Contado')}}</div>
            </div>
        </div>
        <div class="client-col">
            <div class="row">
                <div class="label">Dirección:</div>
                <div class="value">{{tercero.direccion}}</div>
            </div>
            <div class="row">
                <div class="label">Ciudad:</div>
                <div class="value">{{tercero.ciudad}}</div>
            </div>
            <div class="row">
                <div class="label">Teléfono:</div>
                <div class="value">{{tercero.telefono}}</div>
            </div>
            <div class="row">
                <div class="label">Medios de Pago:</div>
                <div class="value">Efectivo</div>
            </div>
            <div class="row">
                <div class="label">Plazo:</div>
                <div class="value">0 Dias</div>
            </div>
            <div class="row">
                <div class="label">Vencimiento:</div>
                <div class="value">{{documento.fecha_vencimiento}}</div>
            </div>
        </div>
    </div>

    <table class="items-table">
        <thead>
            <tr>
                <th width="4%">#</th>
                <th width="14%">Código</th>
                <th width="32%">Descripción</th>
                <th width="7%">Cantidad</th>
                <th width="7%">UM</th>
                <th width="12%">Val. Unit</th>
                <th width="10%">% IVA</th>
                <th width="14%">Val. Item</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr>
                <td class="text-center">{{ loop.index }}</td>
                <td>{{ item.producto_codigo }}</td>
                <td>{{ item.producto_nombre }}</td>
                <td class="text-center">{{ item.cantidad }}</td>
                <td class="text-center">Unidad</td>
                <td class="text-right">{{ item.precio_unitario|format_decimal }}</td>
                <td class="text-right">
                    {% if item.tasa_iva and item.tasa_iva > 0 %}
                    {{ (item.tasa_iva * 100)|round(0) }}%
                    {% else %}
                    0%
                    {% endif %}
                </td>
                <td class="text-right">{{ item.subtotal|format_decimal }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <div class="summary-section">
        <div class="taxes-box">
            <table class="summary-table" style="width: 90%;">
                <thead>
                    <tr>
                        <th colspan="4" class="text-center">Impuestos y Retenciones</th>
                    </tr>
                    <tr>
                        <th>Tipo</th>
                        <th>Base</th>
                        <th>Porcentaje</th>
                        <th>Valor</th>
                    </tr>
                </thead>
                <tbody>
                    {% if totales.base_gravable_5 != '0.00' %}
                    <tr>
                        <td class="text-center">IVA</td>
                        <td>{{ totales.base_gravable_5 }}</td>
                        <td class="text-center">5.00%</td>
                        <td>{{ totales.iva_5 }}</td>
                    </tr>
                    {% endif %}
                    {% if totales.base_gravable_19 != '0.00' %}
                    <tr>
                        <td class="text-center">IVA</td>
                        <td>{{ totales.base_gravable_19 }}</td>
                        <td class="text-center">19.00%</td>
                        <td>{{ totales.iva_19 }}</td>
                    </tr>
                    {% endif %}
                    {% if totales.base_exenta != '0.00' and totales.base_gravable_19 == '0.00' and
                    totales.base_gravable_5 == '0.00' %}
                    <tr>
                        <td class="text-center">Totalmente Exento</td>
                        <td>{{ totales.base_exenta }}</td>
                        <td class="text-center">0.00%</td>
                        <td>0.00</td>
                    </tr>
                    {% endif %}
                    {% if totales.base_gravable_5 == '0.00' and totales.base_gravable_19 == '0.00' and
                    totales.base_exenta == '0.00' %}
                    <tr>
                        <td class="text-center">N/A</td>
                        <td>0.00</td>
                        <td class="text-center">0.00%</td>
                        <td>0.00</td>
                    </tr>
                    {% endif %}
                </tbody>
            </table>

            <div class="amount-words">
                PRECIO EN LETRAS SON: {{ totales.valor_letras|upper }}
            </div>

            <div style="border: 1px solid #ddd; padding: 10px; min-height: 50px;">
                <strong>OBSERVACIONES:</strong><br>
                {{ documento.observaciones or '.' }}
            </div>
        </div>

        <div class="totals-box">
            <table class="summary-table">
                <thead>
                    <tr>
                        <th colspan="2" class="text-center">Totales</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Nro Lineas:</td>
                        <td>{{ items|length }}</td>
                    </tr>
                    <tr>
                        <td>Base:</td>
                        <td>{{ totales.subtotal }}</td>
                    </tr>
                    <tr>
                        <td>Impuestos:</td>
                        <td>{{ totales.impuestos|default(totales.iva_19) }}</td>
                    </tr>
                    <tr>
                        <td>Retenciones:</td>
                        <td>0.00</td>
                    </tr>
                    <tr>
                        <td>Descuentos En Lineas:</td>
                        <td>0.00</td>
                    </tr>
                    <tr>
                        <td>Descuentos Globales:</td>
                        <td>{{ totales.descuento_global|default('0.00') }}</td>
                    </tr>
                    <tr>
                        <td>Otros Cargos:</td>
                        <td>{{ totales.cargos_globales|default('0.00') }}</td>
                    </tr>
                    <tr class="total-pay-row">
                        <td>Total Factura:</td>
                        <td>{{ totales.total }}</td>
                    </tr>
                    <tr class="total-pay-row">
                        <td>Total a Pagar:</td>
                        <td>{{ totales.total }}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    {% if documento.dian_cufe %}
    <div class="dian-section">
        <div class="qr-col">
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=100x100&data=https://catalogo-vpfe-hab.dian.gov.co/document/searchqr?documentkey={{documento.dian_cufe}}"
                width="100" height="100">
        </div>
        <div class="dian-info-col">
            <strong>Resolución de Facturación Electrónica</strong><br>
            Nro. {{documento.resolucion_numero}} de {{documento.resolucion_fecha}}<br>
            Prefijo: {{documento.resolucion_prefijo}}, Rango {{documento.resolucion_rango_desde}} Al
            {{documento.resolucion_rango_hasta}}<br>
            Vigencia Desde: {{documento.resolucion_fecha}} Hasta:
            {{documento.resolucion_fecha_fin|default('2027-10-10')}}<br><br>

            <strong>CUFE:</strong> {{documento.dian_cufe}}<br><br>

            La presente Factura Electrónica de Venta, es un título valor de acuerdo con lo establecido en el Código de
            Comercio y en especial en los artículos 621,772 y 774.
        </div>
    </div>
    {% endif %}

</body>

</html>

''',

    'reports/fuentes_usos_report.html': r'''
﻿<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">
    <title>Estado de Fuentes y Usos</title>
    <style>
        @page {
            size: letter landscape;
            margin: 1cm;
        }

        body {
            font-family: 'Helvetica', sans-serif;
            font-size: 10px;
            color: #333;
        }

        .header {
            text-align: center;
            margin-bottom: 20px;
            border-bottom: 2px solid #004085;
            padding-bottom: 10px;
        }

        .header h1 {
            margin: 0;
            color: #004085;
            font-size: 18px;
            text-transform: uppercase;
        }

        .header p {
            margin: 2px 0;
            font-size: 12px;
        }

        .section-title {
            background-color: #f8f9fa;
            padding: 5px;
            font-weight: bold;
            border-left: 4px solid #004085;
            margin-top: 15px;
            margin-bottom: 5px;
            font-size: 12px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 10px;
        }

        th,
        td {
            border: 1px solid #dee2e6;
            padding: 6px;
            text-align: left;
        }

        th {
            background-color: #004085;
            color: white;
            font-weight: bold;
            text-align: center;
        }

        .text-right {
            text-align: right;
        }

        .text-center {
            text-align: center;
        }

        .font-bold {
            font-weight: bold;
        }

        .bg-gray {
            background-color: #f1f1f1;
        }

        .text-success {
            color: #28a745;
        }

        /* Fuentes */
        .text-danger {
            color: #dc3545;
        }

        /* Usos */

        .summary-box {
            display: inline-block;
            width: 48%;
            vertical-align: top;
            border: 1px solid #ccc;
            padding: 10px;
            margin-top: 10px;
        }

        .kt-summary {
            background-color: #e9ecef;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
    </style>
</head>

<body>
    <div class="header">
        <h1>{{ empresa.razon_social }}</h1>
        <p>NIT: {{ empresa.nit }}</p>
        <p><strong>ESTADO DE FUENTES Y USOS (CAPITAL DE TRABAJO)</strong></p>
        <p>Periodo: {{ fecha_inicio }} al {{ fecha_fin }}</p>
    </div>

    <!-- Resumen Ejecutivo -->
    <div class="kt-summary">
        <table style="width: 100%; border: none;">
            <tr style="background: none;">
                <td style="border: none; width: 50%;">
                    <h3>Capital de Trabajo Neto (K.T.)</h3>
                    <p>Activo Corriente Inicial: <strong>{{ "${:,.0f}".format(resumen_kt.activo_cte_ini) }}</strong></p>
                    <p>Pasivo Corriente Inicial: <strong>{{ "${:,.0f}".format(resumen_kt.pasivo_cte_ini) }}</strong></p>
                    <hr>
                    <p>K.T. Inicial: <strong>{{ "${:,.0f}".format(resumen_kt.kt_ini) }}</strong></p>
                </td>
                <td style="border: none; width: 50%;">
                    <h3>Variación en el Periodo</h3>
                    <p>Activo Corriente Final: <strong>{{ "${:,.0f}".format(resumen_kt.activo_cte_fin) }}</strong></p>
                    <p>Pasivo Corriente Final: <strong>{{ "${:,.0f}".format(resumen_kt.pasivo_cte_fin) }}</strong></p>
                    <hr>
                    <p>K.T. Final: <strong>{{ "${:,.0f}".format(resumen_kt.kt_fin) }}</strong></p>
                    <h4 class="{{ 'text-success' if resumen_kt.variacion_kt > 0 else 'text-danger' }}">
                        Variación K.T.: {{ "${:,.0f}".format(resumen_kt.variacion_kt) }}
                    </h4>
                </td>
            </tr>
        </table>
    </div>

    <div class="section-title">Detalle de Variaciones por Cuenta</div>
    <table>
        <thead>
            <tr>
                <th style="width: 10%;">Código</th>
                <th style="width: 30%;">Cuenta</th>
                <th style="width: 15%;">Saldo Inicial</th>
                <th style="width: 15%;">Saldo Final</th>
                <th style="width: 15%; background-color: #28a745;">FUENTES (Origen)</th>
                <th style="width: 15%; background-color: #dc3545;">USOS (Aplicación)</th>
            </tr>
        </thead>
        <tbody>
            {% for fila in filas %}
            <tr>
                <td class="text-center">{{ fila.cuenta_codigo }}</td>
                <td>{{ fila.cuenta_nombre }}</td>
                <td class="text-right">{{ "${:,.0f}".format(fila.saldo_inicial) }}</td>
                <td class="text-right">{{ "${:,.0f}".format(fila.saldo_final) }}</td>
                <td class="text-right font-bold text-success">
                    {% if fila.fuente > 0 %}{{ "${:,.0f}".format(fila.fuente) }}{% endif %}
                </td>
                <td class="text-right font-bold text-danger">
                    {% if fila.uso > 0 %}{{ "${:,.0f}".format(fila.uso) }}{% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
        <tfoot>
            <tr class="bg-gray">
                <td colspan="4" class="text-right font-bold">TOTALES:</td>
                <td class="text-right font-bold text-success">{{ "${:,.0f}".format(totales.total_fuentes) }}</td>
                <td class="text-right font-bold text-danger">{{ "${:,.0f}".format(totales.total_usos) }}</td>
            </tr>
            <tr>
                <td colspan="4" class="text-right font-bold">Diferencia (Fuentes - Usos):</td>
                <td colspan="2" class="text-center font-bold">
                    {{ "${:,.0f}".format(totales.diferencia) }}
                    <br>
                    <span style="font-size: 9px; font-weight: normal;">(Debe ser igual a la Variación K.T.)</span>
                </td>
            </tr>
        </tfoot>
    </table>

    <div style="font-size: 9px; color: #666; margin-top: 20px;">
        <p><strong>Nota Interpretativa:</strong><br>
            - <strong>FUENTES:</strong> Dinero generado por disminución de Activos (ej. cobro de cartera) o aumento de
            Pasivos (ej. financiación proveedores).<br>
            - <strong>USOS:</strong> Dinero utilizado para aumentar Activos (ej. compra inventario) o disminuir Pasivos
            (ej. pago deudas).</p>
    </div>
</body>

</html>

''',

    'reports/generic_document_template.html': r'''
﻿<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">
    <style>
        @page {
            size: letter;
            margin: 2cm;
        }

        body {
            font-family: 'Helvetica', sans-serif;
            font-size: 11px;
            color: #333;
            margin: 0;
            padding: 20px;
        }

        /* ... (rest of styles) */

        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }

        tr {
            page-break-inside: avoid;
        }

        th {
            background: #333333;
            color: white;
            padding: 5px;
            text-align: left;
            font-size: 10px;
        }

        td {
            padding: 5px;
            border-bottom: 1px solid #eee;
        }

        .text-right {
            text-align: right;
        }

        .font-mono {
            font-family: 'Courier New', monospace;
        }

        .footer-totals {
            background: #f0f0f0;
            font-weight: bold;
        }

        .footer-totals td {
            border-top: 2px solid #333;
        }

        .letras-row td {
            background: #fff;
            padding-top: 10px;
            font-style: italic;
            border: none;
        }

        .signatures {
            margin-top: 50px;
            width: 100%;
            display: table;
        }

        .sig-col {
            display: table-cell;
            width: 25%;
            text-align: center;
            vertical-align: bottom;
            height: 40px;
        }

        .sig-line {
            border-top: 1px solid #333;
            margin: 0 10px;
            padding-top: 5px;
            font-size: 10px;
            font-weight: bold;
        }
    </style>
</head>

<body>
    <table class="header-table">
        <tr>
            <td width="60%" valign="top">
                {% if empresa.logo_url %}
                <img src="{{empresa.logo_url}}" style="max-height: 60px; margin-bottom: 5px;"><br>
                {% endif %}
                <div class="company-name">{{empresa.razon_social}}</div>
                <div>NIT: {{empresa.nit}}</div>
                <div>{{empresa.direccion}}</div>
                <div>{{empresa.telefono}}</div>
            </td>
            <td width="40%" valign="top" align="right">
                <div class="doc-type-box">{{documento.tipo_nombre}}</div>
                <div class="doc-number">N° {{documento.consecutivo}}</div>
                <div style="text-align: right; margin-top: 5px;">Fecha: <strong>{{documento.fecha_emision}}</strong>
                </div>
            </td>
        </tr>
    </table>

    <div class="info-box">
        <table style="width: 100%; margin: 0;">
            <tr>
                <td width="15%"><strong>Tercero:</strong></td>
                <td width="45%">{{tercero.razon_social}}</td>
                <td width="15%"><strong>NIT/CC:</strong></td>
                <td width="25%">{{tercero.nit}}</td>
            </tr>
            {% if documento.observaciones %}
            <tr>
                <td colspan="4" style="border-top: 1px dashed #ccc; padding-top: 5px;">
                    <strong>Notas:</strong> {{documento.observaciones}}
                </td>
            </tr>
            {% endif %}
        </table>
    </div>

    <table>
        <thead>
            <tr>
                <th width="15%">Cuenta</th>
                <th width="45%">Descripción</th>
                <th width="20%" class="text-right">Débito</th>
                <th width="20%" class="text-right">Crédito</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr>
                <td class="font-mono">{{item.producto_codigo}}</td>
                <td>{{item.producto_nombre}}</td>
                <td class="text-right font-mono">{{item.debito_fmt}}</td>
                <td class="text-right font-mono">{{item.credito_fmt}}</td>
            </tr>
            {% endfor %}
            <tr class="footer-totals">
                <td colspan="2" class="text-right">SUMAS IGUALES:</td>
                <td class="text-right font-mono">{{totales.total_debito}}</td>
                <td class="text-right font-mono">{{totales.total_credito}}</td>
            </tr>
            <tr class="letras-row">
                <td colspan="4"><strong>SON:</strong> {{totales.valor_letras}}</td>
            </tr>
        </tbody>
    </table>

    <div class="signatures">
        <div class="sig-col">
            <div class="sig-line">Elaboró</div>
        </div>
        <div class="sig-col">
            <div class="sig-line">Revisó</div>
        </div>
        <div class="sig-col">
            <div class="sig-line">Aprobó</div>
        </div>
        <div class="sig-col">
            <div class="sig-line">Contabilizó</div>
        </div>
    </div>

    {% if documento.dian_cufe %}
    <div style="margin-top: 30px; border-top: 1px dashed #ccc; padding-top: 10px; font-size: 9px; color: #555;">
        <strong>Información Fiscal (DIAN/Proveedor):</strong><br>
        <strong>{% if 'SOPORTE' in documento.tipo_nombre.upper() %}CUDS{% else %}CUFE{% endif %}:</strong> <span
            style="font-family: monospace;">{{documento.dian_cufe}}</span><br>
        <strong>Estado DIAN:</strong> {{documento.dian_estado}}<br>
        {% if not documento.dian_xml_url %}
        <br>
        <em>Nota: Documento generado en entorno de Pruebas/Habilitación (Sin URL pública directa). Este documento es
            válido como soporte interno.</em>
        {% endif %}
    </div>
    {% endif %}

    <div style="text-align: center; font-size: 9px; color: #aaa; margin-top: 20px;">
        Gracias por su confianza.
    </div>
</body>

</html>

''',

    'reports/historial_consumo_report.html': r'''
﻿<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">
    <title>Historial de Consumo</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            font-size: 12px;
            color: #333;
            margin: 0;
            padding: 20px;
        }

        .header {
            margin-bottom: 20px;
            border-bottom: 2px solid #555;
            padding-bottom: 10px;
        }

        .header h1 {
            margin: 0;
            font-size: 24px;
            color: #2c3e50;
        }

        .header h2 {
            margin: 5px 0 0;
            font-size: 16px;
            color: #666;
            font-weight: normal;
        }

        .meta-info {
            margin-bottom: 20px;
            font-size: 11px;
            color: #666;
        }

        .filters-info {
            background: #f0f4f8;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            border: 1px solid #dce4ec;
        }

        .filters-info strong {
            color: #2c3e50;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            /* Asegurar que la cabecera se repita en cada página */
            display: table;
        }

        thead {
            display: table-header-group;
        }

        tfoot {
            display: table-footer-group;
        }

        tr {
            page-break-inside: avoid;
        }

        th,
        td {
            border-bottom: 1px solid #eee;
            padding: 8px;
            text-align: left;
        }

        th {
            background-color: #f8f9fa;
            color: #495057;
            font-weight: bold;
            font-size: 11px;
            text-transform: uppercase;
        }

        tr:nth-child(even) {
            background-color: #fdfdfd;
        }

        .impact-positive {
            color: #27ae60;
            font-weight: bold;
        }

        .impact-negative {
            color: #c0392b;
            font-weight: bold;
        }

        .footer {
            margin-top: 40px;
            border-top: 1px solid #eee;
            padding-top: 10px;
            text-align: center;
            color: #999;
            font-size: 10px;
        }

        .tag {
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 9px;
            font-weight: bold;
            display: inline-block;
        }

        .tag-consumo {
            background: #e0e7ff;
            color: #4338ca;
        }

        .tag-compra {
            background: #fef3c7;
            color: #b45309;
        }

        .tag-reversion {
            background: #d1fae5;
            color: #065f46;
        }

        .tag-cierre {
            background: #f1f5f9;
            color: #475569;
        }

        .summary-box {
            margin-top: 30px;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 15px;
            background-color: #f8fafc;
        }

        .summary-title {
            font-size: 14px;
            font-weight: bold;
            color: #1e293b;
            margin-bottom: 10px;
            border-bottom: 2px solid #cbd5e1;
            padding-bottom: 5px;
        }

        .summary-row {
            display: table;
            width: 100%;
            margin-bottom: 5px;
        }

        .summary-label {
            display: table-cell;
            color: #64748b;
            font-size: 11px;
            padding-right: 10px;
        }

        .summary-value {
            display: table-cell;
            text-align: right;
            font-weight: bold;
            color: #0f172a;
            font-size: 11px;
        }

        .summary-total {
            margin-top: 10px;
            border-top: 1px solid #cbd5e1;
            padding-top: 5px;
        }

        .summary-total .summary-label {
            font-size: 12px;
            color: #334155;
            font-weight: bold;
        }

        .summary-total .summary-value {
            font-size: 14px;
            color: #2563eb;
            /* Blue for emphasis */
        }
    </style>
</head>

<body>
    <div class="header">
        <h1>{{ empresa.razon_social }}</h1>
        <h2>Reporte de Historial de Consumo</h2>
        <div class="meta-info">NIT: {{ empresa.nit }} | Generado el: {{ fecha_generacion }}</div>
    </div>

    <div class="filters-info">
        <strong>Filtros Aplicados:</strong><br>
        Rango de Fechas: {{ filtros.fecha_inicio or 'Inicio' }} - {{ filtros.fecha_fin or 'Actualidad' }} <br>
        Tipo de Operación: {{ filtros.tipo_operacion or 'TODOS' }} <br>
        <strong>Registros Exportados: {{ items|length }} (Max: 5000)</strong>
    </div>

    <table>
        <thead>
            <tr>
                <th width="15%">Fecha</th>
                <th width="15%">Operación</th>
                <th width="20%">Empresa</th>
                <th width="25%">Detalle / Documento</th>
                <th width="15%">Origen/Bolsa</th>
                <th width="10%" style="text-align: right">Impacto</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr>
                <td>{{ item.fecha.strftime('%d/%m/%Y') }} <br> <span style="font-size: 9px; color:#999">{{
                        item.fecha.strftime('%H:%M') }}</span></td>
                <td>
                    {% if item.tipo_operacion == 'CONSUMO' %} <span class="tag tag-consumo">CONSUMO</span>
                    {% elif item.tipo_operacion == 'COMPRA' %} <span class="tag tag-compra">COMPRA RECARGA</span>
                    {% elif item.tipo_operacion == 'REVERSION' %} <span class="tag tag-reversion">REVERSIÓN</span>
                    {% elif item.tipo_operacion == 'CIERRE' %} <span class="tag tag-cierre">CIERRE MENSUAL</span>
                    {% else %} {{ item.tipo_operacion }} {% endif %}
                </td>
                <td>
                    <span style="font-weight:bold; color:#444; font-size:10px;">
                        {{ item.empresa_generadora or '-' }}
                    </span>
                </td>
                <td>
                    {% if item.documento_numero %}
                    <strong>{{ item.documento_tipo_codigo or 'Doc' }} #{{ item.documento_numero }}</strong>
                    {% else %}
                    -
                    {% endif %}
                </td>
                <td>
                    {% if item.bolsa_origen %}
                    {{ item.bolsa_origen }}
                    {% else %}
                    {{ item.fuente_tipo or '-' }}
                    {% endif %}
                </td>
                <td style="text-align: right">
                    {% if item.tipo_operacion in ['REVERSION', 'COMPRA'] %}
                    <span class="impact-positive">+{{ item.cantidad }}</span>
                    {% else %}
                    <span class="impact-negative">-{{ item.cantidad }}</span>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>

    </table>

    <!-- SECTION DE RESUMEN -->
    {% if stats %}
    <div class="summary-box">
        <div class="summary-title">RESUMEN DE CONSUMO DEL PERIODO</div>

        <div class="summary-row">
            <div class="summary-label">Consumo Plan Mensual:</div>
            <div class="summary-value">{{ stats.consumo_plan }}</div>
        </div>
        {% if stats.consumo_anterior > 0 %}
        <div class="summary-row">
            <div class="summary-label">Consumo Periodos Anteriores (Diferido):</div>
            <div class="summary-value">{{ stats.consumo_anterior }}</div>
        </div>
        {% endif %}
        <!-- <div class="summary-row">
            <div class="summary-label">Consumo Bolsas Excedentes:</div>
            <div class="summary-value">{{ stats.consumo_bolsa }}</div>
        </div> -->
        <div class="summary-row">
            <div class="summary-label">Consumo Recargas Adicionales:</div>
            <div class="summary-value">{{ stats.consumo_recarga }}</div>
        </div>

        <div class="summary-row summary-total">
            <div class="summary-label">TOTAL GENERAL CONSUMIDO:</div>
            <div class="summary-value">{{ stats.consumo_total_bruto }}</div>
        </div>
    </div>
    {% endif %}

    <div class="footer">
        Este reporte fue generado automáticamente por el sistema FINAXIS.
    </div>
</body>

</html>

''',

    'reports/income_statement_cc_report.html': r'''
﻿<!DOCTYPE html>
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
﻿<!DOCTYPE html>
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

    'reports/inventario_document_template.html': r'''
﻿<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{{documento.tipo_nombre}}</title>
    <style>
        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            color: #1f2937;
            font-size: 9px;
            margin: 0;
            padding: 12px;
            line-height: 1.3;
            background: #ffffff;
        }

        /* ENCABEZADO EMPRESARIAL */
        .header-container {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 18px;
            padding-bottom: 12px;
            border-bottom: 2px solid #e5e7eb;
        }

        .company-section {
            width: 58%;
        }

        .company-logo {
            max-height: 42px;
            margin-bottom: 6px;
            display: block;
        }

        .company-name {
            font-size: 13px;
            font-weight: 700;
            color: #111827;
            text-transform: uppercase;
            margin-bottom: 4px;
            letter-spacing: 0.3px;
        }

        .company-details {
            color: #6b7280;
            font-size: 8px;
            line-height: 1.4;
        }

        .document-section {
            width: 38%;
            text-align: right;
        }

        .doc-type {
            font-size: 16px;
            font-weight: 800;
            color: #1d4ed8;
            text-transform: uppercase;
            margin-bottom: 4px;
            letter-spacing: -0.2px;
        }

        .doc-number {
            font-size: 14px;
            color: #dc2626;
            font-weight: 700;
            margin-bottom: 10px;
        }

        .doc-dates {
            font-size: 8px;
            color: #6b7280;
            line-height: 1.4;
        }

        .date-label {
            font-weight: 600;
            color: #374151;
        }

        /* INFORMACIÓN CLIENTE */
        .client-section {
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 16px;
            border-left: 4px solid #3b82f6;
        }

        .client-header {
            font-size: 7px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #64748b;
            font-weight: 700;
            margin-bottom: 6px;
        }

        .client-name {
            font-size: 11px;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 3px;
        }

        .client-info {
            color: #64748b;
            font-size: 8px;
            line-height: 1.4;
        }

        /* TABLA PRODUCTOS */
        .products-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 16px;
            font-size: 8px;
            border-radius: 6px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .products-table th {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            color: #ffffff;
            padding: 8px 6px;
            font-size: 7px;
            text-transform: uppercase;
            font-weight: 600;
            text-align: left;
            letter-spacing: 0.5px;
        }

        .products-table th.text-center { text-align: center; }
        .products-table th.text-right { text-align: right; }

        .products-table td {
            padding: 6px;
            border-bottom: 1px solid #f1f5f9;
            vertical-align: middle;
        }

        .products-table tbody tr:nth-child(even) {
            background-color: #fafbfc;
        }

        .products-table tbody tr:hover {
            background-color: #f0f9ff;
        }

        .item-code {
            font-family: 'SF Mono', 'Monaco', 'Cascadia Code', monospace;
            font-size: 7px;
            color: #64748b;
            font-weight: 600;
        }

        .item-description {
            font-size: 8px;
            color: #1e293b;
            font-weight: 500;
        }

        .item-quantity {
            text-align: center;
            font-weight: 700;
            color: #1d4ed8;
            font-size: 8px;
        }

        .item-price, .item-amount {
            text-align: right;
            font-family: 'SF Mono', 'Monaco', 'Cascadia Code', monospace;
            font-size: 8px;
            font-weight: 600;
            color: #374151;
        }

        /* SECCIÓN TOTALES PROFESIONAL */
        .totals-container {
            display: flex;
            justify-content: space-between;
            gap: 20px;
            margin-bottom: 24px;
        }

        .notes-area {
            width: 52%;
        }

        .amount-words {
            background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
            color: #991b1b;
            padding: 8px 10px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 7px;
            text-transform: uppercase;
            margin-bottom: 10px;
            border-left: 4px solid #dc2626;
            letter-spacing: 0.3px;
        }

        .observations {
            background: #fffbeb;
            border: 1px solid #f59e0b;
            border-left: 4px solid #d97706;
            padding: 8px;
            border-radius: 4px;
            color: #92400e;
            font-size: 7px;
            line-height: 1.4;
        }

        .totals-panel {
            width: 45%;
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }

        .total-line {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 6px 12px;
            border-bottom: 1px solid #f3f4f6;
            font-size: 8px;
        }

        .total-line:last-child {
            border-bottom: none;
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            color: #ffffff;
            font-weight: 800;
            font-size: 10px;
        }

        .total-line.subtotal-line {
            background: #f8fafc;
            font-weight: 600;
        }

        .total-line.tax-line {
            background: #fef7ff;
            color: #7c2d12;
        }

        .total-line.base-line {
            background: #f0fdf4;
            color: #166534;
        }

        .total-label {
            font-weight: 600;
            color: #374151;
        }

        .total-line:last-child .total-label {
            color: #ffffff;
        }

        .total-line.tax-line .total-label,
        .total-line.base-line .total-label {
            font-weight: 700;
        }

        .total-value {
            font-family: 'SF Mono', 'Monaco', 'Cascadia Code', monospace;
            font-weight: 700;
            text-align: right;
            min-width: 85px;
        }

        /* PIE DE PÁGINA EMPRESARIAL */
        .footer-area {
            margin-top: 28px;
            padding-top: 16px;
            border-top: 2px solid #f1f5f9;
        }

        .legal-notice {
            background: #f8fafc;
            padding: 8px 10px;
            border-radius: 4px;
            color: #64748b;
            font-size: 7px;
            line-height: 1.4;
            margin-bottom: 12px;
            text-align: justify;
        }

        .signature-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 16px;
        }

        .signature-field {
            text-align: center;
            padding-top: 28px;
        }

        .signature-line {
            border-top: 1.5px solid #64748b;
            padding-top: 4px;
            font-size: 7px;
            font-weight: 700;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .footer-brand {
            text-align: center;
            color: #94a3b8;
            font-size: 7px;
            font-style: italic;
            margin-top: 12px;
        }
    </style>
</head>

<body>
    <!-- ENCABEZADO EMPRESARIAL -->
    <div class="header-container">
        <div class="company-section">
            {% if empresa.logo_url %}
            <img src="{{empresa.logo_url}}" class="company-logo" alt="Logo Empresa">
            {% endif %}
            <div class="company-name">{{empresa.razon_social}}</div>
            <div class="company-details">
                NIT: {{empresa.nit}} • {{empresa.direccion}}<br>
                Tel: {{empresa.telefono}}{% if empresa.email %} • {{empresa.email}}{% endif %}
            </div>
        </div>
        
        <div class="document-section">
            <div class="doc-type">{{documento.tipo_nombre}}</div>
            <div class="doc-number">N° {{documento.consecutivo}}</div>
            <div class="doc-dates">
                <span class="date-label">Fecha:</span> {{documento.fecha_emision}}<br>
                {% if documento.fecha_vencimiento %}<span class="date-label">Vence:</span> {{documento.fecha_vencimiento}}<br>{% endif %}
                {% if documento.vendedor %}<span class="date-label">Vendedor:</span> {{documento.vendedor}}{% endif %}
            </div>
        </div>
    </div>

    <!-- INFORMACIÓN DEL CLIENTE -->
    <div class="client-section">
        <div class="client-header">Cliente / Proveedor</div>
        <div class="client-name">{{tercero.razon_social}}</div>
        <div class="client-info">
            NIT/CC: {{tercero.nit}}{% if tercero.direccion %} • {{tercero.direccion}}{% endif %}{% if tercero.telefono %} • Tel: {{tercero.telefono}}{% endif %}
        </div>
    </div>

    <!-- TABLA DE PRODUCTOS -->
    <table class="products-table">
        <thead>
            <tr>
                <th width="10%">Código</th>
                <th width="40%">Descripción del Producto/Servicio</th>
                <th width="8%" class="text-center">Cant.</th>
                <th width="12%" class="text-right">Precio Unit.</th>
                <th width="10%" class="text-right">Descuento</th>
                <th width="20%" class="text-right">Valor Total</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr>
                <td class="item-code">{{item.producto_codigo}}</td>
                <td class="item-description">{{item.producto_nombre}}</td>
                <td class="item-quantity">{{item.cantidad}}</td>
                <td class="item-price">{{item.precio_unitario}}</td>
                <td class="item-price">{{item.descuento|default('0.00')}}</td>
                <td class="item-amount">{{item.subtotal}}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <!-- TOTALES Y DISCRIMINACIÓN FISCAL -->
    <div class="totals-container">
        <div class="notes-area">
            {% if totales.valor_letras %}
            <div class="amount-words">
                SON: {{totales.valor_letras}}
            </div>
            {% endif %}

            {% if documento.observaciones %}
            <div class="observations">
                <strong>Observaciones:</strong><br>
                {{documento.observaciones}}
            </div>
            {% endif %}
        </div>

        <div class="totals-panel">
            <!-- SUBTOTAL -->
            <div class="total-line subtotal-line">
                <span class="total-label">Subtotal:</span>
                <span class="total-value">{{totales.subtotal}}</span>
            </div>
            
            <!-- DESCUENTOS -->
            {% if totales.descuentos and totales.descuentos != '0.00' %}
            <div class="total-line">
                <span class="total-label">Descuentos:</span>
                <span class="total-value">-{{totales.descuentos}}</span>
            </div>
            {% endif %}
            
            <!-- DISCRIMINACIÓN DE BASES GRAVABLES -->
            {% if totales.base_exenta and totales.base_exenta != '0.00' %}
            <div class="total-line base-line">
                <span class="total-label">Base Exenta (0%):</span>
                <span class="total-value">{{totales.base_exenta}}</span>
            </div>
            {% endif %}
            
            {% if totales.base_gravable_5 and totales.base_gravable_5 != '0.00' %}
            <div class="total-line base-line">
                <span class="total-label">Base Gravable (5%):</span>
                <span class="total-value">{{totales.base_gravable_5}}</span>
            </div>
            {% endif %}
            
            {% if totales.base_gravable_19 and totales.base_gravable_19 != '0.00' %}
            <div class="total-line base-line">
                <span class="total-label">Base Gravable (19%):</span>
                <span class="total-value">{{totales.base_gravable_19}}</span>
            </div>
            {% endif %}
            
            <!-- DISCRIMINACIÓN DE IMPUESTOS -->
            {% if totales.iva_5 and totales.iva_5 != '0.00' %}
            <div class="total-line tax-line">
                <span class="total-label">IVA (5%):</span>
                <span class="total-value">{{totales.iva_5}}</span>
            </div>
            {% endif %}
            
            {% if totales.iva_19 and totales.iva_19 != '0.00' %}
            <div class="total-line tax-line">
                <span class="total-label">IVA (19%):</span>
                <span class="total-value">{{totales.iva_19}}</span>
            </div>
            {% endif %}
            
            <!-- RETENCIONES -->
            {% if totales.retencion and totales.retencion != '0.00' %}
            <div class="total-line">
                <span class="total-label">Retención:</span>
                <span class="total-value">-{{totales.retencion}}</span>
            </div>
            {% endif %}
            
            <!-- TOTAL FINAL -->
            <div class="total-line">
                <span class="total-label">TOTAL A PAGAR:</span>
                <span class="total-value">{{totales.total}}</span>
            </div>
        </div>
    </div>

    <!-- PIE DE PÁGINA EMPRESARIAL -->
    <div class="footer-area">
        <div class="legal-notice">
            Esta factura se asimila en todos sus efectos a una letra de cambio de conformidad con el artículo 774 del Código de Comercio. 
            Los pagos realizados después del vencimiento causarán intereses de mora según las tasas legales vigentes.
        </div>

        <div class="signature-grid">
            <div class="signature-field">
                <div class="signature-line">Elaboró</div>
            </div>
            <div class="signature-field">
                <div class="signature-line">Revisó</div>
            </div>
            <div class="signature-field">
                <div class="signature-line">Aprobó</div>
            </div>
            <div class="signature-field">
                <div class="signature-line">Recibí Conforme</div>
            </div>
        </div>

        <div class="footer-brand">
            Gracias por su confianza • Powered by ContaPY Enterprise
        </div>
    </div>
</body>
</html>

''',

    'reports/inventarios_y_balances_report.html': r'''
﻿<!DOCTYPE html>
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

    'reports/invoice_premium_template.html': r'''
﻿<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">
    <title>{{documento.tipo_nombre}} - Premium</title>
    <style>
        @page {
            size: letter;
            margin: 0;
            /* Usaremos paddings internos para mayor control del diseño */
        }

        body {
            font-family: 'Garamond', 'Georgia', serif;
            color: #1a1a1a;
            font-size: 10px;
            margin: 0;
            padding: 0;
            line-height: 1.5;
            background-color: #ffffff;
        }

        .page-accent {
            height: 8px;
            background: linear-gradient(90deg, #1e293b 0%, #475569 100%);
            width: 100%;
        }

        .container {
            padding: 40px 50px;
        }

        /* ENCABEZADO */
        .header {
            display: table;
            width: 100%;
            margin-bottom: 40px;
        }

        .header-left {
            display: table-cell;
            vertical-align: top;
            width: 60%;
        }

        .header-right {
            display: table-cell;
            vertical-align: top;
            width: 40%;
            text-align: right;
        }

        .company-logo {
            max-height: 80px;
            margin-bottom: 15px;
        }

        .company-name {
            font-size: 22px;
            font-weight: bold;
            color: #1e293b;
            margin: 0;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .company-info {
            font-size: 9px;
            color: #64748b;
            font-family: sans-serif;
            margin-top: 5px;
        }

        .doc-label {
            font-size: 28px;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 3px;
            margin: 0;
            font-weight: 300;
        }

        .doc-number-box {
            display: inline-block;
            background: #f8fafc;
            padding: 10px 20px;
            border: 1px solid #e2e8f0;
            margin-top: 10px;
        }

        .doc-number {
            font-size: 16px;
            font-weight: bold;
            color: #1e293b;
        }

        /* BLOQUES DE DATOS */
        .info-grid {
            display: table;
            width: 100%;
            margin-bottom: 30px;
            border-top: 1px solid #f1f5f9;
            padding-top: 20px;
        }

        .info-col {
            display: table-cell;
            width: 50%;
        }

        .section-title {
            font-family: sans-serif;
            font-size: 8px;
            font-weight: 800;
            text-transform: uppercase;
            color: #94a3b8;
            margin-bottom: 8px;
            letter-spacing: 1px;
        }

        .client-name {
            font-size: 14px;
            font-weight: bold;
            color: #1e293b;
            margin: 0 0 5px 0;
        }

        .data-text {
            font-size: 10px;
            color: #475569;
            font-family: sans-serif;
        }

        /* TABLA DE ITEMS */
        .items-container {
            margin-top: 20px;
            margin-bottom: 40px;
        }

        table.items-table {
            width: 100%;
            border-collapse: collapse;
        }

        table.items-table th {
            font-family: sans-serif;
            background-color: #f8fafc;
            color: #475569;
            padding: 12px 10px;
            text-align: left;
            font-size: 8px;
            font-weight: 800;
            text-transform: uppercase;
            border-bottom: 2px solid #1e293b;
        }

        table.items-table td {
            padding: 15px 10px;
            border-bottom: 1px solid #f1f5f9;
            vertical-align: top;
        }

        .item-desc {
            font-weight: bold;
            color: #1e293b;
        }

        .item-sub {
            font-size: 8px;
            color: #64748b;
            margin-top: 3px;
        }

        .text-right {
            text-align: right;
        }

        .text-center {
            text-align: center;
        }

        /* TOTALES */
        .footer-grid {
            display: table;
            width: 100%;
            margin-top: 20px;
        }

        .footer-left {
            display: table-cell;
            width: 60%;
            vertical-align: top;
        }

        .footer-right {
            display: table-cell;
            width: 40%;
            vertical-align: top;
        }

        .totals-table {
            width: 100%;
            border-collapse: collapse;
        }

        .totals-table td {
            padding: 8px 10px;
            font-family: sans-serif;
        }

        .total-row {
            background-color: #1e293b;
            color: #ffffff;
            font-size: 14px;
            font-weight: bold;
        }

        .total-row td {
            padding: 12px 10px !important;
        }

        .payment-info {
            background-color: #fffbeb;
            border: 1px solid #fef3c7;
            padding: 15px;
            margin-top: 20px;
            font-size: 9px;
            color: #92400e;
        }

        /* FISCAL */
        .fiscal-area {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px dashed #cbd5e1;
            display: table;
            width: 100%;
        }

        .fiscal-left {
            display: table-cell;
            width: 75%;
            font-size: 8px;
            color: #64748b;
            font-family: sans-serif;
        }

        .fiscal-right {
            display: table-cell;
            width: 25%;
            text-align: right;
        }

        .qr-placeholder {
            width: 80px;
            height: 80px;
            background: #eee;
            margin-left: auto;
        }

        .cufe-text {
            font-family: monospace;
            word-break: break-all;
            background: #f1f5f9;
            padding: 5px;
            display: block;
            margin-top: 5px;
            color: #0f172a;
        }

        .signature-line {
            margin-top: 60px;
            border-top: 1px solid #94a3b8;
            width: 200px;
            padding-top: 5px;
            font-size: 8px;
            text-transform: uppercase;
            font-family: sans-serif;
            color: #94a3b8;
        }

        .finaxis-brand {
            text-align: center;
            margin-top: 40px;
            font-size: 7px;
            color: #cbd5e1;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
    </style>
</head>

<body>
    <div class="page-accent"></div>
    <div class="container">
        <!-- CABECERA -->
        <div class="header">
            <div class="header-left">
                {% if empresa.logo_url %}
                <img src="{{empresa.logo_url}}" class="company-logo">
                {% endif %}
                <h1 class="company-name">{{empresa.razon_social}}</h1>
                <div class="company-info">
                    NIT: {{empresa.nit}} • Régimen Común<br>
                    {{empresa.direccion}}<br>
                    {{empresa.email}} • {{empresa.telefono}}
                </div>
            </div>
            <div class="header-right">
                <h2 class="doc-label">{{documento.tipo_nombre}}</h2>
                <div class="doc-number-box">
                    <span style="font-size: 8px; display: block; color: #94a3b8; text-transform: uppercase;">Número de
                        Documento</span>
                    <span class="doc-number">{{documento.prefix}}{{documento.consecutivo}}</span>
                </div>
                <div style="margin-top: 15px; font-size: 10px; color: #475569;">
                    <strong>Fecha:</strong> {{documento.fecha_emision}}<br>
                    {% if documento.fecha_vencimiento %}
                    <strong>Vencimiento:</strong> {{documento.fecha_vencimiento}}
                    {% endif %}
                </div>
            </div>
        </div>

        <!-- INFO CLIENTE Y OTROS -->
        <div class="info-grid">
            <div class="info-col">
                <div class="section-title">Facturado a</div>
                <h3 class="client-name">{{tercero.razon_social}}</h3>
                <div class="data-text">
                    ID/NIT: {{tercero.nit}}<br>
                    {{tercero.direccion}}<br>
                    {{tercero.telefono}}
                </div>
            </div>
            <div class="info-col" style="padding-left: 20px;">
                <div class="section-title">Detalles de Operación</div>
                <div class="data-text">
                    <strong>Vendedor:</strong> {{documento.vendedor|default('N/A')}}<br>
                    <strong>Forma de Pago:</strong> {{documento.metodo_pago|default('Contado')}}<br>
                    <strong>Moneda:</strong> COP - Pesos Colombianos
                </div>
            </div>
        </div>

        <!-- ITEMS -->
        <div class="items-container">
            <table class="items-table">
                <thead>
                    <tr>
                        <th width="50%">Descripción del Servicio</th>
                        <th width="10%" class="text-center">Cant.</th>
                        <th width="20%" class="text-right">Precio Unit.</th>
                        <th width="20%" class="text-right">Subtotal</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in items %}
                    <tr>
                        <td>
                            <div class="item-desc">{{item.producto_nombre}}</div>
                            <div class="item-sub">Cod: {{item.producto_codigo}}</div>
                        </td>
                        <td class="text-center">{{item.cantidad}}</td>
                        <td class="text-right">{{item.precio_unitario}}</td>
                        <td class="text-right">{{item.subtotal}}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <!-- TOTALES Y NOTAS -->
        <div class="footer-grid">
            <div class="footer-left">
                <div class="section-title">Observaciones</div>
                <div style="font-size: 9px; color: #475569; padding-right: 30px;">
                    {{documento.observaciones|default('Sin observaciones adicionales.')}}
                </div>

                <div class="payment-info">
                    <strong>Información de Pago:</strong><br>
                    Por favor realizar transferencia a la cuenta de ahorros No. XXX-XXXXXX-XX de Banco XXXXXX.<br>
                    Referencia: Factura {{documento.consecutivo}}
                </div>
            </div>
            <div class="footer-right">
                <table class="totals-table">
                    <tr>
                        <td class="text-right">Subtotal:</td>
                        <td class="text-right" width="40%">{{totales.subtotal}}</td>
                    </tr>
                    {% if totales.descuentos and totales.descuentos != '0.00' %}
                    <tr>
                        <td class="text-right">Descuentos:</td>
                        <td class="text-right" style="color: #dc2626;">-{{totales.descuentos}}</td>
                    </tr>
                    {% endif %}
                    <tr>
                        <td class="text-right">Impuestos (IVA):</td>
                        <td class="text-right">{{totales.iva_19|default(totales.iva_5)|default('0.00')}}</td>
                    </tr>
                    <tr class="total-row">
                        <td class="text-right">TOTAL:</td>
                        <td class="text-right">{{totales.total}}</td>
                    </tr>
                </table>
                <div style="font-size: 8px; font-style: italic; text-align: right; margin-top: 10px; color: #94a3b8;">
                    Son: {{totales.valor_letras}}
                </div>
            </div>
        </div>

        <!-- AREA FISCAL DIAN -->
        {% if documento.dian_cufe %}
        <div class="fiscal-area">
            <div class="fiscal-left">
                <strong>INFORMACIÓN FISCAL DIAN</strong><br>
                Software Proveedor: <strong>FINAXIS ENTERPRISE</strong> (Tecnología Cloud)<br>
                Tipo: {% if 'SOPORTE' in documento.tipo_nombre.upper() %}Documento Soporte Electrónico{% else %}Factura
                Electrónica de Venta{% endif %}<br>
                CUFE/CUDS:
                <span class="cufe-text">{{documento.dian_cufe}}</span>
            </div>
            <div class="fiscal-right">
                {% if documento.qr_base64 %}
                <img src="data:image/png;base64,{{documento.qr_base64}}" style="width: 80px; height: 80px;">
                {% else %}
                <div class="qr-placeholder"
                    style="display: flex; align-items: center; justify-content: center; font-size: 6px;">
                    CÓDIGO QR VALIDACIÓN
                </div>
                {% endif %}
            </div>
        </div>
        {% endif %}

        <div class="signature-line">
            Recibido por (Nombre y Cédula)
        </div>

        <div class="finaxis-brand">
            Software de Gestión Inteligente • FINAXIS.COM.CO
        </div>
    </div>
</body>

</html>

''',

    'reports/invoice_template.html': r'''
﻿<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">
    <title>{{documento.tipo_nombre}}</title>
    <style>
        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            color: #1f2937;
            font-size: 9px;
            margin: 0;
            padding: 12px;
            line-height: 1.3;
            background: #ffffff;
        }

        /* ENCABEZADO EMPRESARIAL */
        .header-container {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 18px;
            padding-bottom: 12px;
            border-bottom: 2px solid #e5e7eb;
        }

        .company-section {
            width: 58%;
        }

        .company-logo {
            max-height: 42px;
            margin-bottom: 6px;
            display: block;
        }

        .company-name {
            font-size: 13px;
            font-weight: 700;
            color: #111827;
            text-transform: uppercase;
            margin-bottom: 4px;
            letter-spacing: 0.3px;
        }

        .company-details {
            color: #6b7280;
            font-size: 8px;
            line-height: 1.4;
        }

        .document-section {
            width: 38%;
            text-align: right;
        }

        .doc-type {
            font-size: 16px;
            font-weight: 800;
            color: #1d4ed8;
            text-transform: uppercase;
            margin-bottom: 4px;
            letter-spacing: -0.2px;
        }

        .doc-number {
            font-size: 14px;
            color: #dc2626;
            font-weight: 700;
            margin-bottom: 10px;
        }

        .doc-dates {
            font-size: 8px;
            color: #6b7280;
            line-height: 1.4;
        }

        .date-label {
            font-weight: 600;
            color: #374151;
        }

        /* INFORMACIÓN CLIENTE */
        .client-section {
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 16px;
            border-left: 4px solid #3b82f6;
        }

        .client-header {
            font-size: 7px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #64748b;
            font-weight: 700;
            margin-bottom: 6px;
        }

        .client-name {
            font-size: 11px;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 3px;
        }

        .client-info {
            color: #64748b;
            font-size: 8px;
            line-height: 1.4;
        }

        /* TABLA PRODUCTOS */
        /* CONFIGURACIÓN DE PÁGINA PARA PDF (WeasyPrint) */
        @page {
            size: letter;
            margin: 1cm;
        }

        .products-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 16px;
            font-size: 8px;
        }

        .products-table th {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            color: #ffffff;
            padding: 8px 6px;
            font-size: 7px;
            text-transform: uppercase;
            font-weight: 600;
            text-align: left;
            letter-spacing: 0.5px;
        }

        .products-table th.text-center {
            text-align: center;
        }

        .products-table th.text-right {
            text-align: right;
        }

        .products-table td {
            padding: 6px;
            border-bottom: 1px solid #f1f5f9;
            vertical-align: middle;
        }

        .products-table tr {
            page-break-inside: avoid;
            /* Evita que una fila se corte a la mitad */
        }

        .products-table tbody tr:nth-child(even) {
            background-color: #fafbfc;
        }

        .products-table tbody tr:hover {
            background-color: #f0f9ff;
        }

        .item-code {
            font-family: 'SF Mono', 'Monaco', 'Cascadia Code', monospace;
            font-size: 7px;
            color: #64748b;
            font-weight: 600;
        }

        .item-description {
            font-size: 8px;
            color: #1e293b;
            font-weight: 500;
        }

        .item-quantity {
            text-align: center;
            font-weight: 700;
            color: #1d4ed8;
            font-size: 8px;
        }

        .item-price,
        .item-amount {
            text-align: right;
            font-family: 'SF Mono', 'Monaco', 'Cascadia Code', monospace;
            font-size: 8px;
            font-weight: 600;
            color: #374151;
        }

        /* SECCIÓN TOTALES PROFESIONAL */
        .totals-container {
            display: flex;
            justify-content: space-between;
            gap: 20px;
            margin-bottom: 24px;
        }

        .notes-area {
            width: 52%;
        }

        .amount-words {
            background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
            color: #991b1b;
            padding: 8px 10px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 7px;
            text-transform: uppercase;
            margin-bottom: 10px;
            border-left: 4px solid #dc2626;
            letter-spacing: 0.3px;
        }

        .observations {
            background: #fffbeb;
            border: 1px solid #f59e0b;
            border-left: 4px solid #d97706;
            padding: 8px;
            border-radius: 4px;
            color: #92400e;
            font-size: 7px;
            line-height: 1.4;
        }

        .totals-panel {
            width: 45%;
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        .total-line {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 6px 12px;
            border-bottom: 1px solid #f3f4f6;
            font-size: 8px;
        }

        .total-line:last-child {
            border-bottom: none;
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            color: #ffffff;
            font-weight: 800;
            font-size: 10px;
        }

        .total-line.subtotal-line {
            background: #f8fafc;
            font-weight: 600;
        }

        .total-line.tax-line {
            background: #fef7ff;
            color: #7c2d12;
        }

        .total-line.base-line {
            background: #f0fdf4;
            color: #166534;
        }

        .total-label {
            font-weight: 600;
            color: #374151;
        }

        .total-line:last-child .total-label {
            color: #ffffff;
        }

        .total-line.tax-line .total-label,
        .total-line.base-line .total-label {
            font-weight: 700;
        }

        .total-value {
            font-family: 'SF Mono', 'Monaco', 'Cascadia Code', monospace;
            font-weight: 700;
            text-align: right;
            min-width: 85px;
        }

        /* PIE DE PÁGINA EMPRESARIAL */
        .footer-area {
            margin-top: 28px;
            padding-top: 16px;
            border-top: 2px solid #f1f5f9;
        }

        .legal-notice {
            background: #f8fafc;
            padding: 8px 10px;
            border-radius: 4px;
            color: #64748b;
            font-size: 7px;
            line-height: 1.4;
            margin-bottom: 12px;
            text-align: justify;
        }

        .signature-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 16px;
        }

        .signature-field {
            text-align: center;
            padding-top: 28px;
        }

        .signature-line {
            border-top: 1.5px solid #64748b;
            padding-top: 4px;
            font-size: 7px;
            font-weight: 700;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .footer-brand {
            text-align: center;
            color: #94a3b8;
            font-size: 7px;
            font-style: italic;
            margin-top: 12px;
        }
    </style>
</head>

<body>
    <!-- ENCABEZADO EMPRESARIAL -->
    <div class="header-container">
        <div class="company-section">
            {% if empresa.logo_url %}
            <img src="{{empresa.logo_url}}" class="company-logo" alt="Logo Empresa">
            {% endif %}
            <div class="company-name">{{empresa.razon_social}}</div>
            <div class="company-details">
                NIT: {{empresa.nit}} • {{empresa.direccion}}<br>
                Tel: {{empresa.telefono}}{% if empresa.email %} • {{empresa.email}}{% endif %}
            </div>
        </div>

        <div class="document-section">
            <div class="doc-type">{{documento.tipo_nombre}}</div>
            <div class="doc-number">N° {{documento.consecutivo}}</div>
            <div class="doc-dates">
                <span class="date-label">Fecha:</span> {{documento.fecha_emision}}<br>
                {% if documento.fecha_vencimiento %}<span class="date-label">Vence:</span>
                {{documento.fecha_vencimiento}}<br>{% endif %}
                {% if documento.vendedor %}<span class="date-label">Vendedor:</span> {{documento.vendedor}}{% endif %}
            </div>
        </div>
    </div>

    <!-- INFORMACIÓN DEL CLIENTE -->
    <div class="client-section">
        <div class="client-header">Cliente / Proveedor</div>
        <div class="client-name">{{tercero.razon_social}}</div>
        <div class="client-info">
            NIT/CC: {{tercero.nit}}{% if tercero.direccion %} • {{tercero.direccion}}{% endif %}{% if tercero.telefono
            %} • Tel: {{tercero.telefono}}{% endif %}
        </div>
    </div>

    <!-- TABLA DE PRODUCTOS -->
    <table class="products-table">
        <thead>
            <tr>
                <th width="10%">Código</th>
                <th width="40%">Descripción del Producto/Servicio</th>
                <th width="8%" class="text-center">Cant.</th>
                <th width="12%" class="text-right">Precio Unit.</th>
                <th width="10%" class="text-right">Descuento</th>
                <th width="20%" class="text-right">Valor Total</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr>
                <td class="item-code">{{item.producto_codigo}}</td>
                <td class="item-description">{{item.producto_nombre}}</td>
                <td class="item-quantity">{{item.cantidad}}</td>
                <td class="item-price">{{item.precio_unitario}}</td>
                <td class="item-price">{{item.descuento|default('0.00')}}</td>
                <td class="item-amount">{{item.subtotal}}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <!-- TOTALES Y DISCRIMINACIÓN FISCAL -->
    <div class="totals-container">
        <div class="notes-area">
            {% if totales.valor_letras %}
            <div class="amount-words">
                SON: {{totales.valor_letras}}
            </div>
            {% endif %}

            {% if documento.observaciones %}
            <div class="observations">
                <strong>Observaciones:</strong><br>
                {{documento.observaciones}}
            </div>
            {% endif %}
        </div>

        <div class="totals-panel">
            <!-- SUBTOTAL -->
            <div class="total-line subtotal-line">
                <span class="total-label">Subtotal:</span>
                <span class="total-value">{{totales.subtotal}}</span>
            </div>

            <!-- DESCUENTOS -->
            {% if totales.descuentos and totales.descuentos != '0.00' %}
            <div class="total-line">
                <span class="total-label">Descuentos:</span>
                <span class="total-value">-{{totales.descuentos}}</span>
            </div>
            {% endif %}

            <!-- DISCRIMINACIÓN DE BASES GRAVABLES -->
            {% if totales.base_exenta and totales.base_exenta != '0.00' %}
            <div class="total-line base-line">
                <span class="total-label">Base Exenta (0%):</span>
                <span class="total-value">{{totales.base_exenta}}</span>
            </div>
            {% endif %}

            {% if totales.base_gravable_5 and totales.base_gravable_5 != '0.00' %}
            <div class="total-line base-line">
                <span class="total-label">Base Gravable (5%):</span>
                <span class="total-value">{{totales.base_gravable_5}}</span>
            </div>
            {% endif %}

            {% if totales.base_gravable_19 and totales.base_gravable_19 != '0.00' %}
            <div class="total-line base-line">
                <span class="total-label">Base Gravable (19%):</span>
                <span class="total-value">{{totales.base_gravable_19}}</span>
            </div>
            {% endif %}

            <!-- DISCRIMINACIÓN DE IMPUESTOS -->
            {% if totales.iva_5 and totales.iva_5 != '0.00' %}
            <div class="total-line tax-line">
                <span class="total-label">IVA (5%):</span>
                <span class="total-value">{{totales.iva_5}}</span>
            </div>
            {% endif %}

            {% if totales.iva_19 and totales.iva_19 != '0.00' %}
            <div class="total-line tax-line">
                <span class="total-label">IVA (19%):</span>
                <span class="total-value">{{totales.iva_19}}</span>
            </div>
            {% endif %}

            <!-- RETENCIONES -->
            {% if totales.retencion and totales.retencion != '0.00' %}
            <div class="total-line">
                <span class="total-label">Retención:</span>
                <span class="total-value">-{{totales.retencion}}</span>
            </div>
            {% endif %}

            <!-- TOTAL FINAL -->
            <div class="total-line">
                <span class="total-label">TOTAL A PAGAR:</span>
                <span class="total-value">{{totales.total}}</span>
            </div>
        </div>
    </div>

    <!-- PIE DE PÁGINA EMPRESARIAL -->
    <div class="footer-area">
        <div class="legal-notice">
            Esta factura se asimila en todos sus efectos a una letra de cambio de conformidad con el artículo 774 del
            Código de Comercio.
            Los pagos realizados después del vencimiento causarán intereses de mora según las tasas legales vigentes.
        </div>

        <div class="signature-grid">
            <div class="signature-field">
                <div class="signature-line">Elaboró</div>
            </div>
            <div class="signature-field">
                <div class="signature-line">Revisó</div>
            </div>
            <div class="signature-field">
                <div class="signature-line">Aprobó</div>
            </div>
            <div class="signature-field">
                <div class="signature-line">Recibí Conforme</div>
            </div>
        </div>

        <div class="footer-brand">
            Gracias por su confianza • Powered by ContaPY Enterprise
        </div>
    </div>
</body>

</html>

''',

    'reports/journal_report.html': r'''
﻿<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">
    <title>Libro Diario Detallado</title>
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

        .header h1,
        .header h2,
        .header p {
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
            margin-top: 15px;
            table-layout: fixed;
            /* CRITICAL FOR PERFORMANCE */
        }

        th,
        td {
            border: 1px solid #ccc;
            padding: 4px;
            /* Reduced padding for density */
            text-align: left;
            vertical-align: top;
            word-wrap: break-word;
            /* Ensure content wraps */
            overflow-wrap: break-word;
        }

        th {
            background-color: #f2f2f2;
            font-weight: bold;
            font-size: 9px;
        }

        td {
            font-size: 9px;
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
            background-color: #333;
            color: #fff;
            border-top: 2px solid #000;
        }

        .doc-subtotal-row td {
            background-color: #f9f9f9;
            font-weight: bold;
            font-style: italic;
            border-top: 1px solid #aaa;
        }
    </style>
</head>

<body>

    <div class="header">
        <h1>{{ empresa_nombre }}</h1>
        <h2>NIT: {{ empresa_nit }}</h2>
        <p><strong>Libro Diario Detallado</strong></p>
        <p>Desde el {{ fecha_inicio }} hasta el {{ fecha_fin }}</p>
    </div>

    <table>
        <colgroup>
            <col style="width: 12%"> <!-- Documento -->
            <col style="width: 20%"> <!-- Beneficiario -->
            <col style="width: 20%"> <!-- Cuenta -->
            <col style="width: 28%"> <!-- Concepto -->
            {% if has_cost_centers %}
            <col style="width: 20%"> <!-- Reduced Concepto if CC exists? -->
            <col style="width: 8%"> <!-- CC -->
            {% endif %}
            <col style="width: 10%"> <!-- Debito -->
            <col style="width: 10%"> <!-- Credito -->
        </colgroup>
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
            {% for date_group in report_data_structured %}
            <tr>
                <td colspan="{{ 7 if has_cost_centers else 6 }}" class="date-header">
                    Fecha: {{ date_group.fecha }}
                </td>
            </tr>

            {% for doc in date_group.documents %}
            {# --- Filas del Documento --- #}
            {% for mov in doc.rows %}
            <tr>
                <td>{{ doc.tipo_documento }}-{{ doc.numero_documento }}</td>
                <td>{{ doc.beneficiario_nombre or '' }}</td>
                <td>{{ mov.cuenta_codigo }} - {{ mov.cuenta_nombre }}</td>
                <td>{{ mov.concepto }}</td>
                {% if has_cost_centers %}
                <td>{{ mov.centro_costo_codigo or '' }}</td>
                {% endif %}
                <td class="text-right">{{ mov.debito | currency }}</td>
                <td class="text-right">{{ mov.credito | currency }}</td>
            </tr>
            {% endfor %}

            {# --- Subtotal del Documento --- #}
            <tr class="doc-subtotal-row">
                <td colspan="{{ 5 if has_cost_centers else 4 }}" class="text-right">
                    Subtotal {{ doc.tipo_documento }} #{{ doc.numero_documento }}:
                </td>
                <td class="text-right">{{ doc.total_debito | currency }}</td>
                <td class="text-right">{{ doc.total_credito | currency }}</td>
            </tr>
            {% endfor %}

            {% else %}
            <tr>
                <td colspan="{{ 7 if has_cost_centers else 6 }}" style="text-align:center;">No hay movimientos para el
                    período seleccionado.</td>
            </tr>
            {% endfor %}
        </tbody>

        <tfoot>
            <tr class="totals-row">
                <td colspan="{{ 5 if has_cost_centers else 4 }}" class="text-right"><strong>TOTAL GENERAL</strong></td>
                <td class="text-right"><strong>{{ total_debito | currency }}</strong></td>
                <td class="text-right"><strong>{{ total_credito | currency }}</strong></td>
            </tr>
        </tfoot>
    </table>

</body>

</html>

''',

    'reports/journal_summary_report.html': r'''
﻿<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">
    <title>Libro Diario Oficial</title>
    <style>
        @page {
            size: letter;
            margin: 2cm;

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
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
        }

        .header h1 {
            margin: 0;
            font-size: 16px;
        }

        .header h2 {
            margin: 5px 0;
            font-size: 14px;
            color: #555;
        }

        .table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            table-layout: fixed;
        }

        .table th,
        .table td {
            border: 1px solid #ccc;
            padding: 5px;
            vertical-align: top;
            word-wrap: break-word;
        }

        .table th {
            background-color: #f2f2f2;
            font-weight: bold;
            text-align: center;
        }

        .group-header td {
            background-color: #e0e0e0;
            font-weight: bold;
            font-size: 11px;
            text-transform: uppercase;
        }

        .total-row td {
            background-color: #f9f9f9;
            font-weight: bold;
            border-top: 2px solid #333;
        }

        .text-right {
            text-align: right;
        }

        .text-center {
            text-align: center;
        }

        .grand-total {
            margin-top: 30px;
            page-break-inside: avoid;
        }

        .grand-total table {
            border: 2px solid #333;
        }

        .grand-total td {
            font-size: 12px;
            font-weight: bold;
            background-color: #f2f2f2;
        }
    </style>
</head>

<body>
    <div class="header">
        <h1>{{ empresa_nombre }}</h1>
        <h2>NIT: {{ empresa_nit }}</h2>
        <p><strong>LIBRO DIARIO OFICIAL</strong></p>
        <p>Desde: {{ fecha_inicio }} Hasta: {{ fecha_fin }}</p>
    </div>

    {% for grupo in report_data %}
    <div style="page-break-inside: avoid;">
        <table class="table">
            <thead>
                <tr class="group-header">
                    <td colspan="4">COMPROBANTE: {{ grupo.tipo_documento }}</td>
                </tr>
                <tr>
                    <th style="width: 15%">Código</th>
                    <th style="width: 45%">Cuenta</th>
                    <th style="width: 20%">Débitos</th>
                    <th style="width: 20%">Créditos</th>
                </tr>
            </thead>
            <tbody>
                {% for cta in grupo.cuentas %}
                <tr>
                    <td>{{ cta.cuenta_codigo }}</td>
                    <td>{{ cta.cuenta_nombre }}</td>
                    <td class="text-right">{{ "${:,.2f}".format(cta.debito) }}</td>
                    <td class="text-right">{{ "${:,.2f}".format(cta.credito) }}</td>
                </tr>
                {% endfor %}
                <tr class="total-row">
                    <td colspan="2" class="text-right">Total {{ grupo.tipo_documento }}</td>
                    <td class="text-right">{{ "${:,.2f}".format(grupo.total_debito_grupo) }}</td>
                    <td class="text-right">{{ "${:,.2f}".format(grupo.total_credito_grupo) }}</td>
                </tr>
            </tbody>
        </table>
    </div>
    {% endfor %}

    <div class="grand-total">
        <table class="table">
            <tr>
                <td style="width: 60%; text-align: right;">GRAN TOTAL:</td>
                <td style="width: 20%; text-align: right;">{{ "${:,.2f}".format(gran_total_debito) }}</td>
                <td style="width: 20%; text-align: right;">{{ "${:,.2f}".format(gran_total_credito) }}</td>
            </tr>
        </table>
    </div>

</body>

</html>

''',

    'reports/kardex_report.html': r'''
﻿<!DOCTYPE html>
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
﻿<!DOCTYPE html>
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

        .header h1,
        .header h2,
        .header p {
            margin: 0;
            padding: 2px 0;
        }

        .account-block {
            margin-bottom: 25px;
            /* page-break-inside: avoid; REMOVED to allow splitting large tables */
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

        th,
        td {
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

    <table>
        <thead>
            <tr>
                <th style="width: 15%;">Código</th>
                <th style="width: 35%;">Cuenta</th>
                <th class="text-right" style="width: 12.5%;">Saldo Anterior</th>
                <th class="text-right" style="width: 12.5%;">Débitos</th>
                <th class="text-right" style="width: 12.5%;">Créditos</th>
                <th class="text-right" style="width: 12.5%;">Nuevo Saldo</th>
            </tr>
        </thead>
        <tbody>
            {% for cuenta in reporte.cuentas %}
            <tr>
                <td>{{ cuenta.cuenta_codigo }}</td>
                <td>{{ cuenta.cuenta_nombre }}</td>
                <td class="text-right">{{ "${:,.2f}".format(cuenta.saldo_inicial) }}</td>
                <td class="text-right">{{ "${:,.2f}".format(cuenta.total_debito) }}</td>
                <td class="text-right">{{ "${:,.2f}".format(cuenta.total_credito) }}</td>
                <td class="text-right">{{ "${:,.2f}".format(cuenta.nuevo_saldo) }}</td>
            </tr>
            {% else %}
            <tr>
                <td colspan="6" style="text-align: center;">No se encontraron movimientos ni saldos para el período
                    seleccionado.</td>
            </tr>
            {% endfor %}
        </tbody>
        <tfoot>
            <tr class="summary-row">
                <td colspan="3" class="text-right"><strong>Totales Generales:</strong></td>
                <td class="text-right"><strong>{{ "${:,.2f}".format(reporte.totales_generales.debito) }}</strong></td>
                <td class="text-right"><strong>{{ "${:,.2f}".format(reporte.totales_generales.credito) }}</strong></td>
                <td class="text-right"></td>
            </tr>
        </tfoot>
    </table>

</body>

</html>

''',

    'reports/movimiento_analitico_report.html': r'''
﻿<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">
    <title>Reporte Analítico de Movimientos</title>
    <style>
        body {
            font-family: sans-serif;
            font-size: 10px;
        }

        .header {
            text-align: center;
            margin-bottom: 20px;
        }

        .header h1 {
            margin: 0;
            font-size: 16px;
        }

        .header h2 {
            margin: 0;
            font-size: 12px;
            font-weight: normal;
        }

        .filters {
            margin-bottom: 15px;
            border-bottom: 1px solid #ccc;
            padding-bottom: 10px;
        }

        .filters p {
            margin: 2px 0;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }

        th,
        td {
            border: 1px solid #ddd;
            padding: 4px;
            text-align: left;
        }

        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }

        .text-right {
            text-align: right;
        }

        .number {
            font-family: monospace;
        }

        /* Para alinear números */
        .total-row {
            font-weight: bold;
            background-color: #e8e8e8;
        }

        .positive {
            color: green;
        }

        .negative {
            color: red;
        }
    </style>
</head>

<body>
    <div class="header">
        <h1>{{ empresa_nombre }}</h1>
        <h2>Reporte Analítico de Movimiento y Saldos</h2>
        <p>Periodo: {{ filtros.fecha_inicio }} al {{ filtros.fecha_fin }}</p>
    </div>

    <div class="filters">
        <p><strong>Filtros Aplicados:</strong></p>
        <p>Bodega: {{ bodega_nombre | default('Todas', true) }}</p>
        <p>Grupo: {{ grupo_nombre | default('Todos', true) }}</p>
        <p>Artículo: {{ producto_nombre | default('Todos', true) }}</p>
        <p>Vista por: {{ 'Valor' if filtros.vista_por_valor else 'Cantidad' }}</p>
    </div>

    <table>
        <thead>
            <tr>
                <th>Producto</th>
                <th class="text-right">Saldo Inicial {{ '(Valor)' if filtros.vista_por_valor else '(Cant)' }}</th>
                <th class="text-right">Entradas {{ '(Valor)' if filtros.vista_por_valor else '(Cant)' }}</th>
                <th class="text-right">Salidas {{ '(Valor)' if filtros.vista_por_valor else '(Cant)' }}</th>
                <th class="text-right">Saldo Final {{ '(Valor)' if filtros.vista_por_valor else '(Cant)' }}</th>
            </tr>
        </thead>
        <tbody>
            {% if data['items'] %}
            {% for item in data['items'] %}
            <tr>
                <td>({{ item.producto_codigo }}) {{ item.producto_nombre }}</td>
                <td class="text-right number">
                    {% if filtros.vista_por_valor %}
                    {{ item.saldo_inicial_valor | format_value(true) }}
                    {% else %}
                    {{ item.saldo_inicial_cantidad | format_value(false) }}
                    {% endif %}
                </td>
                <td class="text-right number positive">
                    {% if filtros.vista_por_valor %}
                    {{ item.total_entradas_valor | format_value(true) }}
                    {% else %}
                    {{ item.total_entradas_cantidad | format_value(false) }}
                    {% endif %}
                </td>
                <td class="text-right number negative">
                    {% if filtros.vista_por_valor %}
                    {{ item.total_salidas_valor | format_value(true) }}
                    {% else %}
                    {{ item.total_salidas_cantidad | format_value(false) }}
                    {% endif %}
                </td>
                <td class="text-right number">
                    {% if filtros.vista_por_valor %}
                    {{ item.saldo_final_valor | format_value(true) }}
                    {% else %}
                    {{ item.saldo_final_cantidad | format_value(false) }}
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
            {% else %}
            <tr>
                <td colspan="5" style="text-align: center; font-style: italic;">No se encontraron resultados para los
                    filtros seleccionados.</td>
            </tr>
            {% endif %}
        </tbody>
        {% if data['items'] %}
        <tfoot class="total-row">
            <tr>
                <td>TOTALES GENERALES ({{ 'Valor' if filtros.vista_por_valor else 'Cantidad' }})</td>
                <td class="text-right number">
                    {% if filtros.vista_por_valor %}
                    {{ data.totales.saldo_inicial_valor | format_value(true) }}
                    {% else %}
                    {{ data.totales.saldo_inicial_cantidad | format_value(false) }}
                    {% endif %}
                </td>
                <td class="text-right number positive">
                    {% if filtros.vista_por_valor %}
                    {{ data.totales.total_entradas_valor | format_value(true) }}
                    {% else %}
                    {{ data.totales.total_entradas_cantidad | format_value(false) }}
                    {% endif %}
                </td>
                <td class="text-right number negative">
                    {% if filtros.vista_por_valor %}
                    {{ data.totales.total_salidas_valor | format_value(true) }}
                    {% else %}
                    {{ data.totales.total_salidas_cantidad | format_value(false) }}
                    {% endif %}
                </td>
                <td class="text-right number">
                    {% if filtros.vista_por_valor %}
                    {{ data.totales.saldo_final_valor | format_value(true) }}
                    {% else %}
                    {{ data.totales.saldo_final_cantidad | format_value(false) }}
                    {% endif %}
                </td>
            </tr>
        </tfoot>
        {% endif %}
    </table>

    {# Filtro personalizado de Jinja2 para formatear números/moneda #}
    {% macro format_value(num, is_currency) %}
    {% if is_currency %}
    {{ "$ {:,.0f}".format(num | float) }}
    {% else %}
    {{ "{:,.2f}".format(num | float) }}
    {% endif %}
    {% endmacro %}
</body>

</html>

''',

    'reports/premium_fe_template.html': r'''
﻿<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">
    <title>Factura Electrónica de Venta Premium</title>
    <style>
        /* RESET & BASE */
        * {
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, sans-serif;
            color: #1e293b;
            font-size: 10px;
            margin: 0;
            padding: 10px 15px;
            line-height: 1.4;
            background: #ffffff;
        }

        @page {
            size: letter;
            margin: 1.5cm 1.5cm;
        }

        /* TIPOGRAFÍA & UTILIDADES */
        .text-right {
            text-align: right;
        }

        .text-center {
            text-align: center;
        }

        .text-bold {
            font-weight: 700;
        }

        .text-uppercase {
            text-transform: uppercase;
        }

        .text-primary {
            color: #0f172a;
        }

        .text-secondary {
            color: #64748b;
        }

        .text-brand {
            color: #2563eb;
        }

        .text-danger {
            color: #f43f5e;
        }

        /* Modern rose-red */

        /* CABEZOTE: Glassmorphism / Modern Layout */
        .header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 25px;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 20px;
        }

        .header-left {
            width: 55%;
        }

        .logo-placeholder {
            max-width: 160px;
            max-height: 60px;
            margin-bottom: 12px;
        }

        .emisor-name {
            font-size: 16px;
            font-weight: 900;
            color: #0f172a;
            margin-bottom: 4px;
            letter-spacing: -0.5px;
            text-transform: uppercase;
        }

        .emisor-nit {
            font-size: 10px;
            font-weight: 700;
            color: #3b82f6;
            margin-bottom: 6px;
        }

        .emisor-details {
            font-size: 9px;
            color: #475569;
            line-height: 1.5;
        }

        /* BLOQUE TIPO DOCUMENTO DERECHA */
        .header-right {
            width: 40%;
            text-align: right;
            border-left: 1px solid #e2e8f0;
            padding-left: 20px;
        }

        .doc-title {
            font-size: 14px;
            font-weight: 900;
            color: #1e40af;
            text-transform: uppercase;
            margin-bottom: 4px;
            letter-spacing: -0.5px;
        }

        .doc-number {
            font-size: 20px;
            font-weight: 900;
            color: #f43f5e;
            margin-bottom: 12px;
            font-family: 'SF Mono', 'Monaco', monospace;
            letter-spacing: -0.5px;
        }

        .doc-meta {
            display: grid;
            grid-template-columns: 1fr 1fr;
            text-align: right;
            row-gap: 6px;
            font-size: 9px;
            column-gap: 10px;
        }

        .meta-label {
            color: #64748b;
            font-weight: 700;
            text-transform: uppercase;
            font-size: 8px;
        }

        .meta-value {
            color: #0f172a;
            font-weight: 800;
        }

        /* INFORMACIÓN ADQUIRENTE (CARD MODERNO) */
        .adquirente-section {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 15px 20px;
            margin-bottom: 25px;
            display: flex;
            justify-content: space-between;
        }

        .adquirente-col {
            width: 48%;
        }

        .adq-label {
            font-size: 8px;
            text-transform: uppercase;
            color: #3b82f6;
            font-weight: 900;
            margin-bottom: 6px;
            letter-spacing: 0.5px;
        }

        .adq-name {
            font-size: 13px;
            font-weight: 900;
            color: #0f172a;
            margin-bottom: 8px;
            text-transform: uppercase;
        }

        .adq-detail-row {
            display: flex;
            margin-bottom: 4px;
            font-size: 9px;
        }

        .adq-detail-label {
            width: 35%;
            color: #64748b;
            font-weight: 700;
        }

        .adq-detail-value {
            width: 65%;
            color: #1e293b;
            font-weight: 700;
        }

        /* DETALLE DE PRODUCTOS (TABLA MODERNA) */
        .items-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin-bottom: 25px;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            overflow: hidden;
        }

        .items-table th {
            background-color: #f8fafc;
            color: #475569;
            font-size: 8px;
            text-transform: uppercase;
            padding: 10px 12px;
            font-weight: 800;
            border-bottom: 1px solid #e2e8f0;
            letter-spacing: 0.5px;
        }

        .items-table td {
            padding: 10px 12px;
            border-bottom: 1px solid #f1f5f9;
            vertical-align: middle;
            background: #ffffff;
        }

        .items-table tbody tr:last-child td {
            border-bottom: none;
        }

        .item-code {
            font-family: 'SF Mono', 'Monaco', monospace;
            font-size: 8px;
            color: #94a3b8;
            font-weight: 700;
        }

        .item-name {
            font-weight: 700;
            color: #1e293b;
            font-size: 9px;
        }

        .item-number {
            font-family: 'SF Mono', 'Monaco', monospace;
            font-size: 9px;
            font-weight: 700;
            color: #334155;
        }

        /* ZONA DE TOTALES Y OBSERVACIONES */
        .bottom-section {
            display: flex;
            justify-content: space-between;
            margin-bottom: 25px;
        }

        .notes-section {
            width: 55%;
        }

        .amount-words-box {
            background: #f0fdf4;
            /* Verde muy claro indicando éxito / pago */
            border-left: 4px solid #22c55e;
            padding: 12px 15px;
            border-radius: 0 6px 6px 0;
            margin-bottom: 15px;
        }

        .amount-words-label {
            font-size: 8px;
            color: #166534;
            font-weight: 900;
            text-transform: uppercase;
            margin-bottom: 4px;
        }

        .amount-words-value {
            font-size: 9px;
            color: #15803d;
            font-weight: 800;
        }

        .obs-box {
            background: #ffffff;
            border: 1px dashed #cbd5e1;
            padding: 12px 15px;
            border-radius: 6px;
        }

        .obs-label {
            font-size: 8px;
            color: #64748b;
            font-weight: 900;
            text-transform: uppercase;
            margin-bottom: 4px;
        }

        .obs-text {
            font-size: 9px;
            color: #334155;
            white-space: pre-line;
            font-weight: 500;
        }

        .totales-section {
            width: 40%;
        }

        .totales-table {
            width: 100%;
            border-collapse: collapse;
        }

        .totales-table td {
            padding: 8px 12px;
            font-size: 10px;
            border-bottom: 1px solid #f8fafc;
        }

        .total-label-cell {
            color: #64748b;
            font-weight: 700;
            text-transform: uppercase;
            font-size: 8px;
        }

        .total-value-cell {
            text-align: right;
            font-weight: 800;
            font-family: 'SF Mono', 'Monaco', monospace;
            color: #1e293b;
        }

        .row-base td {
            background: #f8fafc;
            color: #1e293b;
        }

        .row-tax td {
            background: #fdf2f8;
            color: #be185d;
        }

        .row-grand-total td {
            background: #1e40af;
            /* Azul vibrante premium */
            color: #ffffff;
            font-size: 14px;
            font-weight: 900;
            border-bottom: none;
            padding: 15px 12px;
            border-radius: 0 0 8px 8px;
            /* Si fuera el final de un contenedor contiguo, asumamos borde redondeado inferior */
        }

        .row-grand-total .total-label-cell {
            color: #bfdbfe;
            font-size: 10px;
        }

        .row-grand-total .total-value-cell {
            color: #ffffff;
        }

        .totales-wrapper {
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            overflow: hidden;
        }

        /* SECCIÓN FACTURACIÓN ELECTRÓNICA DIAN */
        /* Hacemos este bloque VISUALMENTE IMPECABLE para que el usuario no tenga quejas */
        .fe-dian-section {
            margin-top: 30px;
            border: 1px solid #cbd5e1;
            border-top: 4px solid #10b981;
            /* Verde esmeralda DIAN Aceptado */
            border-radius: 8px;
            display: flex;
            padding: 20px;
            background: #ffffff;
            page-break-inside: avoid;
        }

        .fe-qr-col {
            width: 25%;
            display: flex;
            justify-content: center;
            align-items: center;
            border-right: 1px solid #e2e8f0;
            padding-right: 20px;
        }

        .qr-placeholder {
            width: 140px;
            height: 140px;
            object-fit: contain;
        }

        .qr-fallback {
            width: 140px;
            height: 140px;
            background: #f8fafc;
            border: 1px dashed #cbd5e1;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #94a3b8;
            font-size: 10px;
            text-align: center;
            padding: 10px;
            border-radius: 8px;
        }

        .fe-info-col {
            width: 75%;
            padding-left: 25px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .fe-title {
            font-size: 12px;
            font-weight: 900;
            color: #047857;
            /* Verde DIAN oscuro */
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .fe-cufe-box {
            background: #f1f5f9;
            padding: 10px 15px;
            border-radius: 6px;
            border: 1px solid #e2e8f0;
            margin-bottom: 12px;
        }

        .fe-cufe-label {
            font-size: 8px;
            color: #64748b;
            font-weight: 900;
            text-transform: uppercase;
            margin-bottom: 4px;
            letter-spacing: 0.5px;
        }

        .fe-cufe-value {
            font-family: 'SF Mono', 'Monaco', monospace;
            font-size: 9px;
            font-weight: 700;
            color: #1e293b;
            word-break: break-all;
            line-height: 1.4;
        }

        .fe-legal-text {
            font-size: 8px;
            color: #64748b;
            line-height: 1.5;
            text-align: justify;
            font-weight: 500;
        }

        /* PIE DE PÁGINA */
        .commercial-footer {
            margin-top: 30px;
            text-align: center;
            font-size: 8px;
            color: #94a3b8;
            border-top: 1px solid #f1f5f9;
            padding-top: 15px;
            font-weight: 600;
        }
    </style>
</head>

<body>

    <!-- CABECERA DE LA FACTURA -->
    <div class="header">
        <div class="header-left">
            {% if empresa.logo_url %}
            <img src="{{empresa.logo_url}}" class="logo-placeholder" alt="Logo {{empresa.razon_social}}">
            {% endif %}
            <div class="emisor-name">{{empresa.razon_social}}</div>
            <div class="emisor-nit">NIT: {{empresa.nit}}</div>
            <div class="emisor-details">
                {{empresa.direccion}}<br>
                Teléfono: {{empresa.telefono}} {% if empresa.email %}| Correo: {{empresa.email}}{% endif %}<br>
                <strong style="color:#0f172a;">Responsabilidad Tributaria:</strong> IVA Régimen Común
            </div>
        </div>

        <div class="header-right">
            <div class="doc-title">Factura Electrónica de Venta</div>
            <div class="doc-number">N° {{documento.consecutivo}}</div>
            <div class="doc-meta">
                <div class="meta-label">Fecha Emisión:</div>
                <div class="meta-value">{{documento.fecha_emision}}</div>

                <div class="meta-label">Fecha Venc.:</div>
                <div class="meta-value">{{documento.fecha_vencimiento}}</div>
            </div>
        </div>
    </div>

    <!-- DATOS DEL ADQUIRENTE (CLIENTE) -->
    <div class="adquirente-section">
        <div class="adquirente-col">
            <div class="adq-label">Adquirente (Cliente)</div>
            <div class="adq-name">{{tercero.razon_social}}</div>

            <div class="adq-detail-row">
                <div class="adq-detail-label">NIT / CC:</div>
                <div class="adq-detail-value">{{tercero.nit}}</div>
            </div>
        </div>
        <div class="adquirente-col">
            <div class="adq-detail-row" style="margin-top: 18px;">
                <div class="adq-detail-label">Dirección:</div>
                <div class="adq-detail-value">{{tercero.direccion|default('No registrada')}}</div>
            </div>
            <div class="adq-detail-row">
                <div class="adq-detail-label">Teléfono:</div>
                <div class="adq-detail-value">{{tercero.telefono|default('No registrado')}}</div>
            </div>
        </div>
    </div>

    <!-- DETALLE DE ITEMS -->
    <table class="items-table">
        <thead>
            <tr>
                <th width="12%" class="text-left">Código</th>
                <th width="40%" class="text-left">Descripción del Producto o Servicio</th>
                <th width="8%" class="text-center">Cant.</th>
                <th width="15%" class="text-right">Vr. Unitario</th>
                <th width="8%" class="text-right">IVA</th>
                <th width="17%" class="text-right">Valor Total</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr>
                <td class="item-code">{{item.producto_codigo}}</td>
                <td class="item-name">{{item.producto_nombre}}</td>
                <td class="text-center item-number" style="color:#2563eb;">{{item.cantidad}}</td>
                <td class="text-right item-number">{{item.precio_unitario}}</td>
                <td class="text-right item-number">{{ (item.tasa_iva * 100)|round(0) if item.tasa_iva else 0 }}%</td>
                <td class="text-right item-number">{{item.subtotal}}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <!-- TOTALES Y REEMBOLSOS -->
    <div class="bottom-section">
        <div class="notes-section">
            {% if totales.valor_letras %}
            <div class="amount-words-box">
                <div class="amount-words-label">Valor en letras</div>
                <div class="amount-words-value">SON: {{totales.valor_letras}}</div>
            </div>
            {% endif %}

            {% if documento.observaciones %}
            <div class="obs-box">
                <div class="obs-label">Observaciones Adicionales</div>
                <div class="obs-text">{{documento.observaciones}}</div>
            </div>
            {% endif %}
        </div>

        <div class="totales-section">
            <div class="totales-wrapper">
                <table class="totales-table">
                    <tr>
                        <td class="total-label-cell">Subtotal Neto:</td>
                        <td class="total-value-cell">{{totales.subtotal}}</td>
                    </tr>

                    {% if totales.base_exenta and totales.base_exenta != '0.00' %}
                    <tr class="row-base">
                        <td class="total-label-cell">Base Exenta (0%):</td>
                        <td class="total-value-cell">{{totales.base_exenta}}</td>
                    </tr>
                    {% endif %}

                    {% if totales.base_gravable_5 and totales.base_gravable_5 != '0.00' %}
                    <tr class="row-base">
                        <td class="total-label-cell">Base Gravable (5%):</td>
                        <td class="total-value-cell">{{totales.base_gravable_5}}</td>
                    </tr>
                    {% endif %}

                    {% if totales.base_gravable_19 and totales.base_gravable_19 != '0.00' %}
                    <tr class="row-base">
                        <td class="total-label-cell">Base Gravable (19%):</td>
                        <td class="total-value-cell">{{totales.base_gravable_19}}</td>
                    </tr>
                    {% endif %}

                    {% if totales.iva_5 and totales.iva_5 != '0.00' %}
                    <tr class="row-tax">
                        <td class="total-label-cell" style="color:#be185d;">Impuesto IVA (5%):</td>
                        <td class="total-value-cell" style="color:#be185d;">{{totales.iva_5}}</td>
                    </tr>
                    {% endif %}

                    {% if totales.iva_19 and totales.iva_19 != '0.00' %}
                    <tr class="row-tax">
                        <td class="total-label-cell" style="color:#be185d;">Impuesto IVA (19%):</td>
                        <td class="total-value-cell" style="color:#be185d;">{{totales.iva_19}}</td>
                    </tr>
                    {% endif %}

                    <tr class="row-grand-total">
                        <td class="total-label-cell">TOTAL A PAGAR:</td>
                        <td class="total-value-cell">{{totales.total}}</td>
                    </tr>
                </table>
            </div>
        </div>
    </div>

    <!-- BLOQUE DIAN - FACTURACIÓN ELECTRÓNICA -->
    <!-- Mostrar SIEMPRE Si existe CUFE para garantizar visibilidad de la validación -->
    {% if documento.dian_cufe %}
    <div class="fe-dian-section">
        <div class="fe-qr-col">
            <!-- Usamos goqr.me para crear un QR que apunte a la URL oficial de escaneo de la DIAN -->
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=https://catalogo-vpfe-hab.dian.gov.co/document/searchqr?documentkey={{documento.dian_cufe}}"
                class="qr-placeholder" alt="QR DIAN Sandbox">
        </div>
        <div class="fe-info-col">
            <div class="fe-title">✓ Documento Electrónico DIAN</div>

            <div class="fe-cufe-box">
                <div class="fe-cufe-label">CUFE (Código Único de Facturación Electrónica):</div>
                <div class="fe-cufe-value">{{documento.dian_cufe}}</div>
            </div>

            <div class="fe-legal-text">
                Autorización Numeración Facturación Electrónica DIAN NO.
                <strong>{{documento.resolucion_numero}}</strong> de fecha
                <strong>{{documento.resolucion_fecha}}</strong>.
                Rango desde <strong>{{documento.resolucion_prefijo}}-{{documento.resolucion_rango_desde}}</strong> hasta
                <strong>{{documento.resolucion_prefijo}}-{{documento.resolucion_rango_hasta}}</strong>.
                Esta factura se asimila en todos sus efectos a una letra de cambio según el Art. 774 del Código de
                Comercio.
                Transcurridos 3 días hábiles desde su recepción, si no hay reclamación en contra, se entenderá aceptada
                y constituirá título ejecutivo.
            </div>


        </div>
    </div>
    {% endif %}

    <div class="commercial-footer">
        Finaxis Enterprise Software - Sistema Integral de Facturación Electrónica DIAN
    </div>

</body>

</html>

''',

    'reports/purchases_detailed.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Informe Detallado de Compras</title>
    <style>
        @page {
            size: letter landscape;
            margin: 1cm;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 8px;
            color: #333;
            margin: 0;
            padding: 0;
        }
        .header {
            text-align: center;
            border-bottom: 2px solid #2c3e50;
            padding-bottom: 10px;
            margin-bottom: 15px;
        }
        .header h1 {
            margin: 0;
            font-size: 16px;
            color: #2c3e50;
            text-transform: uppercase;
        }
        .header h2 {
            margin: 5px 0;
            font-size: 12px;
            color: #7f8c8d;
        }
        .header .info {
            font-size: 9px;
            margin-top: 5px;
        }
        .filters-summary {
            background-color: #f8f9fa;
            padding: 8px;
            border-radius: 4px;
            margin-bottom: 15px;
            border-left: 4px solid #3498db;
        }
        .filters-summary span {
            font-weight: bold;
            margin-right: 15px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th {
            background-color: #2c3e50;
            color: white;
            padding: 6px 4px;
            text-align: left;
            text-transform: uppercase;
            font-size: 7px;
        }
        td {
            padding: 5px 4px;
            border-bottom: 1px solid #ecf0f1;
        }
        .text-right { text-align: right; }
        .text-center { text-align: center; }
        .font-bold { font-weight: bold; }
        
        tr:nth-child(even) { background-color: #fdfdfd; }
        
        .totals-section {
            float: right;
            width: 250px;
            margin-top: 10px;
        }
        .totals-table {
            width: 100%;
        }
        .totals-table td {
            padding: 4px;
            border: none;
        }
        .totals-table .label {
            text-align: right;
            padding-right: 15px;
            font-weight: bold;
            color: #7f8c8d;
        }
        .totals-table .value {
            text-align: right;
            font-size: 10px;
            border-bottom: 1px solid #bdc3c7;
        }
        .grand-total {
            background-color: #2c3e50;
            color: white !important;
            font-weight: bold;
        }
        
        .footer {
            position: fixed;
            bottom: 0;
            width: 100%;
            text-align: center;
            font-size: 7px;
            color: #95a5a6;
            border-top: 1px solid #ecf0f1;
            padding-top: 5px;
        }
        
        .negative { color: #e74c3c; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ empresa.razon_social }}</h1>
        <div class="info">
            NIT: {{ empresa.nit }} | Tel: {{ empresa.telefono or 'N/A' }} | Email: {{ empresa.email or 'N/A' }}
        </div>
        <h2>INFORME ESPECIALIZADO DE COMPRAS DETALLADO</h2>
        <div class="info">
            Período: <strong>{{ filtros.fecha_inicio }}</strong> hasta <strong>{{ filtros.fecha_fin }}</strong>
        </div>
    </div>

    <div class="filters-summary">
        <span>Filtros Aplicados:</span>
        {% if filtros.proveedor_id %} <strong>Proveedor:</strong> {{ filtros_nombres.proveedor }} {% endif %}
        {% if filtros.producto_id %} <strong>Producto:</strong> {{ filtros_nombres.producto }} {% endif %}
        {% if filtros.centro_costo_id %} <strong>Centro Costo:</strong> {{ filtros_nombres.centro_costo }} {% endif %}
        {% if filtros.bodega_id %} <strong>Bodega:</strong> {{ filtros_nombres.bodega }} {% endif %}
        {% if not filtros.proveedor_id and not filtros.producto_id and not filtros.centro_costo_id and not filtros.bodega_id %}
            Ninguno adicional
        {% endif %}
    </div>

    <table>
        <thead>
            <tr>
                <th width="8%">Fecha</th>
                <th width="12%">Documento</th>
                <th width="16%">Proveedor</th>
                <th width="16%">Producto</th>
                <th width="8%">Bodega</th>
                <th width="8%">C. Costo</th>
                <th width="6%" class="text-right">CANT</th>
                <th width="8%" class="text-right">V/U</th>
                <th width="8%" class="text-right">Subtotal</th>
                <th width="5%" class="text-right">IVA</th>
                <th width="5%" class="text-right">Total</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr>
                <td>{{ item.fecha }}</td>
                <td class="font-bold">
                    {{ (item.tipo_documento_nombre[:2] | upper) if item.tipo_documento_nombre else 'FC' }}-{{ item.numero }}
                </td>
                <td>{{ item.proveedor_nombre }}</td>
                <td class="font-bold">{{ item.producto_nombre }}</td>
                <td>{{ item.bodega_nombre or '-' }}</td>
                <td>{{ item.centro_costo_nombre or '-' }}</td>
                <td class="text-right {{ 'negative' if item.cantidad < 0 else '' }}">
                    {{ "{:,.2f}".format(item.cantidad) }}
                </td>
                <td class="text-right">$ {{ "{:,.2f}".format(item.valor_unitario) }}</td>
                <td class="text-right {{ 'negative' if item.subtotal < 0 else '' }}">
                    $ {{ "{:,.2f}".format(item.subtotal) }}
                </td>
                <td class="text-right {{ 'negative' if item.iva < 0 else '' }}">
                    $ {{ "{:,.2f}".format(item.iva) }}
                </td>
                <td class="text-right font-bold {{ 'negative' if item.total < 0 else '' }}">
                    $ {{ "{:,.2f}".format(item.total) }}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <div style="page-break-inside: avoid;">
        <div style="width: 48%; float: left;">
            <h3 style="font-size: 10px; color: #2c3e50; border-left: 3px solid #3498db; padding-left: 5px;">TOP 5 PROVEEDORES</h3>
            <table style="font-size: 7px;">
                {% set max_prov = graficos.top_proveedores[0].value if graficos.top_proveedores else 1 %}
                {% for p in graficos.top_proveedores %}
                <tr>
                    <td width="40%">{{ p.label }}</td>
                    <td width="60%">
                        <div style="background-color: #3498db; width: {{ (p.value / max_prov * 100)|round }}%; height: 8px; border-radius: 2px;"></div>
                        <span style="font-size: 6px;">$ {{ "{:,.0f}".format(p.value) }}</span>
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
        <div style="width: 48%; float: right;">
            <h3 style="font-size: 10px; color: #2c3e50; border-left: 3px solid #e74c3c; padding-left: 5px;">TOP 5 PRODUCTOS</h3>
            <table style="font-size: 7px;">
                {% set max_prod = graficos.top_productos[0].value if graficos.top_productos else 1 %}
                {% for p in graficos.top_productos %}
                <tr>
                    <td width="40%">{{ p.label }}</td>
                    <td width="60%">
                        <div style="background-color: #e74c3c; width: {{ (p.value / max_prod * 100)|round }}%; height: 8px; border-radius: 2px;"></div>
                        <span style="font-size: 6px;">$ {{ "{:,.0f}".format(p.value) }}</span>
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
        <div style="clear: both;"></div>
    </div>

    <div class="totals-section" style="page-break-inside: avoid; margin-top: 20px;">
        <table class="totals-table">
            <tr>
                <td class="label">SUBTOTAL BASE:</td>
                <td class="value {{ 'negative' if total_base < 0 else '' }}">
                    $ {{ "{:,.2f}".format(total_base) }}
                </td>
            </tr>
            <tr>
                <td class="label">IVA TOTAL:</td>
                <td class="value {{ 'negative' if total_iva < 0 else '' }}">
                    $ {{ "{:,.2f}".format(total_iva) }}
                </td>
            </tr>
            <tr class="grand-total">
                <td class="label" style="color: white;">COMPRAS NETAS:</td>
                <td class="value" style="border-bottom: none;">
                    $ {{ "{:,.2f}".format(total_general) }}
                </td>
            </tr>
        </table>
    </div>

    <div class="footer">
        Generado por Finaxis ERP el {{ fecha_generacion }} | Página 1
    </div>
</body>
</html>

''',

    'reports/rentabilidad_documento_report.html': r'''
﻿<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Rentabilidad por Documento</title>
    <style>
        body { font-family: Arial, sans-serif; font-size: 10pt; }
        .header { text-align: center; margin-bottom: 20px; }
        .header h1 { font-size: 16pt; margin-bottom: 5px; }
        .header p { font-size: 10pt; margin: 0; }
        .info-box { border: 1px solid #ddd; padding: 10px; margin-bottom: 15px; border-radius: 5px; background-color: #f9f9f9; }
        .info-box p { margin: 3px 0; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #eee; font-weight: bold; }
        .right { text-align: right; }
        .mono { font-family: 'Courier New', monospace; }
        .footer { margin-top: 30px; border-top: 1px solid #ccc; padding-top: 10px; font-size: 9pt; }
        .totals-row td { font-weight: bold; background-color: #e0e0e0; }
        .negative { color: red; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ empresa.razon_social }}</h1>
        <p>NIT: {{ empresa.nit }}</p>
        <p>Reporte Generado: {{ now()|date("d/m/Y H:i") }}</p>
    </div>

    <div class="header-section">
        <h1>Análisis de Rentabilidad por Documento</h1>
    </div>

    <div class="info-box">
        <p><strong>Documento Auditado:</strong> {{ data.documento_ref }}</p>
        <p><strong>Tercero:</strong> {{ data.tercero_nombre }}</p>
        <p><strong>Fecha de Documento:</strong> {{ data.fecha|date("d/m/Y") }}</p>
        <p><strong>Filtro Usado:</strong> Código {{ filtros.tipo_documento_codigo|default('N/A') }} y Número {{ filtros.numero_documento|default('N/A') }}</p>
    </div>

    <table>
        <thead>
            <tr>
                <th style="width: 15%;">CÓDIGO</th>
                <th style="width: 25%;">ARTÍCULO</th>
                <th class="right" style="width: 8%;">CANT.</th>
                <th class="right" style="width: 10%;">VTA. UNIT.</th>
                <th class="right" style="width: 10%;">COSTO UNIT.</th>
                <th class="right" style="width: 10%;">VTA. TOTAL</th>
                <th class="right" style="width: 10%;">COSTO TOTAL</th>
                <th class="right" style="width: 10%;">UTILIDAD BRUTA</th>
                <th class="right" style="width: 7%;">MARGEN %</th>
            </tr>
        </thead>
        <tbody>
            {% for item in data.detalle %}
            <tr class="{% if item.utilidad_bruta_valor|default(0) < 0 %}negative{% endif %}">
                <td class="mono">{{ item.producto_codigo }}</td>
                <td>{{ item.producto_nombre }}</td>
                <td class="right mono">{{ item.cantidad|format_decimal(2) }}</td>
                <td class="right mono">{{ item.valor_venta_unitario|format_currency }}</td>
                <td class="right mono">{{ item.costo_unitario|format_currency }}</td>
                <td class="right mono">{{ item.valor_venta_total|format_currency }}</td>
                <td class="right mono">{{ item.costo_total|format_currency }}</td>
                <td class="right mono">{{ item.utilidad_bruta_valor|format_currency }}</td>
                <td class="right mono">{{ item.utilidad_bruta_porcentaje|format_decimal(2) }}%</td>
            </tr>
            {% endfor %}
            {% if not data.detalle %}
            <tr>
                <td colspan="9" style="text-align: center;">No se encontraron movimientos de inventario de venta para este documento.</td>
            </tr>
            {% endif %}
        </tbody>
        <tfoot>
            <tr class="totals-row">
                <td colspan="5" class="right">TOTALES ACUMULADOS:</td>
                <td class="right mono">{{ data.totales.total_venta|default(0)|format_currency }}</td>
                <td class="right mono">{{ data.totales.total_costo|default(0)|format_currency }}</td>
                <td class="right mono">{{ data.totales.total_utilidad_bruta_valor|default(0)|format_currency }}</td>
                <td class="right mono">{{ data.totales.total_utilidad_bruta_porcentaje|default(0)|format_decimal(2) }}%</td>
            </tr>
        </tfoot>
    </table>

    <div class="footer">
        <p>Fin del reporte de Rentabilidad por Documento.</p>
        <p>Sistema Contable Finaxis.</p>
    </div>
</body>
</html>

''',

    'reports/rentabilidad_factura_report.html': r'''
﻿<!DOCTYPE html>
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
﻿<!DOCTYPE html>
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
﻿<!DOCTYPE html>
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
﻿<!DOCTYPE html>
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
﻿<!DOCTYPE html>
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
﻿<!DOCTYPE html>
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
﻿<!DOCTYPE html>
<html lang="es">

<head>
    <title>Auditoría Contable Avanzada</title>
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

        h1,
        h2 {
            margin: 0;
        }

        h1 {
            font-size: 14px;
        }

        h2 {
            font-size: 12px;
            font-weight: normal;
        }

        .report-info {
            margin-bottom: 15px;
            font-size: 9px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th,
        td {
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

        .text-right {
            text-align: right;
        }

        .text-center {
            text-align: center;
        }

        /* Estilos para filas basados en el estado pre-procesado */
        .ANULADO {
            background-color: #fffbe6;
        }

        .ELIMINADO {
            background-color: #ffebee;
        }

        /* Se eliminó el tachado */

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
        {% if column_widths %}
        <colgroup>
            {% for width in column_widths %}
            <col style="width: {{ width }}">
            {% endfor %}
        </colgroup>
        {% endif %}
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
                <td colspan="{{ headers|length }}">No se encontraron resultados que coincidan con los criterios de
                    búsqueda.</td>
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
﻿<!DOCTYPE html>
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

        h1,
        h2 {
            margin: 0;
        }

        h1 {
            font-size: 14px;
        }

        h2 {
            font-size: 12px;
            font-weight: normal;
        }

        .report-info {
            margin-bottom: 15px;
            font-size: 9px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th,
        td {
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

        .text-right {
            text-align: right;
        }

        .text-center {
            text-align: center;
        }

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

            <tr class="total-global-row" style="background-color: #f1f5f9;">
                <td colspan="{{ 4 if has_cost_centers else 3 }}"><strong>TOTALES MOVIMIENTOS DEL PERIODO</strong></td>
                <td class="text-right"><strong>{{ "{:,.2f}".format(total_debito_global) }}</strong></td>
                <td class="text-right"><strong>{{ "{:,.2f}".format(total_credito_global) }}</strong></td>
                <td></td>
            </tr>

            <tr class="total-global-row" style="background-color: #1e293b; color: white;">
                <td colspan="{{ 6 if has_cost_centers else 5 }}"><strong>SALDO FINAL GLOBAL AL {{ fecha_fin }}</strong>
                </td>
                {% set saldo_final_global = (movimientos[-1].saldo_parcial if movimientos else saldo_anterior_global) %}
                <td class="text-right"><strong>{{ "{:,.2f}".format(saldo_final_global) }}</strong></td>
            </tr>
        </tbody>
    </table>
</body>

</html>

''',

    'reports/topes_inventario_report.html': r'''
﻿<!DOCTYPE html>
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

}
