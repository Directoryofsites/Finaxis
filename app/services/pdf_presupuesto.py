from fastapi.responses import Response
from fastapi import HTTPException
from sqlalchemy.orm import Session
from weasyprint import HTML
from jinja2 import Environment, select_autoescape
import locale

# Intentar configurar locale para formato moneda, si falla no es critico
try:
    locale.setlocale(locale.LC_ALL, 'es_CO.UTF-8')
except:
    pass

from app.services import presupuesto_avanzado as service_presupuesto
from app.models import Empresa as models_empresa

# Jinja Env
JINJA_ENV = Environment(loader=None, autoescape=select_autoescape(['html', 'xml']))
JINJA_ENV.filters['format_currency'] = lambda x: "{:,.2f}".format(x)

# --- TEMPLATE CSS ---
BASE_CSS = """
<style>
    @page { size: A4 landscape; margin: 1cm; }
    body { font-family: Helvetica, Arial, sans-serif; font-size: 10px; color: #333; }
    .header { text-align: center; margin-bottom: 20px; border-bottom: 2px solid #4f46e5; padding-bottom: 10px; }
    .empresa-title { font-size: 16px; font-weight: bold; text-transform: uppercase; color: #1e1b4b; }
    .report-title { font-size: 14px; font-weight: bold; color: #4338ca; margin-top: 5px; }
    .meta-info { font-size: 10px; color: #666; margin-top: 5px; }
    
    table { width: 100%; border-collapse: collapse; margin-top: 15px; }
    th { background-color: #e0e7ff; color: #312e81; font-weight: bold; padding: 5px; border: 1px solid #c7d2fe; text-align: center; }
    td { border: 1px solid #e5e7eb; padding: 4px; vertical-align: middle; }
    
    .text-right { text-align: right; }
    .text-center { text-align: center; }
    .font-bold { font-weight: bold; }
    .positive { color: green; }
    .negative { color: red; font-weight: bold; }
    
    .footer { position: fixed; bottom: 0; width: 100%; text-align: center; font-size: 8px; color: #999; border-top: 1px solid #eee; padding-top: 5px; }
</style>
"""

# --- 1. REPORTE MATRIZ (PRESUPUESTO COMPLETO) ---
TEMPLATE_MATRIZ = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8">{BASE_CSS}</head>
<body>
    <div class="header">
        <div class="empresa-title">{{{{ empresa.razon_social }}}}</div>
        <div>NIT: {{{{ empresa.nit }}}}</div>
        <div class="report-title">PRESUPUESTO DETALLADO {{{{ escenario.anio }}}}</div>
        <div class="meta-info">Escenario: {{{{ escenario.nombre }}}} | Sector: {{{{ escenario.tipo_sector }}}}</div>
    </div>

    <table>
        <thead>
            <tr>
                <th width="20%">Cuenta</th>
                <th width="5%">Ene</th><th width="5%">Feb</th><th width="5%">Mar</th>
                <th width="5%">Abr</th><th width="5%">May</th><th width="5%">Jun</th>
                <th width="5%">Jul</th><th width="5%">Ago</th><th width="5%">Sep</th>
                <th width="5%">Oct</th><th width="5%">Nov</th><th width="5%">Dic</th>
                <th width="10%">Total</th>
            </tr>
        </thead>
        <tbody>
            {{% for item in items %}}
            <tr>
                <td><b>{{{{ item.cuenta.codigo }}}}</b> {{{{ item.cuenta.nombre }}}}</td>
                <td class="text-right">{{{{ item.mes_01 | format_currency }}}}</td>
                <td class="text-right">{{{{ item.mes_02 | format_currency }}}}</td>
                <td class="text-right">{{{{ item.mes_03 | format_currency }}}}</td>
                <td class="text-right">{{{{ item.mes_04 | format_currency }}}}</td>
                <td class="text-right">{{{{ item.mes_05 | format_currency }}}}</td>
                <td class="text-right">{{{{ item.mes_06 | format_currency }}}}</td>
                <td class="text-right">{{{{ item.mes_07 | format_currency }}}}</td>
                <td class="text-right">{{{{ item.mes_08 | format_currency }}}}</td>
                <td class="text-right">{{{{ item.mes_09 | format_currency }}}}</td>
                <td class="text-right">{{{{ item.mes_10 | format_currency }}}}</td>
                <td class="text-right">{{{{ item.mes_11 | format_currency }}}}</td>
                <td class="text-right">{{{{ item.mes_12 | format_currency }}}}</td>
                <td class="text-right font-bold">{{{{ item.valor_total | format_currency }}}}</td>
            </tr>
            {{% endfor %}}
            <tr style="background-color: #f3f4f6; font-weight: bold;">
                 <td>TOTALES</td>
                 {{% for m in range(1, 13) %}}
                    <td class="text-right">{{{{ total_meses[m] | format_currency }}}}</td>
                 {{% endfor %}}
                 <td class="text-right">{{{{ total_general | format_currency }}}}</td>
            </tr>
        </tbody>
    </table>
    
    <div class="footer">Generado por Sistema Contable | Fecha: {{{{ fecha_impresion }}}}</div>
