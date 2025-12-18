
NOMINA_RESUMEN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        @page { size: letter landscape; margin: 1cm; }
        body { font-family: Arial, sans-serif; font-size: 10px; color: #333; }
        .header { text-align: center; margin-bottom: 20px; border-bottom: 2px solid #eee; padding-bottom: 10px; }
        .header h2 { margin: 0; color: #444; }
        .header p { margin: 2px 0; color: #666; }
        
        table { width: 100%; border-collapse: collapse; margin-bottom: 15px; }
        th { background: #eee; text-align: left; padding: 6px; font-weight: bold; border-bottom: 1px solid #ddd; font-size: 9px; }
        td { padding: 6px; border-bottom: 1px solid #eee; font-size: 10px; }
        .num { text-align: right; }
        .total-row td { border-top: 2px solid #ccc; font-weight: bold; font-size: 11px; background: #fdfdfd; }
        
        .footer { margin-top: 20px; border-top: 1px dashed #ccc; padding-top: 5px; text-align: center; font-size: 9px; color: #999; }
    </style>
</head>
<body>
    <div class="header">
        <h2>{{ empresa.nombre }}</h2>
        <p>NIT: {{ empresa.nit }}</p>
        <h3>Resumen de Nómina - Período {{ periodo }}</h3>
    </div>

    <table>
        <thead>
            <tr>
                <th>Empleado</th>
                <th>Doc</th>
                <th class="num">Días</th>
                <th class="num">Básico</th>
                <th class="num">Aux. Trans.</th>
                <th class="num">Extras</th>
                <th class="num">Comis.</th>
                <th class="num">Otros Dev.</th>
                <th class="num" style="background: #e3f2fd;">Total Dev.</th>
                <th class="num">Salud</th>
                <th class="num">Pensión</th>
                <th class="num">FSP</th>
                <th class="num">Otras Ded.</th>
                <th class="num" style="background: #ffebee;">Total Ded.</th>
                <th class="num" style="background: #e8f5e9;">NETO PAGAR</th>
            </tr>
        </thead>
        <tbody>
            {% for item in detalles %}
            <tr>
                <td>{{ item.nombre }}</td>
                <td>{{ item.documento }}</td>
                <td class="num">{{ item.dias }}</td>
                <td class="num">{{ item.basico_fmt }}</td>
                <td class="num">{{ item.auxilio_fmt }}</td>
                <td class="num">{{ item.extras_fmt }}</td>
                <td class="num">{{ item.comisiones_fmt }}</td>
                <td class="num">{{ item.otros_dev_fmt }}</td>
                <td class="num" style="font-weight:bold;">{{ item.total_dev_fmt }}</td>
                <td class="num">{{ item.salud_fmt }}</td>
                <td class="num">{{ item.pension_fmt }}</td>
                <td class="num">{{ item.fsp_fmt }}</td>
                <td class="num">{{ item.otras_ded_fmt }}</td>
                <td class="num" style="font-weight:bold;">{{ item.total_ded_fmt }}</td>
                <td class="num" style="font-weight:bold; color: #2e7d32;">{{ item.neto_fmt }}</td>
            </tr>
            {% endfor %}
        </tbody>
        <tfoot>
            <tr class="total-row">
                <td colspan="3" style="text-align: right; padding-right: 10px;">TOTALES GENERALES</td>
                <td class="num">{{ totales.basico_fmt }}</td>
                <td class="num">{{ totales.auxilio_fmt }}</td>
                <td class="num">{{ totales.extras_fmt }}</td>
                <td class="num">{{ totales.comisiones_fmt }}</td>
                <td class="num">{{ totales.otros_dev_fmt }}</td>
                <td class="num">{{ totales.total_dev_fmt }}</td>
                <td class="num">{{ totales.salud_fmt }}</td>
                <td class="num">{{ totales.pension_fmt }}</td>
                <td class="num">{{ totales.fsp_fmt }}</td>
                <td class="num">{{ totales.otras_ded_fmt }}</td>
                <td class="num">{{ totales.total_ded_fmt }}</td>
                <td class="num" style="color: #2e7d32;">{{ totales.neto_fmt }}</td>
            </tr>
        </tfoot>
    </table>

    <div class="footer">
        Generado por Finaxis Software Contable - {{ fecha_generacion }}
    </div>
</body>
</html>
"""
