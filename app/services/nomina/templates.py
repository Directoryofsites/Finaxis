NOMINA_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        @page { size: letter; margin: 2cm; }
        body { font-family: Arial, sans-serif; font-size: 11px; color: #333; }
        .header { text-align: center; margin-bottom: 20px; border-bottom: 2px solid #eee; padding-bottom: 10px; }
        .header h2 { margin: 0; color: #444; }
        .header p { margin: 2px 0; color: #666; }
        
        .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }
        .info-box { background: #f9f9f9; padding: 10px; border-radius: 4px; border: 1px solid #eee; }
        .info-box strong { display: block; margin-bottom: 4px; color: #555; }
        
        table { width: 100%; border-collapse: collapse; margin-bottom: 15px; }
        th { background: #eee; text-align: left; padding: 8px; font-weight: bold; border-bottom: 1px solid #ddd; }
        td { padding: 8px; border-bottom: 1px solid #eee; }
        .num { text-align: right; }
        .total-row td { border-top: 2px solid #ccc; font-weight: bold; font-size: 12px; }
        
        .footer { margin-top: 40px; border-top: 1px dashed #ccc; padding-top: 10px; text-align: center; font-size: 10px; color: #999; }
        .signatures { margin-top: 50px; display: grid; grid-template-columns: 1fr 1fr; gap: 50px; }
        .sign-line { border-top: 1px solid #ccc; padding-top: 5px; text-align: center; }
    </style>
</head>
<body>
    <div class="header">
        <h2>{{ empresa.nombre }}</h2>
        <p>NIT: {{ empresa.nit }} - {{ empresa.dv }}</p>
        <h3>Desprendible de Pago de Nómina</h3>
    </div>

    <div class="info-grid">
        <div class="info-box">
            <strong>Empleado:</strong> {{ empleado.nombre }}<br>
            <strong>Documento:</strong> {{ empleado.documento }}<br>
            <strong>Cargo:</strong> {{ empleado.cargo or 'N/A' }}
        </div>
        <div class="info-box">
            <strong>Período:</strong> {{ periodo }}<br>
            <strong>Fecha de Pago:</strong> {{ fecha_pago }}<br>
            <strong>Días Trabajados:</strong> {{ dias_trabajados }}
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Concepto</th>
                <th class="num">Devengados</th>
                <th class="num">Deducciones</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Sueldo Básico</td>
                <td class="num">{{ sueldo_fmt }}</td>
                <td class="num"></td>
            </tr>
            {% if auxilio > 0 %}
            <tr>
                <td>Auxilio de Transporte</td>
                <td class="num">{{ auxilio_fmt }}</td>
                <td class="num"></td>
            </tr>
            {% endif %}
            {% if extras > 0 %}
            <tr>
                <td>Horas Extras / Recargos</td>
                <td class="num">{{ extras_fmt }}</td>
                <td class="num"></td>
            </tr>
            {% endif %}
            {% if comisiones > 0 %}
            <tr>
                <td>Comisiones</td>
                <td class="num">{{ comisiones_fmt }}</td>
                <td class="num"></td>
            </tr>
            {% endif %}
            {% if otros_devengados > 0 %}
            <tr>
                <td>Otros Devengados</td>
                <td class="num">{{ otros_devengados_fmt }}</td>
                <td class="num"></td>
            </tr>
            {% endif %}
            
            <!-- DEDUCCIONES -->
            <tr>
                <td>Aporte Salud (4%)</td>
                <td class="num"></td>
                <td class="num">{{ salud_fmt }}</td>
            </tr>
            <tr>
                <td>Aporte Pensión (4%)</td>
                <td class="num"></td>
                <td class="num">{{ pension_fmt }}</td>
            </tr>
            {% if fsp > 0 %}
            <tr>
                <td>Fondo Solidaridad Pensional</td>
                <td class="num"></td>
                <td class="num">{{ fsp_fmt }}</td>
            </tr>
            {% endif %}
            {% if otras_deducciones > 0 %}
            <tr>
                <td>Otras Deducciones/Préstamos</td>
                <td class="num"></td>
                <td class="num">{{ otras_deducciones_fmt }}</td>
            </tr>
            {% endif %}
        </tbody>
        <tfoot>
            <tr class="total-row">
                <td style="text-align: right; padding-right: 20px;">TOTALES</td>
                <td class="num">{{ total_devengado_fmt }}</td>
                <td class="num">{{ total_deducciones_fmt }}</td>
            </tr>
        </tfoot>
    </table>

    <div style="background: #eefdf0; padding: 15px; border-radius: 5px; border: 1px solid #bcebc6; text-align: right; font-size: 14px; margin-top: 10px;">
        <strong>NETO A PAGAR:</strong> <span style="font-size: 18px; color: #2e7d32; margin-left: 10px;">{{ neto_fmt }}</span>
    </div>

    <div class="signatures">
        <div class="sign-line">Firma Empleador</div>
        <div class="sign-line">Firma Empleado (Recibí Conforme)</div>
    </div>
    
    <div class="footer">
        Generado por Finaxis Software Contable
    </div>
</body>
</html>
"""

NOMINA_EMPLEADOS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        @page { size: letter; margin: 2cm; }
        body { font-family: 'Helvetica', Arial, sans-serif; font-size: 10px; color: #333; }
        .header { text-align: center; margin-bottom: 30px; border-bottom: 2px solid #5a67d8; padding-bottom: 10px; }
        .header h1 { margin: 0; color: #2d3748; font-size: 18px; text-transform: uppercase; }
        .header p { margin: 2px 0; color: #718096; font-size: 10px; }
        
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th { background: #5a67d8; color: white; text-align: left; padding: 10px; font-weight: bold; font-size: 9px; text-transform: uppercase; }
        td { padding: 8px 10px; border-bottom: 1px solid #e2e8f0; font-size: 10px; vertical-align: middle; }
        tr:nth-child(even) { background-color: #f7fafc; }
        
        .currency { font-family: monospace; text-align: right; }
        .status-active { color: #2f855a; font-weight: bold; }
        .status-inactive { color: #c53030; }
        
        .footer { position: fixed; bottom: 0; left: 0; right: 0; text-align: center; font-size: 8px; color: #cbd5e0; padding: 10px; border-top: 1px solid #eee; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ empresa.nombre }}</h1>
        <p>NIT: {{ empresa.nit }} - Reporte Generado: {{ fecha_generacion }}</p>
        <h2 style="font-size: 14px; color: #5a67d8; margin-top: 10px;">DIRECTORIO DE EMPLEADOS ACITVOS</h2>
        {% if tipo_nomina %}
        <p style="font-weight: bold;">FILTRO: NÓMINA {{ tipo_nomina|upper }}</p>
        {% endif %}
    </div>

    <table>
        <thead>
            <tr>
                <th>Documento</th>
                <th>Empleado</th>
                <th>Cargo</th>
                <th>Fecha Ingreso</th>
                <th>Tipo Nómina</th>
                <th class="currency">Salario Base</th>
                <th class="currency">Aux. Transp.</th>
            </tr>
        </thead>
        <tbody>
            {% for emp in empleados %}
            <tr>
                <td>{{ emp.documento }}</td>
                <td>
                    <strong>{{ emp.nombre_completo }}</strong><br>
                    <span style="color: #718096; font-size: 8px;">{{ emp.email or '' }}</span>
                </td>
                <td>{{ emp.cargo }}</td>
                <td>{{ emp.fecha_ingreso }}</td>
                <td>{{ emp.tipo_nomina }}</td>
                <td class="currency" style="font-weight: bold;">{{ emp.salario_fmt }}</td>
                <td class="currency">{{ "SÍ" if emp.auxilio else "NO" }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <div style="margin-top: 30px; font-size: 10px; color: #718096;">
        <p><strong>Total Empleados Listados:</strong> {{ empleados|length }}</p>
    </div>

    <div class="footer">
        Generado por Finaxis Software Contable
    </div>
</body>
</html>
"""

