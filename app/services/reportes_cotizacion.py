from sqlalchemy.orm import Session
from fastapi import HTTPException
from weasyprint import HTML
from jinja2 import Environment, select_autoescape
from app.models.cotizacion import Cotizacion
from app.models.empresa import Empresa
from datetime import datetime

# --- TEMPLATE HTML INLINE ---
COTIZACION_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Cotización {{ cotizacion.numero }}</title>
    <style>
        @page { size: letter; margin: 2cm; }
        body { font-family: sans-serif; font-size: 12px; color: #333; }
        .header-table { width: 100%; margin-bottom: 20px; }
        .company-name { font-size: 20px; font-weight: bold; color: #2c3e50; }
        .doc-title { font-size: 24px; font-weight: bold; text-align: right; color: #7f8c8d; }
        .doc-info { text-align: right; }
        .client-box { border: 1px solid #ddd; padding: 10px; border-radius: 5px; margin-bottom: 20px; background-color: #f9f9f9; }
        .items-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        .items-table th { background-color: #2c3e50; color: white; padding: 8px; text-align: left; }
        .items-table td { border-bottom: 1px solid #eee; padding: 8px; }
        .text-right { text-align: right; }
        .totals-table { width: 40%; margin-left: auto; border-collapse: collapse; }
        .totals-table td { padding: 5px; }
        .total-row { font-weight: bold; font-size: 14px; border-top: 2px solid #333; }
        .footer { margin-top: 50px; font-size: 10px; color: #777; border-top: 1px solid #eee; padding-top: 10px; text-align: center; }
    </style>
</head>
<body>
    <table class="header-table">
        <tr>
            <td valign="top">
                <div class="company-name">{{ empresa.razon_social }}</div>
                <div>NIT: {{ empresa.nit }}</div>
                <div>{{ empresa.direccion or '' }}</div>
                <div>{{ empresa.telefono or '' }}</div>
                <div>{{ empresa.email or '' }}</div>
            </td>
            <td valign="top" class="doc-info">
                <div class="doc-title">COTIZACIÓN</div>
                <div style="font-size: 16px; color: #c0392b;"># {{ cotizacion.numero }}</div>
                <br>
                <div><strong>Fecha:</strong> {{ cotizacion.fecha }}</div>
                {% if cotizacion.fecha_vencimiento %}
                <div><strong>Vence:</strong> {{ cotizacion.fecha_vencimiento }}</div>
                {% endif %}
            </td>
        </tr>
    </table>

    <div class="client-box">
        <div style="font-weight: bold; margin-bottom: 5px; color: #2c3e50;">CLIENTE</div>
        <div>{{ cotizacion.tercero.razon_social }}</div>
        <div>NIT/CC: {{ cotizacion.tercero.numero_identificacion }}</div>
        <div>{{ cotizacion.tercero.direccion or '' }}</div>
        <div>{{ cotizacion.tercero.telefono or '' }}</div>
    </div>

    <table class="items-table">
        <thead>
            <tr>
                <th>Producto / Descripción</th>
                <th class="text-right">Cant.</th>
                <th class="text-right">Precio Unit.</th>
                <th class="text-right">Total</th>
            </tr>
        </thead>
        <tbody>
            {% for item in cotizacion.detalles %}
            <tr>
                <td>
                    <b>{{ item.producto.codigo if item.producto else '' }}</b> - 
                    {{ item.producto.nombre if item.producto else 'Item desconocido' }}
                </td>
                <td class="text-right">{{ item.cantidad }}</td>
                <td class="text-right">{{ "{:,.0f}".format(item.precio_unitario) }}</td>
                <td class="text-right">{{ "{:,.0f}".format(item.cantidad * item.precio_unitario) }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <table class="totals-table">
        <tr class="total-row">
            <td>TOTAL ESTIMADO</td>
            <td class="text-right">{{ "{:,.0f}".format(cotizacion.total_estimado) }}</td>
        </tr>
    </table>

    {% if cotizacion.observaciones %}
    <div style="margin-top: 20px; padding: 10px; background-color: #fff3cd; border: 1px solid #ffeeba; border-radius: 5px;">
        <strong>Observaciones:</strong><br>
        {{ cotizacion.observaciones }}
    </div>
    {% endif %}

    <div class="footer">
        <p>Generado automáticamente por ContaPY2 el {{ now().strftime('%d/%m/%Y %H:%M') }}</p>
    </div>
</body>
</html>
"""

def generar_pdf_cotizacion(db: Session, cotizacion_id: int, empresa_id: int):
    # 1. Obtener Datos
    cotizacion = db.query(Cotizacion).filter(Cotizacion.id == cotizacion_id, Cotizacion.empresa_id == empresa_id).first()
    if not cotizacion:
        raise HTTPException(status_code=404, detail="Cotización no encontrada.")
    
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada.")

    # 2. Renderizar Template
    env = Environment(autoescape=select_autoescape(['html', 'xml']))
    env.globals['now'] = datetime.now
    template = env.from_string(COTIZACION_TEMPLATE)
    
    html_content = template.render(cotizacion=cotizacion, empresa=empresa)
    
    # 3. Generar PDF
    return HTML(string=html_content).write_pdf()