</body>
</html>
"""

# --- 2. REPORTE EJECUCIÓN (COMPARATIVO) ---
TEMPLATE_EJECUCION = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8">{BASE_CSS}</head>
<body>
    <div class="header">
        <div class="empresa-title">{{{{ empresa.razon_social }}}}</div>
        <div>NIT: {{{{ empresa.nit }}}}</div>
        <div class="report-title">EJECUCIÓN PRESUPUESTAL {{{{ escenario.anio }}}}</div>
        <div class="meta-info">Escenario: {{{{ escenario.nombre }}}} | Comparativo Acumulado Anual</div>
    </div>

    <table>
        <thead>
            <tr>
                <th width="30%">Cuenta</th>
                <th width="15%">Presupuestado</th>
                <th width="15%">Ejecutado</th>
                <th width="15%">Variación $</th>
                <th width="10%">% Ejec.</th>
                <th width="15%">Estado</th>
            </tr>
        </thead>
        <tbody>
            {{% for item in items %}}
            <tr>
                <td><b>{{{{ item['codigo'] }}}}</b> {{{{ item['nombre'] }}}}</td>
                <td class="text-right">{{{{ item['total_anual']['presupuestado'] | format_currency }}}}</td>
                <td class="text-right">{{{{ item['total_anual']['ejecutado'] | format_currency }}}}</td>
                <td class="text-right font-bold {{{{ 'negative' if item['total_anual']['variacion'] < 0 else 'positive' }}}}">
                    {{{{ item['total_anual']['variacion'] | format_currency }}}}
                </td>
                <td class="text-center">{{{{ "%.1f"|format(item['total_anual']['porcentaje_ejecucion']) }}}}%</td>
                 <td class="text-center">
                    {{% if item['total_anual']['variacion'] < 0 %}}
                        <span style="background-color: #fee2e2; color: #991b1b; padding: 2px 6px; border-radius: 4px;">EXCEDIDO</span>
                    {{% else %}}
                        <span style="background-color: #dcfce7; color: #166534; padding: 2px 6px; border-radius: 4px;">OK</span>
                    {{% endif %}}
                </td>
            </tr>
            {{% endfor %}}
        </tbody>
    </table>
    
    <div class="footer">Generado por Sistema Contable | Fecha: {{{{ fecha_impresion }}}}</div>
</body>
</html>
"""

def generate_pdf_matriz_presupuesto(db: Session, escenario_id: int):
    # 1. Get Data
    escenario = service_presupuesto.get_escenario(db, escenario_id)
    if not escenario: raise HTTPException(status_code=404, detail="Escenario no encontrado")
    
    empresa = db.query(models_empresa).filter(models_empresa.id == escenario.empresa_id).first()
    items = service_presupuesto.get_items_escenario(db, escenario_id)
    
    # Calculate column totals
    total_meses = {m: 0 for m in range(1, 13)}
    total_general = 0
    
    for item in items:
        total_general += item.valor_total
        total_meses[1] += item.mes_01
        total_meses[2] += item.mes_02
        total_meses[3] += item.mes_03
        total_meses[4] += item.mes_04
        total_meses[5] += item.mes_05
        total_meses[6] += item.mes_06
        total_meses[7] += item.mes_07
        total_meses[8] += item.mes_08
        total_meses[9] += item.mes_09
        total_meses[10] += item.mes_10
        total_meses[11] += item.mes_11
        total_meses[12] += item.mes_12

    from datetime import datetime
    
    context = {
        "escenario": escenario,
        "empresa": empresa,
        "items": items,
        "total_meses": total_meses,
        "total_general": total_general,
        "fecha_impresion": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "range": range # Make range available in jinja
    }
    
    # 2. Render
    try:
        template = JINJA_ENV.from_string(TEMPLATE_MATRIZ)
        html = template.render(context)
        pdf = HTML(string=html).write_pdf()
        return Response(content=pdf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="Presupuesto_{escenario.anio}.pdf"'})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando PDF: {e}")


def generate_pdf_ejecucion(db: Session, escenario_id: int):
    # 1. Get Data from existing service
    reporte = service_presupuesto.calcular_ejecucion_comparativa(db, escenario_id)
    if not reporte: raise HTTPException(status_code=404, detail="Reporte no generado")
    
    escenario = reporte["escenario"] 
    # Compatibility fix: reporte might be a dict not a Pydantic model if returned directly from service logic or schemas
    # Based on service trace: it returns {"escenario": obj, "items": list_of_dicts}
    
    empresa = db.query(models_empresa).filter(models_empresa.id == escenario.empresa_id).first()
    items = reporte["items"]
    
    from datetime import datetime

    context = {
        "escenario": escenario,
        "empresa": empresa,
        "items": items,
        "fecha_impresion": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    
    # 2. Render
    try:
        template = JINJA_ENV.from_string(TEMPLATE_EJECUCION)
        html = template.render(context)
        pdf = HTML(string=html).write_pdf()
        return Response(content=pdf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="Ejecucion_{escenario.anio}.pdf"'})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando PDF: {e}")
