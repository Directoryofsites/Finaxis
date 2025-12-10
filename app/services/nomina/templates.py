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
