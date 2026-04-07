# -*- coding: utf-8 -*-
# Â¡Â¡Â¡ ARCHIVO AUTO-GENERADO !!!
# No editar este archivo manualmente. Ejecutar precompile_templates.py para actualizar.

TEMPLATES_EMPAQUETADOS = {
    'reports/account_ledger_report.html': r'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Auxiliar por Cuenta</title>
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=DM+Sans:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --green-inst: #1C3A18;
            --green-light: #2D5A27;
            --gold-soft: #C9A84C;
            --white: #FFFFFF;
            --bg-page: #FAFAF7;
            --text-main: #1C3A18;
            --text-muted: #666666;
            --text-labels: #444444;
            --bg-grand-total: #F2F5F1;
            --bg-accent: #FAFAF7;
            --negative: #B22222;
        }

        @page {
            size: A4 landscape;
            margin: 0;
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
            width: 297mm;
            height: 210mm;
            margin: 0 auto;
            position: relative;
            box-sizing: border-box;
            overflow: hidden;
            background-color: var(--white);
        }

        .decor-bar-top {
            height: 6px;
            background: linear-gradient(90deg, var(--green-inst), var(--green-light), var(--gold-soft), var(--green-light), var(--green-inst));
            width: 100%;
        }

        .decor-bar-bottom {
            height: 4px;
            background: linear-gradient(90deg, var(--green-inst), var(--gold-soft));
            width: 100%;
            position: absolute;
            bottom: 0;
        }

        header {
            padding: 35px 50px 20px 50px;
            display: table;
            width: 100%;
            box-sizing: border-box;
        }

        .header-left { display: table-cell; vertical-align: middle; text-align: left; }
        .header-right { display: table-cell; vertical-align: middle; text-align: right; }

        .badge-premium {
            font-size: 9px;
            font-weight: 700;
            color: var(--green-inst);
            text-transform: uppercase;
            letter-spacing: 2.5px;
            margin-bottom: 5px;
            display: block;
        }
        .badge-premium::before { content: "â€¢"; margin-right: 8px; color: var(--gold-soft); }

        .company-name {
            font-family: 'Cormorant Garamond', serif;
            font-size: 32px;
            font-weight: 700;
            line-height: 1;
            margin: 0;
            color: var(--green-inst);
        }
        .company-nit {
            font-size: 10px;
            color: #888;
            margin-top: 4px;
            letter-spacing: 1px;
        }

        .report-title-box {
            text-align: right;
        }
        .doc-title {
            font-family: 'Cormorant Garamond', serif;
            font-size: 22px;
            font-style: italic;
            color: #444;
            margin-bottom: 8px;
        }
        .date-range-badge {
            display: inline-block;
            border: 1px solid var(--green-inst);
            padding: 5px 12px;
            border-radius: 2px;
        }
        .date-range-text { font-size: 13px; font-weight: 700; color: var(--green-inst); }

        .account-ribbon {
            margin: 0 50px;
            padding: 12px 20px;
            background-color: var(--bg-grand-total);
            border-left: 4px solid var(--green-inst);
            font-size: 12px;
            color: var(--text-main);
        }
        .account-ribbon strong { color: var(--green-light); margin-right: 5px; }

        main { padding: 25px 50px; }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        thead th {
            background-color: #F8F9F7;
            color: var(--text-labels);
            font-size: 9px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            padding: 12px 10px;
            border-bottom: 2px solid var(--green-inst);
            text-align: left;
        }

        tbody td {
            padding: 10px;
            font-size: 10px;
            border-bottom: 1px solid #EEE;
            color: #333;
            vertical-align: middle;
        }

        .row-alt { background-color: #FCFCFB; }
        .text-right { text-align: right !important; }
        .negative { color: var(--negative) !important; font-weight: 500; }
        
        .doc-id { font-weight: 700; color: var(--green-light); font-size: 9px; }

        .subtotal-row {
            background-color: #F8F9F7;
            font-weight: 700;
            color: var(--green-inst);
        }

        .grand-total-section {
            background-color: var(--green-inst);
            color: var(--white);
            font-weight: 700;
            font-size: 12px;
        }
        .grand-total-section td { border: none; padding: 15px 10px; color: var(--white) !important; }
        .gold-label { color: var(--gold-soft); text-transform: uppercase; letter-spacing: 1px; font-size: 10px; }
    </style>
</head>
<body>
    <div class="page-container">
        <div class="decor-bar-top"></div>
        
        <header>
            <div class="header-left">
                <span class="badge-premium">Inteligencia Financiera</span>
                <h1 class="company-name">{{ empresa_nombre or 'VERDURAS LA 21' }}</h1>
                <div class="company-nit">NIT: {{ empresa_nit or '901464119-7' }}</div>
            </div>
            <div class="header-right">
                <div class="report-title-box">
                    <div class="doc-title">Auxiliar por Cuenta</div>
                    <div class="date-range-badge">
                        <span class="date-range-text">Del {{ fecha_inicio }} al {{ fecha_fin }}</span>
                    </div>
                </div>
            </div>
        </header>

        <div class="account-ribbon">
            <strong>CUENTA SELECCIONADA:</strong> {{ cuenta_codigo }} - {{ cuenta_nombre }}
        </div>

        <main>
            <table>
                <thead>
                    <tr>
                        <th width="80">Fecha</th>
                        <th width="120">Documento</th>
                        <th>Beneficiario / Tercero</th>
                        <th width="200">Concepto</th>
                        {% if has_cost_centers %}
                        <th width="90" class="text-right" style="white-space: nowrap;">C. Costo</th>
                        {% endif %}
                        <th width="100" class="text-right">D&eacute;bitos</th>
                        <th width="100" class="text-right">Cr&eacute;ditos</th>
                        <th width="110" class="text-right">Saldo</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="subtotal-row">
                        <td colspan="{{ 5 if has_cost_centers else 4 }}">SALDO ANTERIOR</td>
                        <td colspan="3" class="text-right" style="padding-right: 10px;">{{ "{:,.0f}".format(saldo_anterior).replace(',', '.') }}</td>
                    </tr>
                    
                    {% for mov in movimientos %}
                    <tr class="{{ 'row-alt' if loop.index0 % 2 == 0 else '' }}">
                        <td>{{ mov.fecha.strftime('%Y-%m-%d') }}</td>
                        <td class="doc-id">{{ mov.tipo_documento }}-{{ mov.numero_documento }}</td>
                        <td style="font-size: 9px; max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                            {{ mov.beneficiario or 'N/A' }}
                        </td>
                        <td style="font-size: 9px; line-height: 1.2;">{{ mov.concepto }}</td>
                        {% if has_cost_centers %}
                        <td class="text-right" style="color: #888;">{{ mov.centro_costo_codigo or '-' }}</td>
                        {% endif %}
                        <td class="text-right">{{ "{:,.0f}".format(mov.debito).replace(',', '.') }}</td>
                        <td class="text-right">{{ "{:,.0f}".format(mov.credito).replace(',', '.') }}</td>
                        <td class="text-right {{ 'negative' if mov.saldo_parcial < 0 else '' }}">
                            {{ "{:,.0f}".format(mov.saldo_parcial).replace(',', '.') }}
                        </td>
                    </tr>
                    {% endfor %}

                    <tr class="subtotal-row">
                        <td colspan="{{ 5 if has_cost_centers else 4 }}">MOVIMIENTOS DEL PERIODO</td>
                        <td class="text-right">{{ "{:,.0f}".format(total_debito_periodo).replace(',', '.') }}</td>
                        <td class="text-right">{{ "{:,.0f}".format(total_credito_periodo).replace(',', '.') }}</td>
                        <td></td>
                    </tr>
                </tbody>
                <tfoot>
                    <tr class="grand-total-section">
                        <td colspan="{{ 5 if has_cost_centers else 4 }}">
                            <span class="gold-label">Consolidado Final</span><br>
                            SALDO ACUMULADO AL {{ fecha_fin }}
                        </td>
                        {% set saldo_final = movimientos[-1].saldo_parcial if movimientos else saldo_anterior %}
                        <td colspan="3" class="text-right" style="font-size: 16px; padding-right: 10px;">
                            {{ "{:,.0f}".format(saldo_final).replace(',', '.') }}
                        </td>
                    </tr>
                </tfoot>
            </table>
        </main>

        <div class="decor-bar-bottom"></div>
    </div>
</body>
</html>
''',
    'reports/analisis_cuenta_doc_report.html': r'''
<!DOCTYPE html>
<html lang="es">

<head>
    <title>AnÃ¡lisis de Cuenta por Documento</title>
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
        <h2>ANÃLISIS DE CUENTA POR DOCUMENTO</h2>
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
                    <th class="text-left" style="width: 15%">CÃ³d. Tipo</th>
                    <th class="text-left" style="width: 45%">Tipo de Documento</th>
                    <th style="width: 20%">DÃ©bitos</th>
                    <th style="width: 20%">CrÃ©ditos</th>
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
                <td><strong>DÃ©bitos: ${{ "{:,.0f}".format(reporte.totales_generales.debito) }}</strong></td>
                <td><strong>CrÃ©ditos: ${{ "{:,.0f}".format(reporte.totales_generales.credito) }}</strong></td>
            </tr>
        </table>
    </div>
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
                <th style="width: 20%;">DÃ©bito (Cargos)</th>
                <th style="width: 20%;">CrÃ©dito (Abonos)</th>
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
        <p>PerÃ­odo: {{ fecha_inicio }} al {{ fecha_fin }}</p>
    </div>

    <table>
        <thead>
            <tr>
                <th style="width: 8%;">Fecha</th>
                <th style="width: 8%;">Doc.</th>
                <th style="width: 15%;">Beneficiario</th>
                <th style="width: 10%;">Cuenta</th>
                <th style="width: 20%;">Concepto</th>
                <th style="width: 10%;">DÃ©bito</th>
                <th style="width: 10%;">CrÃ©dito</th>
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
                <th style="width: 21%;">DÃ©bito (Pagos)</th>
                <th style="width: 21%;">CrÃ©dito (Deudas)</th>
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
                <th>CÃ³digo</th>
                <th>Nombre del Centro de Costo</th>
                <th class="text-right">Saldo Inicial</th>
                <th class="text-right">DÃ©bitos</th>
                <th class="text-right">CrÃ©ditos</th>
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

    'reports/balance_de_prueba_report.html': r'''<!DOCTYPE html>
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
            print-color-adjust: exact;
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
        .badge::before { content: "â€¢"; margin-right: 6px; }

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
                <th>CÃ³digo</th>
                <th>Nombre de la Cuenta</th>
                <th class="text-right">Saldo Inicial</th>
                <th class="text-right">DÃ©bitos</th>
                <th class="text-right">CrÃ©ditos</th>
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
            <span>3605 - Utilidad (PÃ©rdida) del Ejercicio</span>
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
            <span>3605 - Utilidad (PÃ©rdida) del Ejercicio</span>
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
                    <th>CÃ³digo</th>
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
<!DOCTYPE html>
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
        <h3>{{ documento.tipo_nombre }} NÂ° {{ documento.consecutivo }}</h3>
    </div>

    <div class="info-grid">
        <div class="info-row">
            <div class="info-cell label">Fecha:</div>
            <div class="info-cell">{{ documento.fecha_emision }}</div>
            <div class="info-cell label">Ciudad:</div>
            <div class="info-cell">BogotÃ¡ D.C.</div> <!-- Placeholder city -->
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
                <th style="width: 15%;">CÃ³digo</th>
                <th style="width: 45%;">DescripciÃ³n</th>
                <th style="width: 20%;" class="text-right">DÃ©bito</th>
                <th style="width: 20%;" class="text-right">CrÃ©dito</th>
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
            <div class="sig-line">ElaborÃ³</div>
        </div>
        <div class="sig-box">
            <div class="sig-line">AprobÃ³</div>
        </div>
        <div class="sig-box">
            <div class="sig-line">RecibÃ­ Conforme</div>
            <div style="font-size: 8pt;">C.C.</div>
        </div>
    </div>

    <div class="footer">
        Generado automÃ¡ticamente por Finaxis Cloud
    </div>
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
                        <span class="vencida">{{ factura.dias_mora }} dÃ­as de mora</span>
                    {% else %}
                        <span class="por-vencer">Vence en {{ factura.dias_para_vencer }} dÃ­as</span>
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
        <div class="aging-box"><h4 class="vencida">1-30 DÃ­as</h4><p>{{ '{:,.2f}'.format(reporte.edades.vencida_1_30) }}</p></div>
        <div class="aging-box"><h4 class="vencida">31-60 DÃ­as</h4><p>{{ '{:,.2f}'.format(reporte.edades.vencida_31_60) }}</p></div>
        <div class="aging-box"><h4 class="vencida">61-90 DÃ­as</h4><p>{{ '{:,.2f}'.format(reporte.edades.vencida_61_90) }}</p></div>
        <div class="aging-box"><h4 class="vencida">+90 DÃ­as</h4><p>{{ '{:,.2f}'.format(reporte.edades.vencida_mas_90) }}</p></div>
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
                        <span class="vencida">{{ factura.dias_mora }} dÃ­as de mora</span>
                    {% else %}
                        <span class="por-vencer">Vence en {{ factura.dias_para_vencer }} dÃ­as</span>
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
        <div class="aging-box"><h4 class="vencida">1-30 DÃ­as</h4><p>{{ '{:,.2f}'.format(reporte.edades.vencida_1_30) }}</p></div>
        <div class="aging-box"><h4 class="vencida">31-60 DÃ­as</h4><p>{{ '{:,.2f}'.format(reporte.edades.vencida_31_60) }}</p></div>
        <div class="aging-box"><h4 class="vencida">61-90 DÃ­as</h4><p>{{ '{:,.2f}'.format(reporte.edades.vencida_61_90) }}</p></div>
        <div class="aging-box"><h4 class="vencida">+90 DÃ­as</h4><p>{{ '{:,.2f}'.format(reporte.edades.vencida_mas_90) }}</p></div>
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
        <p><strong>PerÃ­odo Analizado:</strong> {{ filtros.fecha_inicio }} al {{ filtros.fecha_fin }}</p>
    </div>

    <table>
        <thead>
            <tr>
                <th>CÃ³digo</th>
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
                <td colspan="10" style="text-align:center;">No se encontraron productos con movimiento en el perÃ­odo seleccionado.</td>
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
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Estado de Resultados Â· {{ empresa_nombre }}</title>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Lato:wght@300;400;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --cream:    #faf8f4;
      --white:    #ffffff;
      --warm1:    #f3ede3;
      --warm2:    #e8dfd0;
      --ink:      #1a1612;
      --ink2:     #3d3529;
      --muted:    #8a7e6f;
      --rule:     #d9cfc0;
      --gold:     #b5892a;
      --gold-lt:  #f5ead4;
      --green:    #2e7d52;
      --green-lt: #e6f4ed;
      --red:      #b53a2a;
      --red-lt:   #faecea;
      --blue:     #1e4f87;
      --blue-lt:  #e8f0fb;
    }

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    html { scroll-behavior: smooth; }

    body {
      background: var(--cream);
      color: var(--ink);
      font-family: 'Lato', sans-serif;
      font-size: 15px;
      line-height: 1.6;
    }

    /* â”€â”€â”€ PAGE WRAPPER â”€â”€â”€ */
    .page {
      max-width: 860px;
      margin: 0 auto;
      padding: 60px 48px 80px;
      background: var(--white);
      box-shadow: 0 2px 40px rgba(90,60,20,.10);
      min-height: 100vh;
    }

    /* â”€â”€â”€ HEADER â”€â”€â”€ */
    .header {
      border-top: 4px solid var(--ink);
      padding-top: 28px;
      margin-bottom: 40px;
      position: relative;
    }
    .header::after {
      content: '';
      display: block;
      height: 1px;
      background: var(--rule);
      margin-top: 28px;
    }
    .org-name {
      font-family: 'Playfair Display', serif;
      font-size: 26px;
      font-weight: 700;
      letter-spacing: .01em;
      color: var(--ink);
    }
    .org-meta {
      font-family: 'IBM Plex Mono', monospace;
      font-size: 11px;
      color: var(--muted);
      letter-spacing: .1em;
      text-transform: uppercase;
      margin-top: 4px;
    }
    .doc-title {
      margin-top: 16px;
      font-family: 'Playfair Display', serif;
      font-size: 20px;
      font-style: italic;
      color: var(--gold);
      font-weight: 400;
    }
    .doc-period {
      font-size: 13px;
      color: var(--muted);
      margin-top: 3px;
      font-family: 'IBM Plex Mono', monospace;
      letter-spacing: .06em;
    }

    /* â”€â”€â”€ KPI STRIP â”€â”€â”€ */
    .kpi-strip {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1px;
      background: var(--rule);
      border: 1px solid var(--rule);
      border-radius: 8px;
      overflow: hidden;
      margin-bottom: 48px;
    }
    .kpi-cell {
      background: var(--white);
      padding: 20px 22px;
    }
    .kpi-cell:hover { background: var(--warm1); }
    .kpi-label {
      font-size: 10px;
      letter-spacing: .12em;
      text-transform: uppercase;
      color: var(--muted);
      font-family: 'IBM Plex Mono', monospace;
      margin-bottom: 6px;
    }
    .kpi-value {
      font-family: 'IBM Plex Mono', monospace;
      font-size: 20px;
      font-weight: 500;
    }
    .kpi-value.green { color: var(--green); }
    .kpi-value.red   { color: var(--red);   }
    .kpi-value.gold  { color: var(--gold);  }
    .kpi-sub {
      font-size: 11px;
      color: var(--muted);
      margin-top: 3px;
    }

    /* â”€â”€â”€ SECTION TITLE â”€â”€â”€ */
    .section-head {
      display: flex;
      align-items: center;
      gap: 14px;
      margin-bottom: 4px;
    }
    .section-head h2 {
      font-family: 'Playfair Display', serif;
      font-size: 16px;
      font-weight: 700;
      letter-spacing: .03em;
      text-transform: uppercase;
      white-space: nowrap;
    }
    .section-head h2.income { color: var(--green); }
    .section-head h2.expense { color: var(--red); }
    .section-head::after {
      content: '';
      flex: 1;
      height: 1px;
      background: var(--rule);
    }

    /* â”€â”€â”€ TABLE â”€â”€â”€ */
    .tbl-wrap { margin-bottom: 36px; }

    table {
      width: 100%;
      border-collapse: collapse;
    }

    thead tr {
      border-bottom: 2px solid var(--rule);
    }
    thead th {
      font-size: 10px;
      letter-spacing: .1em;
      text-transform: uppercase;
      font-family: 'IBM Plex Mono', monospace;
      color: var(--muted);
      font-weight: 500;
      padding: 8px 10px 10px;
    }
    thead th:first-child { text-align: left; padding-left: 0; }
    thead th:not(:first-child) { text-align: right; }

    tbody tr {
      border-bottom: 1px solid var(--warm1);
      transition: background .12s;
    }
    tbody tr:hover { background: var(--warm1); }

    td {
      padding: 11px 10px;
      font-size: 14px;
      vertical-align: middle;
    }
    td:first-child {
      padding-left: 0;
      color: var(--ink2);
      font-weight: 400;
    }
    td:not(:first-child) {
      text-align: right;
      font-family: 'IBM Plex Mono', monospace;
      font-size: 13px;
      color: var(--ink);
    }

    .code-cell {
      font-family: 'IBM Plex Mono', monospace;
      font-size: 11px;
      color: var(--muted);
      padding-right: 16px;
    }

    /* pct bar */
    .bar-wrap { display: flex; align-items: center; gap: 8px; justify-content: flex-end; }
    .bar-track {
      width: 80px; height: 5px;
      background: var(--warm2);
      border-radius: 3px;
      overflow: hidden;
    }
    .bar-fill { height: 100%; border-radius: 3px; }

    /* subtotal / total rows */
    tr.subtotal td {
      border-top: 1.5px solid var(--rule);
      border-bottom: 1.5px solid var(--rule);
      font-weight: 700;
      font-size: 14px;
      background: var(--warm1);
    }
    tr.subtotal td:first-child { font-family: 'Lato', sans-serif; }
    tr.subtotal td:not(:first-child) { font-family: 'IBM Plex Mono', monospace; }

    tr.grand-total td {
      border-top: 3px double var(--ink);
      padding-top: 16px;
      padding-bottom: 16px;
      font-weight: 700;
      font-size: 15px;
    }
    tr.grand-total td:first-child {
      font-family: 'Playfair Display', serif;
      font-size: 16px;
    }

    .loss { color: var(--red) !important; }
    .profit { color: var(--green) !important; }

    /* badge */
    .badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 20px;
      font-size: 10px;
      font-weight: 700;
      font-family: 'IBM Plex Mono', monospace;
      letter-spacing: .05em;
      margin-left: 6px;
      vertical-align: middle;
    }
    .badge.ing { background: var(--green-lt); color: var(--green); }
    .badge.gasto { background: var(--red-lt); color: var(--red); }
    .badge.info { background: var(--blue-lt); color: var(--blue); }

    /* group header inside tbody */
    tr.group-row td {
      font-size: 11px;
      letter-spacing: .09em;
      text-transform: uppercase;
      color: var(--muted);
      font-family: 'IBM Plex Mono', monospace;
      padding: 14px 0 4px;
      border-bottom: none;
      background: transparent;
    }
    tr.group-row:hover { background: transparent; }

    /* â”€â”€â”€ UTILIDAD BLOCK â”€â”€â”€ */
    .result-block {
      margin-top: 8px;
      border-radius: 10px;
      padding: 24px 28px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 20px;
      flex-wrap: wrap;
    }
    .result-block.loss { background: var(--red-lt); border: 1.5px solid #e8bdb8; }
    .result-block.profit { background: var(--green-lt); border: 1.5px solid #a8d9bb; }
    .result-label {
      font-family: 'Playfair Display', serif;
      font-size: 18px;
      font-weight: 700;
    }
    .result-label.loss  { color: var(--red); }
    .result-label.profit { color: var(--green); }
    .result-period { font-size: 12px; color: var(--muted); margin-top: 2px; }
    .result-value {
      font-family: 'IBM Plex Mono', monospace;
      font-size: 32px;
      font-weight: 500;
    }
    .result-value.loss  { color: var(--red); }
    .result-value.profit { color: var(--green); }

    /* â”€â”€â”€ DONUT CHART â”€â”€â”€ */
    .charts-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
      margin: 44px 0;
    }
    .chart-card {
      border: 1px solid var(--rule);
      border-radius: 10px;
      padding: 22px;
      background: var(--white);
    }
    .chart-title {
      font-family: 'Playfair Display', serif;
      font-size: 13px;
      font-weight: 700;
      color: var(--ink);
      margin-bottom: 16px;
      text-transform: uppercase;
      letter-spacing: .06em;
    }
    .donut-wrap { display: flex; align-items: center; gap: 16px; }
    svg.donut { flex-shrink: 0; }
    .legend-list { font-size: 12px; color: var(--ink2); }
    .legend-list li {
      display: flex; align-items: center; gap: 7px;
      margin-bottom: 7px; list-style: none;
    }
    .leg-swatch { width: 10px; height: 10px; border-radius: 2px; flex-shrink:0; }
    .leg-name { flex: 1; }
    .leg-pct { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: var(--muted); }

    /* â”€â”€â”€ BAR CHART â”€â”€â”€ */
    .hbar-list { list-style: none; }
    .hbar-item { margin-bottom: 10px; }
    .hbar-meta { display: flex; justify-content: space-between; font-size: 11px; color: var(--muted); margin-bottom: 3px; }
    .hbar-name { font-family: 'Lato', sans-serif; color: var(--ink2); }
    .hbar-val  { font-family: 'IBM Plex Mono', monospace; font-size: 11px; }
    .hbar-track { height: 8px; background: var(--warm2); border-radius: 4px; overflow: hidden; }
    .hbar-fill  { height: 100%; border-radius: 4px; }

    /* â”€â”€â”€ FOOTER â”€â”€â”€ */
    .footer {
      margin-top: 60px;
      padding-top: 20px;
      border-top: 1px solid var(--rule);
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 11px;
      color: var(--muted);
      font-family: 'IBM Plex Mono', monospace;
      flex-wrap: wrap;
      gap: 8px;
    }

    /* â”€â”€â”€ PRINT â”€â”€â”€ */
    @media print {
      body { background: #fff; }
      .page { box-shadow: none; padding: 30px 30px 50px; }
      .kpi-cell:hover, tbody tr:hover { background: none; }
    }

    @media (max-width: 640px) {
      .page { padding: 30px 20px 50px; }
      .kpi-strip { grid-template-columns: 1fr; }
      .charts-row { grid-template-columns: 1fr; }
      .result-value { font-size: 24px; }
    }

    /* â”€â”€â”€ ANIMATIONS â”€â”€â”€ */
    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(18px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    .page > * {
      animation: fadeUp .5s ease both;
    }
    .page > *:nth-child(1) { animation-delay: .05s; }
    .page > *:nth-child(2) { animation-delay: .12s; }
    .page > *:nth-child(3) { animation-delay: .18s; }
    .page > *:nth-child(4) { animation-delay: .24s; }
    .page > *:nth-child(5) { animation-delay: .30s; }
    .page > *:nth-child(6) { animation-delay: .36s; }
    .page > *:nth-child(7) { animation-delay: .42s; }
  </style>
</head>
<body>
<div class="page">

  <!-- HEADER -->
  <header class="header">
    <div class="org-name">{{ empresa_nombre }}</div>
    <div class="org-meta">NIT: {{ empresa_nit }}</div>
    <div class="doc-title">Estado de Resultados Gerencial</div>
    <div class="doc-period">PerÃ­odo: {{ fecha_inicio }} â€” {{ fecha_fin }}</div>
  </header>

  <!-- KPIs -->
  <div class="kpi-strip">
    <div class="kpi-cell">
      <div class="kpi-label">Total Ingresos</div>
      <div class="kpi-value green">${{ "{:,.0f}".format(report_data.totales.total_ingresos).replace(',', '.') }}</div>
      <div class="kpi-sub">Ingresos operacionales</div>
    </div>
    <div class="kpi-cell">
      <div class="kpi-label">Total Gastos</div>
      <div class="kpi-value red">${{ "{:,.0f}".format(report_data.totales.total_gastos).replace(',', '.') }}</div>
      <div class="kpi-sub">Gastos operacionales</div>
    </div>
    <div class="kpi-cell">
      <div class="kpi-label">Resultado del PerÃ­odo</div>
      <div class="kpi-value {% if report_data.totales.utilidad_neta < 0 %}red{% else %}gold{% endif %}">
        {% if report_data.totales.utilidad_neta < 0 %}âˆ’{% endif %}${{ "{:,.0f}".format(report_data.totales.utilidad_neta | abs).replace(',', '.') }}
      </div>
      <div class="kpi-sub">{% if report_data.totales.utilidad_neta < 0 %}DÃ©ficit{% else %}SuperÃ¡vit{% endif %} operacional</div>
    </div>
  </div>

  <!-- INGRESOS -->
  <div class="tbl-wrap">
    <div class="section-head"><h2 class="income">Ingresos Operacionales</h2></div>
    <table>
      <thead>
        <tr>
          <th>Cuenta</th>
          <th>DescripciÃ³n</th>
          <th>Valor</th>
          <th>% s/Total Ing.</th>
        </tr>
      </thead>
      <tbody>
        {% for ing in report_data.ingresos %}
        <tr>
          <td class="code-cell">{{ ing.codigo }}</td>
          <td>{{ ing.nombre }} {% if ing.is_ingreso_principal %}<span class="badge ing">Principal</span>{% endif %}</td>
          <td>${{ "{:,.0f}".format(ing.saldo).replace(',', '.') }}</td>
          <td>
            <div class="bar-wrap">
              <div class="bar-track"><div class="bar-fill" style="width:{{ ing.porcentaje | round(1) }}%; background:#2e7d52;"></div></div>
              <span>{{ "{:,.1f}".format(ing.porcentaje).replace('.', ',') }}%</span>
            </div>
          </td>
        </tr>
        {% endfor %}
        <tr class="subtotal">
          <td colspan="2"><strong>TOTAL INGRESOS OPERACIONALES</strong></td>
          <td><strong>${{ "{:,.0f}".format(report_data.totales.total_ingresos).replace(',', '.') }}</strong></td>
          <td></td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- GASTOS -->
  <div class="tbl-wrap">
    <div class="section-head"><h2 class="expense">Gastos Operacionales</h2></div>
    <table>
      <thead>
        <tr>
          <th>Cuenta</th>
          <th>DescripciÃ³n</th>
          <th>Valor</th>
          <th>% s/Total Gtos.</th>
        </tr>
      </thead>
      <tbody>

        <!-- NÃ“MINA -->
        {% if report_data.gastos_nomina %}
        <tr class="group-row"><td colspan="4">â–¸ NÃ³mina y Carga Prestacional</td></tr>
        {% for gasto in report_data.gastos_nomina %}
        <tr>
          <td class="code-cell">{{ gasto.codigo }}</td>
          <td>{{ gasto.nombre }} {% if gasto.is_mayor_gasto %}<span class="badge gasto">Mayor gasto</span>{% endif %}</td>
          <td>${{ "{:,.0f}".format(gasto.saldo).replace(',', '.') }}</td>
          <td>
            <div class="bar-wrap">
              <div class="bar-track"><div class="bar-fill" style="width:{{ gasto.porcentaje | round(1) }}%; background:#b53a2a;"></div></div>
              <span>{{ "{:,.1f}".format(gasto.porcentaje).replace('.', ',') }}%</span>
            </div>
          </td>
        </tr>
        {% endfor %}
        {% endif %}

        <!-- OPERATIVOS -->
        {% if report_data.gastos_operativos %}
        <tr class="group-row"><td colspan="4">â–¸ Gastos Operativos</td></tr>
        {% for gasto in report_data.gastos_operativos %}
        <tr>
          <td class="code-cell">{{ gasto.codigo }}</td>
          <td>{{ gasto.nombre }} {% if gasto.is_mayor_gasto %}<span class="badge gasto">Mayor gasto</span>{% endif %}</td>
          <td>${{ "{:,.0f}".format(gasto.saldo).replace(',', '.') }}</td>
          <td>
            <div class="bar-wrap">
              <div class="bar-track"><div class="bar-fill" style="width:{{ gasto.porcentaje | round(1) }}%; background:#c05a45;"></div></div>
              <span>{{ "{:,.1f}".format(gasto.porcentaje).replace('.', ',') }}%</span>
            </div>
          </td>
        </tr>
        {% endfor %}
        {% endif %}

        <!-- GENERALES -->
        {% if report_data.gastos_generales %}
        <tr class="group-row"><td colspan="4">â–¸ Gastos Generales y Tributarios</td></tr>
        {% for gasto in report_data.gastos_generales %}
        <tr>
          <td class="code-cell">{{ gasto.codigo }}</td>
          <td>{{ gasto.nombre }} {% if gasto.is_mayor_gasto %}<span class="badge gasto">Mayor gasto</span>{% endif %}</td>
          <td>${{ "{:,.0f}".format(gasto.saldo).replace(',', '.') }}</td>
          <td>
            <div class="bar-wrap">
              <div class="bar-track"><div class="bar-fill" style="width:{{ gasto.porcentaje | round(1) }}%; background:#d8958a;"></div></div>
              <span>{{ "{:,.1f}".format(gasto.porcentaje).replace('.', ',') }}%</span>
            </div>
          </td>
        </tr>
        {% endfor %}
        {% endif %}

        <tr class="subtotal">
          <td colspan="2"><strong>TOTAL GASTOS OPERACIONALES</strong></td>
          <td><strong>${{ "{:,.0f}".format(report_data.totales.total_gastos).replace(',', '.') }}</strong></td>
          <td></td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- RESULTADO -->
  <div class="result-block {% if report_data.totales.utilidad_neta < 0 %}loss{% else %}profit{% endif %}">
    <div>
      <div class="result-label {% if report_data.totales.utilidad_neta < 0 %}loss{% else %}profit{% endif %}">Utilidad (PÃ©rdida) del Ejercicio</div>
      <div class="result-period">PerÃ­odo {{ fecha_inicio }} â€“ {{ fecha_fin }}</div>
    </div>
    <div class="result-value {% if report_data.totales.utilidad_neta < 0 %}loss{% else %}profit{% endif %}">
      {% if report_data.totales.utilidad_neta < 0 %}âˆ’{% endif %}${{ "{:,.0f}".format(report_data.totales.utilidad_neta | abs).replace(',', '.') }}
    </div>
  </div>

  <!-- GRÃFICAS -->
  <div class="charts-row">

    <!-- Donut ingresos -->
    <div class="chart-card">
      <div class="chart-title">ComposiciÃ³n de Ingresos</div>
      <div class="donut-wrap">
        <svg class="donut" width="90" height="90" viewBox="0 0 36 36">
          <circle r="15.9155" cx="18" cy="18" fill="none" stroke="#e8dfd0" stroke-width="3.8"/>
          
          {% set ns = namespace(offset=25) %}
          {% set colors = ['#2e7d52', '#5aab82', '#9ecfb5', '#c8e6d6', '#e0f0e6'] %}
          
          {% for ing in report_data.ingresos[:5] %}
          {% set pct = ing.porcentaje %}
          {% if pct > 0 %}
          <circle r="15.9155" cx="18" cy="18" fill="none" stroke="{{ colors[loop.index0] }}" stroke-width="3.8"
            stroke-dasharray="{{ pct | round(1) }} {{ 100 - (pct | round(1)) }}" stroke-dashoffset="{{ ns.offset }}" stroke-linecap="round"/>
          {% set ns.offset = ns.offset - pct %}
          {% endif %}
          {% endfor %}
        </svg>
        <ul class="legend-list">
          {% for ing in report_data.ingresos[:5] %}
          <li><div class="leg-swatch" style="background:{{ colors[loop.index0] }}"></div><span class="leg-name">{{ ing.nombre }}</span><span class="leg-pct">{{ "{:,.1f}".format(ing.porcentaje).replace('.', ',') }}%</span></li>
          {% endfor %}
        </ul>
      </div>
    </div>

    <!-- Barras top 5 gastos -->
    <div class="chart-card">
      <div class="chart-title">Top 5 Rubros de Gasto</div>
      <ul class="hbar-list">
        {% for gasto in report_data.top_5_gastos %}
        <li class="hbar-item">
          <div class="hbar-meta"><span class="hbar-name">{{ gasto.nombre }}</span><span class="hbar-val">${{ "{:,.0f}".format(gasto.saldo).replace(',', '.') }} Â· {{ "{:,.1f}".format(gasto.porcentaje).replace('.', ',') }}%</span></div>
          <div class="hbar-track"><div class="hbar-fill" style="width:{{ gasto.porcentaje | round(1) }}%; background:{% if loop.index0 == 0 %}#b53a2a{% elif loop.index0 == 1 %}#c05a45{% else %}#1e4f87{% endif %};"></div></div>
        </li>
        {% endfor %}
      </ul>
    </div>
  </div>

  <!-- FOOTER -->
  <footer class="footer">
    <span>Estado de Resultados Gerencial Â· {{ fecha_inicio }} â€“ {{ fecha_fin }} Â· {{ empresa_nombre }} Â· NIT {{ empresa_nit }}</span>
    <span>Generado automÃ¡ticamente Â· Solo lectura</span>
  </footer>

</div>
</body>
</html>

''',

    'reports/exito_fe_template.html': r'''
<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">
    <title>Factura ElectrÃ³nica de Venta - Estilo Exito</title>
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

        /* SECCIÃ“N TIPO DOCUMENTO Y NÃšMERO (IZQUIERDA) */
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

        /* CLIENTE Y DIRECCIÃ“N */
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

        /* SECCIÃ“N TOTALES E IMPUESTOS */
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

        /* PIE DE PÃGINA (DIAN) */
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
        <div class="company-details">TelÃ©fono - {{empresa.telefono}}</div>
        <div class="company-details">E-mail: {{empresa.email}}</div>
        <div class="company-details text-bold">REPRESENTACION GRAFICA DE FACTURA ELECTRONICA</div>
    </div>

    <div class="doc-info">
        <div class="doc-title">FACTURA ELECTRONICA DE VENTA</div>
        <div class="doc-number">{{documento.tipo_documento_codigo}} - {{documento.numero}}</div>
        <div class="doc-dates">
            Fecha ValidaciÃ³n DIAN: {{documento.fecha_emision}}<br>
            Hora ValidaciÃ³n DIAN: {{documento.hora_emision|default('00:00:00')}}
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
                <div class="label">RÃ©gimen:</div>
                <div class="value">{{tercero.regimen|default('No responsable de IVA')}}</div>
            </div>
            <div class="row">
                <div class="label">ObligaciÃ³n:</div>
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
                <div class="label">DirecciÃ³n:</div>
                <div class="value">{{tercero.direccion}}</div>
            </div>
            <div class="row">
                <div class="label">Ciudad:</div>
                <div class="value">{{tercero.ciudad}}</div>
            </div>
            <div class="row">
                <div class="label">TelÃ©fono:</div>
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
                <th width="14%">CÃ³digo</th>
                <th width="32%">DescripciÃ³n</th>
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
            <strong>ResoluciÃ³n de FacturaciÃ³n ElectrÃ³nica</strong><br>
            Nro. {{documento.resolucion_numero}} de {{documento.resolucion_fecha}}<br>
            Prefijo: {{documento.resolucion_prefijo}}, Rango {{documento.resolucion_rango_desde}} Al
            {{documento.resolucion_rango_hasta}}<br>
            Vigencia Desde: {{documento.resolucion_fecha}} Hasta:
            {{documento.resolucion_fecha_fin|default('2027-10-10')}}<br><br>

            <strong>CUFE:</strong> {{documento.dian_cufe}}<br><br>

            La presente Factura ElectrÃ³nica de Venta, es un tÃ­tulo valor de acuerdo con lo establecido en el CÃ³digo de
            Comercio y en especial en los artÃ­culos 621,772 y 774.
        </div>
    </div>
    {% endif %}

</body>

</html>
''',

    'reports/fuentes_usos_report.html': r'''
<!DOCTYPE html>
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
                    <h3>VariaciÃ³n en el Periodo</h3>
                    <p>Activo Corriente Final: <strong>{{ "${:,.0f}".format(resumen_kt.activo_cte_fin) }}</strong></p>
                    <p>Pasivo Corriente Final: <strong>{{ "${:,.0f}".format(resumen_kt.pasivo_cte_fin) }}</strong></p>
                    <hr>
                    <p>K.T. Final: <strong>{{ "${:,.0f}".format(resumen_kt.kt_fin) }}</strong></p>
                    <h4 class="{{ 'text-success' if resumen_kt.variacion_kt > 0 else 'text-danger' }}">
                        VariaciÃ³n K.T.: {{ "${:,.0f}".format(resumen_kt.variacion_kt) }}
                    </h4>
                </td>
            </tr>
        </table>
    </div>

    <div class="section-title">Detalle de Variaciones por Cuenta</div>
    <table>
        <thead>
            <tr>
                <th style="width: 10%;">CÃ³digo</th>
                <th style="width: 30%;">Cuenta</th>
                <th style="width: 15%;">Saldo Inicial</th>
                <th style="width: 15%;">Saldo Final</th>
                <th style="width: 15%; background-color: #28a745;">FUENTES (Origen)</th>
                <th style="width: 15%; background-color: #dc3545;">USOS (AplicaciÃ³n)</th>
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
                    <span style="font-size: 9px; font-weight: normal;">(Debe ser igual a la VariaciÃ³n K.T.)</span>
                </td>
            </tr>
        </tfoot>
    </table>

    <div style="font-size: 9px; color: #666; margin-top: 20px;">
        <p><strong>Nota Interpretativa:</strong><br>
            - <strong>FUENTES:</strong> Dinero generado por disminuciÃ³n de Activos (ej. cobro de cartera) o aumento de
            Pasivos (ej. financiaciÃ³n proveedores).<br>
            - <strong>USOS:</strong> Dinero utilizado para aumentar Activos (ej. compra inventario) o disminuir Pasivos
            (ej. pago deudas).</p>
    </div>
</body>

</html>
''',

    'reports/generic_document_template.html': r'''
<!DOCTYPE html>
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
<!DOCTYPE html>
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
            /* Asegurar que la cabecera se repita en cada pÃ¡gina */
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
        Tipo de OperaciÃ³n: {{ filtros.tipo_operacion or 'TODOS' }} <br>
        <strong>Registros Exportados: {{ items|length }} (Max: 5000)</strong>
    </div>

    <table>
        <thead>
            <tr>
                <th width="15%">Fecha</th>
                <th width="15%">OperaciÃ³n</th>
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
                    {% elif item.tipo_operacion == 'REVERSION' %} <span class="tag tag-reversion">REVERSIÃ“N</span>
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
        Este reporte fue generado automÃ¡ticamente por el sistema FINAXIS.
    </div>
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
                <td><strong>UTILIDAD (O PÃ‰RDIDA) DEL EJERCICIO</strong></td>
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
                <td><strong>UTILIDAD (O PÃ‰RDIDA) DEL EJERCICIO</strong></td>
                <td class="text-right"><strong>{{ "{:,.2f}".format(totales.utilidad_neta) }}</strong></td>
            </tr>
        </tbody>
    </table>
</body>
</html>
''',

    'reports/inventario_document_template.html': r'''
<!DOCTYPE html>
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

        /* INFORMACIÃ“N CLIENTE */
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

        /* SECCIÃ“N TOTALES PROFESIONAL */
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

        /* PIE DE PÃGINA EMPRESARIAL */
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
                NIT: {{empresa.nit}} â€¢ {{empresa.direccion}}<br>
                Tel: {{empresa.telefono}}{% if empresa.email %} â€¢ {{empresa.email}}{% endif %}
            </div>
        </div>
        
        <div class="document-section">
            <div class="doc-type">{{documento.tipo_nombre}}</div>
            <div class="doc-number">NÂ° {{documento.consecutivo}}</div>
            <div class="doc-dates">
                <span class="date-label">Fecha:</span> {{documento.fecha_emision}}<br>
                {% if documento.fecha_vencimiento %}<span class="date-label">Vence:</span> {{documento.fecha_vencimiento}}<br>{% endif %}
                {% if documento.vendedor %}<span class="date-label">Vendedor:</span> {{documento.vendedor}}{% endif %}
            </div>
        </div>
    </div>

    <!-- INFORMACIÃ“N DEL CLIENTE -->
    <div class="client-section">
        <div class="client-header">Cliente / Proveedor</div>
        <div class="client-name">{{tercero.razon_social}}</div>
        <div class="client-info">
            NIT/CC: {{tercero.nit}}{% if tercero.direccion %} â€¢ {{tercero.direccion}}{% endif %}{% if tercero.telefono %} â€¢ Tel: {{tercero.telefono}}{% endif %}
        </div>
    </div>

    <!-- TABLA DE PRODUCTOS -->
    <table class="products-table">
        <thead>
            <tr>
                <th width="10%">CÃ³digo</th>
                <th width="40%">DescripciÃ³n del Producto/Servicio</th>
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

    <!-- TOTALES Y DISCRIMINACIÃ“N FISCAL -->
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
            
            <!-- DISCRIMINACIÃ“N DE BASES GRAVABLES -->
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
            
            <!-- DISCRIMINACIÃ“N DE IMPUESTOS -->
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
                <span class="total-label">RetenciÃ³n:</span>
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

    <!-- PIE DE PÃGINA EMPRESARIAL -->
    <div class="footer-area">
        <div class="legal-notice">
            Esta factura se asimila en todos sus efectos a una letra de cambio de conformidad con el artÃ­culo 774 del CÃ³digo de Comercio. 
            Los pagos realizados despuÃ©s del vencimiento causarÃ¡n intereses de mora segÃºn las tasas legales vigentes.
        </div>

        <div class="signature-grid">
            <div class="signature-field">
                <div class="signature-line">ElaborÃ³</div>
            </div>
            <div class="signature-field">
                <div class="signature-line">RevisÃ³</div>
            </div>
            <div class="signature-field">
                <div class="signature-line">AprobÃ³</div>
            </div>
            <div class="signature-field">
                <div class="signature-line">RecibÃ­ Conforme</div>
            </div>
        </div>

        <div class="footer-brand">
            Gracias por su confianza â€¢ Powered by ContaPY Enterprise
        </div>
    </div>
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
                content: "PÃ¡gina " counter(page) " de " counter(pages);
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
        <p><strong>Libro de Inventarios y Balances (Estado de SituaciÃ³n Financiera)</strong></p>
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
            <td>Utilidad (o PÃ©rdida) del Ejercicio</td>
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
<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">
    <title>{{documento.tipo_nombre}} - Premium</title>
    <style>
        @page {
            size: letter;
            margin: 0;
            /* Usaremos paddings internos para mayor control del diseÃ±o */
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
                    NIT: {{empresa.nit}} â€¢ RÃ©gimen ComÃºn<br>
                    {{empresa.direccion}}<br>
                    {{empresa.email}} â€¢ {{empresa.telefono}}
                </div>
            </div>
            <div class="header-right">
                <h2 class="doc-label">{{documento.tipo_nombre}}</h2>
                <div class="doc-number-box">
                    <span style="font-size: 8px; display: block; color: #94a3b8; text-transform: uppercase;">NÃºmero de
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
                <div class="section-title">Detalles de OperaciÃ³n</div>
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
                        <th width="50%">DescripciÃ³n del Servicio</th>
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
                    <strong>InformaciÃ³n de Pago:</strong><br>
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
                <strong>INFORMACIÃ“N FISCAL DIAN</strong><br>
                Software Proveedor: <strong>FINAXIS ENTERPRISE</strong> (TecnologÃ­a Cloud)<br>
                Tipo: {% if 'SOPORTE' in documento.tipo_nombre.upper() %}Documento Soporte ElectrÃ³nico{% else %}Factura
                ElectrÃ³nica de Venta{% endif %}<br>
                CUFE/CUDS:
                <span class="cufe-text">{{documento.dian_cufe}}</span>
            </div>
            <div class="fiscal-right">
                {% if documento.qr_base64 %}
                <img src="data:image/png;base64,{{documento.qr_base64}}" style="width: 80px; height: 80px;">
                {% else %}
                <div class="qr-placeholder"
                    style="display: flex; align-items: center; justify-content: center; font-size: 6px;">
                    CÃ“DIGO QR VALIDACIÃ“N
                </div>
                {% endif %}
            </div>
        </div>
        {% endif %}

        <div class="signature-line">
            Recibido por (Nombre y CÃ©dula)
        </div>

        <div class="finaxis-brand">
            Software de GestiÃ³n Inteligente â€¢ FINAXIS.COM.CO
        </div>
    </div>
</body>

</html>
''',

    'reports/invoice_template.html': r'''
<!DOCTYPE html>
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

        /* INFORMACIÃ“N CLIENTE */
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
        /* CONFIGURACIÃ“N DE PÃGINA PARA PDF (WeasyPrint) */
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

        /* SECCIÃ“N TOTALES PROFESIONAL */
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

        /* PIE DE PÃGINA EMPRESARIAL */
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
                NIT: {{empresa.nit}} â€¢ {{empresa.direccion}}<br>
                Tel: {{empresa.telefono}}{% if empresa.email %} â€¢ {{empresa.email}}{% endif %}
            </div>
        </div>

        <div class="document-section">
            <div class="doc-type">{{documento.tipo_nombre}}</div>
            <div class="doc-number">NÂ° {{documento.consecutivo}}</div>
            <div class="doc-dates">
                <span class="date-label">Fecha:</span> {{documento.fecha_emision}}<br>
                {% if documento.fecha_vencimiento %}<span class="date-label">Vence:</span>
                {{documento.fecha_vencimiento}}<br>{% endif %}
                {% if documento.vendedor %}<span class="date-label">Vendedor:</span> {{documento.vendedor}}{% endif %}
            </div>
        </div>
    </div>

    <!-- INFORMACIÃ“N DEL CLIENTE -->
    <div class="client-section">
        <div class="client-header">Cliente / Proveedor</div>
        <div class="client-name">{{tercero.razon_social}}</div>
        <div class="client-info">
            NIT/CC: {{tercero.nit}}{% if tercero.direccion %} â€¢ {{tercero.direccion}}{% endif %}{% if tercero.telefono
            %} â€¢ Tel: {{tercero.telefono}}{% endif %}
        </div>
    </div>

    <!-- TABLA DE PRODUCTOS -->
    <table class="products-table">
        <thead>
            <tr>
                <th width="10%">CÃ³digo</th>
                <th width="40%">DescripciÃ³n del Producto/Servicio</th>
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

    <!-- TOTALES Y DISCRIMINACIÃ“N FISCAL -->
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

            <!-- DISCRIMINACIÃ“N DE BASES GRAVABLES -->
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

            <!-- DISCRIMINACIÃ“N DE IMPUESTOS -->
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
                <span class="total-label">RetenciÃ³n:</span>
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

    <!-- PIE DE PÃGINA EMPRESARIAL -->
    <div class="footer-area">
        <div class="legal-notice">
            Esta factura se asimila en todos sus efectos a una letra de cambio de conformidad con el artÃ­culo 774 del
            CÃ³digo de Comercio.
            Los pagos realizados despuÃ©s del vencimiento causarÃ¡n intereses de mora segÃºn las tasas legales vigentes.
        </div>

        <div class="signature-grid">
            <div class="signature-field">
                <div class="signature-line">ElaborÃ³</div>
            </div>
            <div class="signature-field">
                <div class="signature-line">RevisÃ³</div>
            </div>
            <div class="signature-field">
                <div class="signature-line">AprobÃ³</div>
            </div>
            <div class="signature-field">
                <div class="signature-line">RecibÃ­ Conforme</div>
            </div>
        </div>

        <div class="footer-brand">
            Gracias por su confianza â€¢ Powered by ContaPY Enterprise
        </div>
    </div>
</body>

</html>
''',

    'reports/journal_report.html': r'''
<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">
    <title>Libro Diario Detallado</title>
    <style>
        @page {
            size: letter;
            margin: 1.5cm;

            @bottom-center {
                content: "PÃ¡gina " counter(page) " de " counter(pages);
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
                <th class="text-right">DÃ©bito</th>
                <th class="text-right">CrÃ©dito</th>
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
                    perÃ­odo seleccionado.</td>
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
<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">
    <title>Libro Diario Oficial</title>
    <style>
        @page {
            size: letter;
            margin: 2cm;

            @bottom-center {
                content: "PÃ¡gina " counter(page) " de " counter(pages);
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
                    <th style="width: 15%">CÃ³digo</th>
                    <th style="width: 45%">Cuenta</th>
                    <th style="width: 20%">DÃ©bitos</th>
                    <th style="width: 20%">CrÃ©ditos</th>
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
            /* Ajuste de tamaÃ±o de fuente para cabecera */
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
        <p><strong>PerÃ­odo Analizado:</strong> {{ filtros.fecha_inicio | truncate(10, True, '') }} al {{ filtros.fecha_fin | truncate(10, True, '') }}</p>
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

            {# FIX CRÃTICO DE ALINEACIÃ“N: Fila de Saldo Anterior #}
            {% set saldo_inicial_cant = data.totales.saldo_inicial_cantidad | default(0) | float %}
            {% set saldo_inicial_valor = data.totales.saldo_inicial_valor | default(0) | float %}
            
            {# FIX CRÃTICO: Evitar DivisiÃ³n por Cero en Costo Promedio Inicial #}
            {% set costo_prom_inicial = saldo_inicial_valor / saldo_inicial_cant if saldo_inicial_cant else 0.00 %}
            
            <tr class="saldo-anterior">
                <td>{{ filtros.fecha_inicio | truncate(10, True, '') }}</td>
                <td colspan="8">SALDO ANTERIOR</td> {# Â¡FIX DE ALINEACIÃ“N CRÃTICO! Fusiona 8 celdas (Col 2 a Col 9) #}

                {# Las Ãºltimas 3 columnas (Saldo, Costo Prom, Saldo Val) se mantienen alineadas #}
                <td class="text-right"><strong>{{ "%.2f"|format(saldo_inicial_cant) }}</strong></td>
                <td class="text-right"><strong>{{ costo_prom_inicial | float | format_miles }}</strong></td>
                <td class="text-right"><strong>{{ saldo_inicial_valor | float | format_miles }}</strong></td>
            </tr>

            {# Bucle de Movimientos: FIX CRÃTICO: Se usa 'data.movimientos' #}
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
        <p><strong>Balance del PerÃ­odo:</strong></p>
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
                content: "PÃ¡gina " counter(page) " de " counter(pages);
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
                <th style="width: 15%;">CÃ³digo</th>
                <th style="width: 35%;">Cuenta</th>
                <th class="text-right" style="width: 12.5%;">Saldo Anterior</th>
                <th class="text-right" style="width: 12.5%;">DÃ©bitos</th>
                <th class="text-right" style="width: 12.5%;">CrÃ©ditos</th>
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
                <td colspan="6" style="text-align: center;">No se encontraron movimientos ni saldos para el perÃ­odo
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
<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">
    <title>Reporte AnalÃ­tico de Movimientos</title>
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

        /* Para alinear nÃºmeros */
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
        <h2>Reporte AnalÃ­tico de Movimiento y Saldos</h2>
        <p>Periodo: {{ filtros.fecha_inicio }} al {{ filtros.fecha_fin }}</p>
    </div>

    <div class="filters">
        <p><strong>Filtros Aplicados:</strong></p>
        <p>Bodega: {{ bodega_nombre | default('Todas', true) }}</p>
        <p>Grupo: {{ grupo_nombre | default('Todos', true) }}</p>
        <p>ArtÃ­culo: {{ producto_nombre | default('Todos', true) }}</p>
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

    {# Filtro personalizado de Jinja2 para formatear nÃºmeros/moneda #}
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
<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">
    <title>Factura ElectrÃ³nica de Venta Premium</title>
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

        /* TIPOGRAFÃA & UTILIDADES */
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

        /* INFORMACIÃ“N ADQUIRENTE (CARD MODERNO) */
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
            /* Verde muy claro indicando Ã©xito / pago */
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

        /* SECCIÃ“N FACTURACIÃ“N ELECTRÃ“NICA DIAN */
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

        /* PIE DE PÃGINA */
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
                TelÃ©fono: {{empresa.telefono}} {% if empresa.email %}| Correo: {{empresa.email}}{% endif %}<br>
                <strong style="color:#0f172a;">Responsabilidad Tributaria:</strong> IVA RÃ©gimen ComÃºn
            </div>
        </div>

        <div class="header-right">
            <div class="doc-title">Factura ElectrÃ³nica de Venta</div>
            <div class="doc-number">NÂ° {{documento.consecutivo}}</div>
            <div class="doc-meta">
                <div class="meta-label">Fecha EmisiÃ³n:</div>
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
                <div class="adq-detail-label">DirecciÃ³n:</div>
                <div class="adq-detail-value">{{tercero.direccion|default('No registrada')}}</div>
            </div>
            <div class="adq-detail-row">
                <div class="adq-detail-label">TelÃ©fono:</div>
                <div class="adq-detail-value">{{tercero.telefono|default('No registrado')}}</div>
            </div>
        </div>
    </div>

    <!-- DETALLE DE ITEMS -->
    <table class="items-table">
        <thead>
            <tr>
                <th width="12%" class="text-left">CÃ³digo</th>
                <th width="40%" class="text-left">DescripciÃ³n del Producto o Servicio</th>
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

    <!-- BLOQUE DIAN - FACTURACIÃ“N ELECTRÃ“NICA -->
    <!-- Mostrar SIEMPRE Si existe CUFE para garantizar visibilidad de la validaciÃ³n -->
    {% if documento.dian_cufe %}
    <div class="fe-dian-section">
        <div class="fe-qr-col">
            <!-- Usamos goqr.me para crear un QR que apunte a la URL oficial de escaneo de la DIAN -->
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=https://catalogo-vpfe-hab.dian.gov.co/document/searchqr?documentkey={{documento.dian_cufe}}"
                class="qr-placeholder" alt="QR DIAN Sandbox">
        </div>
        <div class="fe-info-col">
            <div class="fe-title">âœ“ Documento ElectrÃ³nico DIAN</div>

            <div class="fe-cufe-box">
                <div class="fe-cufe-label">CUFE (CÃ³digo Ãšnico de FacturaciÃ³n ElectrÃ³nica):</div>
                <div class="fe-cufe-value">{{documento.dian_cufe}}</div>
            </div>

            <div class="fe-legal-text">
                AutorizaciÃ³n NumeraciÃ³n FacturaciÃ³n ElectrÃ³nica DIAN NO.
                <strong>{{documento.resolucion_numero}}</strong> de fecha
                <strong>{{documento.resolucion_fecha}}</strong>.
                Rango desde <strong>{{documento.resolucion_prefijo}}-{{documento.resolucion_rango_desde}}</strong> hasta
                <strong>{{documento.resolucion_prefijo}}-{{documento.resolucion_rango_hasta}}</strong>.
                Esta factura se asimila en todos sus efectos a una letra de cambio segÃºn el Art. 774 del CÃ³digo de
                Comercio.
                Transcurridos 3 dÃ­as hÃ¡biles desde su recepciÃ³n, si no hay reclamaciÃ³n en contra, se entenderÃ¡ aceptada
                y constituirÃ¡ tÃ­tulo ejecutivo.
            </div>


        </div>
    </div>
    {% endif %}

    <div class="commercial-footer">
        Finaxis Enterprise Software - Sistema Integral de FacturaciÃ³n ElectrÃ³nica DIAN
    </div>

</body>

</html>
''',

    'reports/rentabilidad_documento_report.html': r'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Rentabilidad por Documento</title>
    <style>
        @page { size: letter landscape; margin: 1cm; }
        body { font-family: 'Helvetica', 'Arial', sans-serif; font-size: 9pt; color: #333; line-height: 1.4; }
        .header { text-align: center; margin-bottom: 20px; border-bottom: 2px solid #444; padding-bottom: 10px; }
        .header h1 { font-size: 18pt; margin: 0; color: #000; }
        .header p { font-size: 10pt; margin: 2px 0; color: #666; }
        
        .header-section { text-align: center; margin-bottom: 15px; }
        .header-section h1 { font-size: 16pt; color: #2c3e50; text-transform: uppercase; margin: 0; }

        .info-box { display: table; width: 100%; border: 1px solid #ddd; padding: 10px; margin-bottom: 15px; border-radius: 5px; background-color: #fcfcfc; }
        .info-box div { display: table-cell; width: 50%; vertical-align: top; }
        .info-box p { margin: 3px 0; font-size: 9pt; }
        
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; table-layout: fixed; }
        th, td { border: 1px solid #ccc; padding: 6px 4px; text-align: left; word-wrap: break-word; }
        th { background-color: #f2f2f2; font-weight: bold; font-size: 8pt; text-transform: uppercase; color: #444; text-align: center; }
        td { font-size: 8pt; }
        
        .right { text-align: right; }
        .center { text-align: center; }
        .mono { font-family: 'Courier New', monospace; font-weight: bold; }
        .footer { margin-top: 30px; border-top: 1px solid #ccc; padding-top: 10px; font-size: 8pt; color: #777; text-align: center; }
        .totals-row td { font-weight: bold; background-color: #eee; font-size: 9pt; border-top: 2px solid #444; }
        .negative { color: #d9534f; background-color: #f9f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ empresa.razon_social }}</h1>
        <p>NIT: {{ empresa.nit }}</p>
        <p>Reporte Generado: {{ now()|date("%d/%m/%Y %H:%M") }}</p>
    </div>

    <div class="header-section">
        <h1>Análisis de Rentabilidad por Documento</h1>
    </div>

    <div class="info-box">
        <div>
            <p><strong>Documento Auditado:</strong> {{ data.documento_ref }}</p>
            <p><strong>Tercero:</strong> {{ data.tercero_nombre }}</p>
        </div>
        <div>
            <p><strong>Fecha de Documento:</strong> {{ data.fecha|date("%d/%m/%Y") }}</p>
            <p><strong>Filtro Usado:</strong> Código {{ filtros.tipo_documento_codigo|default('N/A') }} y Número {{ filtros.numero_documento|default('N/A') }}</p>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th style="width: 6%;">CÓDIGO</th>
                <th style="width: 15%;">ARTÍCULO</th>
                <th class="right" style="width: 5%;">CANT.</th>
                <th class="right" style="width: 8%;">VTA. UNIT.</th>
                <th class="right" style="width: 8%;">COSTO UNIT.</th>
                <th class="right" style="width: 15%;">VTA. TOTAL</th>
                <th class="right" style="width: 15%;">COSTO TOTAL</th>
                <th class="right" style="width: 12%;">UTILIDAD</th>
                <th class="center" style="width: 16%;">MARGEN%</th>
            </tr>
        </thead>
        <tbody>
            {% for item in data.detalle %}
            <tr class="{% if item.utilidad_bruta_valor|default(0) < 0 %}negative{% endif %}">
                <td class="mono">{{ item.producto_codigo }}</td>
                <td>{{ item.producto_nombre }}</td>
                <td class="right mono">{{ item.cantidad|format_decimal(0) }}</td>
                <td class="right mono">{{ item.valor_venta_unitario|format_currency(0) }}</td>
                <td class="right mono">{{ item.costo_unitario|format_currency(0) }}</td>
                <td class="right mono">{{ item.valor_venta_total|format_currency(0) }}</td>
                <td class="right mono">{{ item.costo_total|format_currency(0) }}</td>
                <td class="right mono">{{ item.utilidad_bruta_valor|format_currency(0) }}</td>
                <td class="center mono">{{ item.utilidad_bruta_porcentaje|format_decimal(2) }}%</td>
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
                <td class="right mono">{{ data.totales.total_venta|default(0)|format_currency(0) }}</td>
                <td class="right mono">{{ data.totales.total_costo|default(0)|format_currency(0) }}</td>
                <td class="right mono">{{ data.totales.total_utilidad_bruta_valor|default(0)|format_currency(0) }}</td>
                <td class="center mono">{{ data.totales.total_utilidad_bruta_porcentaje|default(0)|format_decimal(2) }}%</td>
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
                <th style="width: 10%;">Fecha</th>
                <th style="width: 13%;">Documento</th>
                <th class="text-right" style="width: 5%;">Cant.</th>
                <th class="text-right" style="width: 8%;">Venta Unit.</th>
                <th class="text-right" style="width: 15%;">Venta Total</th>
                <th class="text-right" style="width: 8%;">Costo Unit.</th>
                <th class="text-right" style="width: 15%;">Costo Total</th>
                <th class="text-right" style="width: 11%;">Utilidad Bruta</th>
                <th class="text-right" style="width: 15%;">% Margen</th>
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
            size: letter landscape; /* Paisaje para mÃ¡s columnas */
            margin: 1.5cm;
        }
        body {
            font-family: 'Helvetica', 'Arial', sans-serif;
            font-size: 8pt; /* TamaÃ±o reducido para caber mÃ¡s info */
            color: #333;
        }
        .header {
            text-align: center;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
            margin-bottom: 15px; /* Reducido margen */
        }
        .header h1 { margin: 0; font-size: 14pt; }
        .header h2 { margin: 0; font-size: 11pt; font-weight: normal; }
        .info {
            margin-bottom: 15px; /* Reducido margen */
            text-align: center;
            font-size: 9pt; /* Reducido tamaÃ±o */
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
        .nowrap { white-space: nowrap; } /* Para columnas de ID/CÃ³digo */
        tfoot td {
            font-weight: bold;
            background-color: #e8e8e8;
            border-top: 2px solid #333;
        }
        /* Clases para formato numÃ©rico */
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
        <p><strong>PerÃ­odo Analizado:</strong> {{ filtros.fecha_inicio }} al {{ filtros.fecha_fin }}</p>
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
    <title>Reporte de GestiÃ³n de Ventas</title>
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
        <h2>Reporte de GestiÃ³n de Ventas</h2>
        <p>PerÃ­odo del {{ data.filtros.fecha_inicio }} al {{ data.filtros.fecha_fin }}</p>
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
        /* FORZAR ORIENTACIÃ“N HORIZONTAL PARA MOVIMIENTOS DETALLADOS */
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

        /* --- Estilos EspecÃ­ficos para cada Vista --- */

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
        <p>TelÃ©fono: (pendiente)</p>
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
                    <th>CÃ³digo</th>
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
    <title>AuditorÃ­a Contable Avanzada</title>
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

        /* Se eliminÃ³ el tachado */

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
                    bÃºsqueda.</td>
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

    'reports/tercero_account_ledger_report.html': r'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Auxiliar por Tercero y Cuenta</title>
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=DM+Sans:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --green-inst: #1C3A18;
            --green-light: #2D5A27;
            --gold-soft: #C9A84C;
            --white: #FFFFFF;
            --bg-page: #FAFAF7;
            --text-main: #1C3A18;
            --text-labels: #444444;
            --bg-accent: #F2F5F1;
        }

        @page {
            size: A4 portrait;
            margin: 0;
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
            width: 210mm;
            min-height: 297mm;
            margin: 0 auto;
            position: relative;
            box-sizing: border-box;
            background-color: var(--white);
            padding-bottom: 30px;
        }

        .decor-bar-top {
            height: 6px;
            background: linear-gradient(90deg, var(--green-inst), var(--green-light), var(--gold-soft), var(--green-light), var(--green-inst));
            width: 100%;
        }

        .decor-bar-bottom {
            height: 4px;
            background: linear-gradient(90deg, var(--green-inst), var(--gold-soft));
            width: 100%;
            position: absolute;
            bottom: 0;
        }

        header {
            padding: 30px 30px 15px 30px;
            display: table;
            width: 100%;
            box-sizing: border-box;
        }

        .header-left { display: table-cell; vertical-align: middle; text-align: left; }
        .header-right { display: table-cell; vertical-align: middle; text-align: right; }

        .badge-premium {
            font-size: 10px;
            font-weight: 700;
            color: var(--green-inst);
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 4px;
            display: block;
        }
        .badge-premium::before { content: "•"; margin-right: 6px; color: var(--gold-soft); }

        .company-name {
            font-family: 'Cormorant Garamond', serif;
            font-size: 32px;
            font-weight: 700;
            line-height: 1;
            margin: 0;
            color: var(--green-inst);
        }
        .company-nit {
            font-size: 11px;
            color: #888;
            margin-top: 2px;
            letter-spacing: 1px;
        }

        .report-title-box {
            text-align: right;
        }
        .doc-title {
            font-family: 'Cormorant Garamond', serif;
            font-size: 24px;
            font-style: italic;
            color: #444;
            margin-bottom: 6px;
        }
        .date-range-badge {
            display: inline-block;
            border: 1px solid var(--green-inst);
            padding: 4px 10px;
            border-radius: 2px;
        }
        .date-range-text { font-size: 13px; font-weight: 700; color: var(--green-inst); }

        .tercero-ribbon {
            background-color: var(--green-inst);
            color: var(--white);
            padding: 12px 30px;
            font-size: 13px;
            margin-bottom: 20px;
        }
        .tercero-ribbon strong { color: var(--gold-soft); }

        main { padding: 0 30px; }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }

        thead th {
            background-color: #F8F9F7;
            color: var(--text-labels);
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 10px 8px;
            border-bottom: 2px solid var(--green-inst);
            text-align: left;
        }

        tbody td {
            padding: 8px;
            font-size: 11px;
            border-bottom: 1px solid #EEE;
            color: #333;
            vertical-align: middle;
        }

        .row-alt { background-color: #FCFCFB; }
        .text-right { text-align: right !important; }
        .text-center { text-align: center !important; }
        
        .cuenta-header {
            background-color: #F4F6F2;
            font-weight: 700;
            color: var(--green-inst);
            font-size: 12px;
        }

        .saldo-ant-row {
            font-style: italic;
            color: #666;
            font-size: 10px;
        }

        .total-section {
            background-color: var(--green-inst);
            color: var(--white);
            font-weight: 700;
            font-size: 12px;
        }
        .total-section td { border: none; padding: 12px 8px; color: var(--white) !important; }
        .gold-label { color: var(--gold-soft); text-transform: uppercase; letter-spacing: 1px; font-size: 10px; }
    </style>
</head>
<body>
    <div class="page-container">
        <div class="decor-bar-top"></div>
        
        <header>
            <div class="header-left">
                <span class="badge-premium">Inteligencia Financiera</span>
                <h1 class="company-name">{{ empresa_nombre or 'VERDURAS LA 21' }}</h1>
                <div class="company-nit">NIT: {{ empresa_nit or '901464119-7' }}</div>
            </div>
            <div class="header-right">
                <div class="report-title-box">
                    <div class="doc-title">Auxiliar por Tercero y Cuenta</div>
                    <div class="date-range-badge">
                        <span class="date-range-text">Del {{ fecha_inicio }} al {{ fecha_fin }}</span>
                    </div>
                </div>
            </div>
        </header>

        <div class="tercero-ribbon">
            <strong>TERCERO SELECCIONADO:</strong> {{ tercero_info.nit }} &#8212; {{ tercero_info.razon_social }}
        </div>

        <main>
            <table>
                <thead>
                    <tr>
                        <th width="10%">Fecha</th>
                        <th width="12%">Documento</th>
                        <th>Concepto</th>
                        {% if has_cost_centers %}
                        <th width="10%">C. Costo</th>
                        {% endif %}
                        <th width="12%" class="text-right">D&eacute;bito</th>
                        <th width="12%" class="text-right">Cr&eacute;dito</th>
                        <th width="12%" class="text-right">Saldo Parcial</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="cuenta-header">
                        <td colspan="{{ 6 if has_cost_centers else 5 }}">SALDO ANTERIOR GLOBAL</td>
                        <td class="text-right">{{ "{:,.0f}".format(saldo_anterior_global).replace(',', '.') }}</td>
                    </tr>

                    {% for cuenta_id, grupo_movimientos in movimientos | groupby('cuenta_id') %}
                    {% set movimientos_lista = list(grupo_movimientos) %}
                    {% set primer_mov = movimientos_lista[0] %}
                    <tr class="cuenta-header" style="background-color: #EEE; color: #333; font-size: 9px;">
                        <td colspan="{{ 7 if has_cost_centers else 6 }}">
                            Cuenta: {{ primer_mov.cuenta_codigo }} &#8212; {{ primer_mov.cuenta_nombre }}
                        </td>
                    </tr>
                    <tr class="saldo-ant-row">
                        <td colspan="{{ 6 if has_cost_centers else 5 }}">Saldo Inicial de la Cuenta</td>
                        <td class="text-right">
                            {{ "{:,.0f}".format(saldos_iniciales_por_cuenta.get(cuenta_id | string, 0)).replace(',', '.') }}
                        </td>
                    </tr>

                    {% for mov in movimientos_lista %}
                    <tr class="{{ 'row-alt' if loop.index0 % 2 == 0 else '' }}">
                        <td class="text-center">{{ mov.fecha.strftime('%Y-%m-%d') if mov.fecha else '' }}</td>
                        <td style="font-weight: 700; color: var(--green-light);">{{ mov.tipo_documento }}-{{ mov.numero_documento }}</td>
                        <td style="font-size: 8px;">{{ mov.concepto }}</td>
                        {% if has_cost_centers %}
                        <td class="text-center" style="color: #888;">{{ mov.centro_costo_codigo or '-' }}</td>
                        {% endif %}
                        <td class="text-right">{{ "{:,.0f}".format(mov.debito).replace(',', '.') }}</td>
                        <td class="text-right">{{ "{:,.0f}".format(mov.credito).replace(',', '.') }}</td>
                        <td class="text-right">{{ "{:,.0f}".format(mov.saldo_parcial).replace(',', '.') }}</td>
                    </tr>
                    {% endfor %}
                    {% endfor %}

                    <tr class="cuenta-header">
                        <td colspan="{{ 4 if has_cost_centers else 3 }}">TOTALES MOVIMIENTOS PERIODO</td>
                        <td class="text-right">{{ "{:,.0f}".format(total_debito_global).replace(',', '.') }}</td>
                        <td class="text-right">{{ "{:,.0f}".format(total_credito_global).replace(',', '.') }}</td>
                        <td></td>
                    </tr>

                    <tr class="total-section">
                        <td colspan="{{ 6 if has_cost_centers else 5 }}">
                            <span class="gold-label">Consolidado Final</span><br>
                            SALDO FINAL GLOBAL AL {{ fecha_fin }}
                        </td>
                        {% set saldo_final_global = (movimientos[-1].saldo_parcial if movimientos else saldo_anterior_global) %}
                        <td class="text-right" style="font-size: 14px;">
                            {{ "{:,.0f}".format(saldo_final_global).replace(',', '.') }}
                        </td>
                    </tr>
                </tbody>
            </table>
        </main>
        <div class="decor-bar-bottom"></div>
    </div>
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
                <th style="width: 10%;">CÃ³d.</th>
                <th style="width: 30%;">Producto</th>
                <th style="width: 15%;" class="text-right">Saldo Actual</th>
                <th style="width: 10%;" class="text-right">Stock MÃ­n.</th>
                <th style="width: 10%;" class="text-right">Stock MÃ¡x.</th>
                <th style="width: 15%;" class="text-right">Diferencia</th>
                <th style="width: 10%;" class="text-center">DecisiÃ³n</th>
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
    
    <h2>Total ArtÃ­culos en Alerta: {{ data | length }}</h2>

</body>
</html>
''',

    'reports/ventas_cliente_report.html': r'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Reporte Integral de Ventas por Cliente</title>
    <style>
        @page { size: letter landscape; margin: 1cm; }
        body { font-family: 'Helvetica', sans-serif; font-size: 9pt; color: #333; }
        .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 15px; }
        .header h1 { margin: 0; font-size: 14pt; }
        .header h2 { margin: 2px 0; font-size: 11pt; font-weight: normal; }
        .info { margin-bottom: 15px; text-align: center; font-size: 9pt; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        th, td { border: 1px solid #ccc; padding: 4px; text-align: left; }
        th { background-color: #f2f2f2; font-weight: bold; text-align: center; }
        .text-right { text-align: right; }
        .text-center { text-align: center; }
        .bg-totals { background-color: #e8e8e8; font-weight: bold; border-top: 2px solid #333; }
        .client-header { background-color: #d9edf7; font-weight: bold; }
        .detail-table { width: 95%; margin: 5px auto; font-size: 8pt; background-color: #fcfcfc;}
        .detail-table th { background-color: #e0e0e0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ empresa.razon_social }}</h1>
        <h2>Reporte Integral de Ventas por Cliente</h2>
    </div>

    <div class="info">
        <p><strong>Período:</strong> {{ filtros.fecha_inicio }} al {{ filtros.fecha_fin }}</p>
    </div>

    <table>
        <thead>
            <tr>
                <th style="width: 10%">NIT</th>
                <th style="width: 25%">Cliente</th>
                <th style="width: 8%; font-size: 8pt;">Venta Total</th>
                <th style="width: 4%; font-size: 8pt;">% Vta</th>
                <th style="width: 4%; font-size: 8pt;">% Util</th>
                <th style="width: 8%; font-size: 8pt;">Costo Total</th>
                <th style="width: 8%; font-size: 8pt;">Utilidad Total</th>
                <th style="width: 5%; font-size: 8pt;">Margen</th>
                <th style="width: 8%; font-size: 8pt;">Cant. Ítems</th>
                <th style="width: 6%; font-size: 8pt;">Facturas</th>
            </tr>
        </thead>
        <tbody>
            {% for item in data.items %}
            <tr class="client-header">
                <td>{{ item.tercero_identificacion }}</td>
                <td>{{ item.tercero_nombre }}</td>
                <td class="text-right">${{ "{:,.0f}".format(item.total_venta) }}</td>
                {% set pct_vta = ((item.total_venta / data.gran_total_venta * 100) | round | int) if data.gran_total_venta else 0 %}
                <td class="text-right" style="color:#3730a3;font-weight:bold;">{{ pct_vta }}%</td>
                {% set pct_util = ((item.total_utilidad / (data.gran_total_utilidad | abs) * 100) | round | int) if data.gran_total_utilidad else 0 %}
                <td class="text-right" style="color:{% if item.total_utilidad < 0 %}red{% else %}#065f46{% endif %};font-weight:bold;">{{ pct_util }}%</td>
                <td class="text-right">${{ "{:,.0f}".format(item.total_costo) }}</td>
                <td class="text-right" style="color:{% if item.total_utilidad < 0 %}red{% endif %}">${{ "{:,.0f}".format(item.total_utilidad) }}</td>
                <td class="text-right">{{ "%.2f"|format(item.margen_porcentaje) }}%</td>
                <td class="text-right">{{ "%.2f"|format(item.cantidad_items) }}</td>
                <td class="text-center">{{ item.conteo_documentos }}</td>
            </tr>
            {% if item.detalle_productos %}
            <tr>
                <td colspan="10" style="padding: 0;">
                    <table class="detail-table">
                        <thead>
                            <tr>
                                <th style="width: 15%">Código</th>
                                <th style="width: 30%">Producto</th>
                                <th style="width: 10%">Cantidad</th>
                                <th style="width: 15%">Venta Total</th>
                                <th style="width: 15%">Costo Total</th>
                                <th style="width: 15%">Utilidad</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for prod in item.detalle_productos %}
                            <tr>
                                <td>{{ prod.producto_codigo }}</td>
                                <td>{{ prod.producto_nombre }}</td>
                                <td class="text-right">{{ "%.2f"|format(prod.cantidad) }}</td>
                                <td class="text-right">${{ "{:,.0f}".format(prod.total_venta) }}</td>
                                <td class="text-right">${{ "{:,.0f}".format(prod.total_costo) }}</td>
                                <td class="text-right">${{ "{:,.0f}".format(prod.utilidad) }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </td>
            </tr>
            {% endif %}
            {% else %}
            <tr>
                <td colspan="10" class="text-center">No se encontraron ventas para los filtros seleccionados.</td>
            </tr>
            {% endfor %}
        </tbody>
        <tfoot>
            <tr class="bg-totals">
                <td colspan="2" class="text-right">TOTALES GENERALES</td>
                <td class="text-right">${{ "{:,.0f}".format(data.gran_total_venta) }}</td>
                <td class="text-right" style="color:#3730a3;font-weight:bold;">100%</td>
                <td class="text-right" style="color:#065f46;font-weight:bold;">{{ '−' if data.gran_total_utilidad < 0 else '' }}100%</td>
                <td class="text-right">${{ "{:,.0f}".format(data.gran_total_costo) }}</td>
                <td class="text-right">${{ "{:,.0f}".format(data.gran_total_utilidad) }}</td>
                <td class="text-right">{{ "%.2f"|format(data.margen_global_porcentaje) }}%</td>
                <td colspan="2"></td>
            </tr>
        </tfoot>
    </table>
</body>
</html>
'''
}
