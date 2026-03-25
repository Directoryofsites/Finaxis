from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case
from app.models.movimiento_contable import MovimientoContable
from app.models.plan_cuenta import PlanCuenta
from app.models.documento import Documento
from datetime import date
from decimal import Decimal
import logging

class CashFlowService:
    @staticmethod
    def calculate_statement(db: Session, empresa_id: int, fecha_inicio: date, fecha_fin: date):
        # 1. Identificar cuentas de efectivo (Grupo 11)
        cuentas_caja_ids = db.query(PlanCuenta.id).filter(
            PlanCuenta.empresa_id == empresa_id,
            PlanCuenta.codigo.like("11%")
        ).all()
        caja_ids = [c[0] for c in cuentas_caja_ids]

        if not caja_ids:
            return CashFlowService._empty_response(saldo_inicial=0)

        # 2. Calcular Saldos (Inicial y Final Real en Libros)
        saldo_inicial = db.query(
            func.sum(MovimientoContable.debito - MovimientoContable.credito)
        ).join(Documento).filter(
            MovimientoContable.cuenta_id.in_(caja_ids),
            Documento.empresa_id == empresa_id,
            Documento.fecha < fecha_inicio,
            Documento.anulado == False 
        ).scalar() or Decimal(0)

        saldo_final_real = db.query(
            func.sum(MovimientoContable.debito - MovimientoContable.credito)
        ).join(Documento).filter(
            MovimientoContable.cuenta_id.in_(caja_ids),
            Documento.empresa_id == empresa_id,
            Documento.fecha <= fecha_fin,
            Documento.anulado == False
        ).scalar() or Decimal(0)

        # 3. Obtener movimientos de efectivo del período
        movimientos_efectivo = db.query(
            MovimientoContable,
            Documento.fecha,
            Documento.numero
        ).join(Documento).filter(
            MovimientoContable.cuenta_id.in_(caja_ids),
            Documento.empresa_id == empresa_id,
            Documento.fecha >= fecha_inicio,
            Documento.fecha <= fecha_fin,
            Documento.anulado == False
        ).all()

        # Estructuras de agregación
        agregado = {
            "OPERACION": {},
            "INVERSION": {},
            "FINANCIACION": {}
        }
        
        totales = {
            "OPERACION": Decimal(0),
            "INVERSION": Decimal(0),
            "FINANCIACION": Decimal(0)
        }

        for mov, fecha, numero in movimientos_efectivo:
            valor_flujo = mov.debito - mov.credito
            if valor_flujo == 0: continue

            # Buscar contrapartida real
            contrapartidas = db.query(
                PlanCuenta.codigo, 
                PlanCuenta.nombre,
                (MovimientoContable.debito - MovimientoContable.credito).label("neto")
            ).join(PlanCuenta).filter(
                MovimientoContable.documento_id == mov.documento_id,
                ~MovimientoContable.cuenta_id.in_(caja_ids)
            ).all()

            if not contrapartidas:
                categoria = "OPERACION"
                con_fin = "Ajustes o Traslados Internos de Efectivo"
            else:
                principal = sorted(contrapartidas, key=lambda x: abs(x.neto), reverse=True)[0]
                categoria = CashFlowService._classify_activity(principal.codigo)
                con_fin = CashFlowService._get_financial_concept(principal.codigo, principal.nombre, valor_flujo)

            # Acumular
            current_val = agregado[categoria].get(con_fin, Decimal(0))
            agregado[categoria][con_fin] = current_val + valor_flujo
            totales[categoria] += valor_flujo

        # 4. Formatear respuesta
        def format_activity_group(activity_name):
            items = []
            for concepto, valor in agregado[activity_name].items():
                items.append({"concepto": concepto, "valor": valor})
            items.sort(key=lambda x: x["valor"], reverse=True)
            return {"detalles": items, "total": totales[activity_name]}

        flujos_operacion = format_activity_group("OPERACION")
        flujos_inversion = format_activity_group("INVERSION")
        flujos_financiacion = format_activity_group("FINANCIACION")

        flujos_netos = totales["OPERACION"] + totales["INVERSION"] + totales["FINANCIACION"]
        saldo_final_calculado = saldo_inicial + flujos_netos
        
        diferencia = saldo_final_real - saldo_final_calculado
        es_valido = abs(diferencia) < Decimal('0.01')

        return {
            "saldo_inicial": saldo_inicial,
            "flujos_operacion": flujos_operacion,
            "flujos_inversion": flujos_inversion,
            "flujos_financiacion": flujos_financiacion,
            "flujos_netos_totales": flujos_netos,
            "saldo_final_calculado": saldo_final_calculado,
            "saldo_final_real": saldo_final_real,
            "validacion": {
                "es_valido": es_valido,
                "diferencia": diferencia
            }
        }

    @staticmethod
    def _empty_response(saldo_inicial):
        empty_group = {"detalles": [], "total": Decimal(0)}
        return {
            "saldo_inicial": saldo_inicial,
            "flujos_operacion": empty_group,
            "flujos_inversion": empty_group,
            "flujos_financiacion": empty_group,
            "flujos_netos_totales": Decimal(0),
            "saldo_final_calculado": saldo_inicial,
            "saldo_final_real": saldo_inicial,
            "validacion": {"es_valido": True, "diferencia": Decimal(0)}
        }

    @staticmethod
    def _classify_activity(codigo: str) -> str:
        if codigo.startswith(("15", "16", "12")): 
            return "INVERSION"
        if codigo.startswith(("21", "3")):
            return "FINANCIACION"
        return "OPERACION"

    @staticmethod
    def _get_financial_concept(codigo: str, nombre: str, valor: Decimal) -> str:
        prefix_2 = codigo[:2]
        prefix_4 = codigo[:4]

        # --- MAPA DE CONCEPTOS POR CUENTA MAYOR (4 DÍGITOS) ---
        # Agrupa auxiliares bajo conceptos estandarizados según NIC 7 / PUC
        concept_map = {
            # Gastos Operacionales (51/52)
            "5105": "Pago de Gastos de Personal (Nómina)",
            "5205": "Pago de Gastos de Personal (Ventas)",
            "5110": "Pago de Honorarios",
            "5210": "Pago de Honorarios",
            "5115": "Pago de Impuestos Operacionales",
            "5215": "Pago de Impuestos Operacionales",
            "5120": "Pago de Arrendamientos",
            "5220": "Pago de Arrendamientos",
            "5125": "Pago de Contribuciones y Afiliaciones",
            "5225": "Pago de Contribuciones y Afiliaciones",
            "5130": "Pago de Seguros",
            "5230": "Pago de Seguros",
            "5135": "Pago de Servicios Públicos y Generales", # SOLICITUD ESPECIFICA (Agrupa Aseo, Energia, etc.)
            "5235": "Pago de Servicios Públicos y Generales",
            "5140": "Pago de Gastos Legales",
            "5240": "Pago de Gastos Legales",
            "5145": "Pago de Mantenimiento y Reparaciones",
            "5245": "Pago de Mantenimiento y Reparaciones",
            "5150": "Pago de Adecuación e Instalación",
            "5250": "Pago de Adecuación e Instalación",
            "5155": "Pago de Gastos de Viaje",
            "5255": "Pago de Gastos de Viaje",
            "5160": "Pago de Depreciaciones (Si hubo desembolso)",
            "5195": "Pago de Otros Gastos Operativos (Diversos)",
            "5295": "Pago de Otros Gastos Operativos (Diversos)",
            
            # Pasivos Operativos
            "2335": "Pago de Costos y Gastos por Pagar",
            "2365": "Pago de Retención en la Fuente",
            "2408": "Pago de IVA",
        }

        # 1. Búsqueda Directa en Mapa (Prioridad Cuenta Mayor)
        if prefix_4 in concept_map:
            return concept_map[prefix_4]

        # 2. Lógica Especial (Proveedores y Clientes)
        if prefix_4 == "1305": return "Recaudo de Clientes Nacionales"
        if prefix_2 == "13": return "Recaudo de Otras Cuentas por Cobrar"
        
        if prefix_4 == "2205": return "Pago a Proveedores Nacionales"
        if prefix_2 == "22": return "Pago a Otros Proveedores"
        
        # 3. Ingresos (Grupo 4)
        if prefix_2 == "41": return "Ingresos por Ventas (Contado)"
        if prefix_2 == "42": 
            # Lógica refinada para Ingresos No Operacionales
            nombre_lower = nombre.lower()
            if "interes" in nombre_lower:
                return "Intereses Recibidos"
            return nombre.title()

        # 4. Inversión
        if prefix_2 == "15": 
            return "Venta de Propiedad, Planta y Equipo" if valor > 0 else "Compra de Propiedad, Planta y Equipo"

        # 5. Financiación
        if prefix_2 == "21":
            return "Desembolsos de Obligaciones Financieras" if valor > 0 else "Pago de Obligaciones Financieras"
        if prefix_2 == "31": return "Aportes de Capital"

        # 6. Fallback General (Nombre Cuenta)
        return nombre.title()

    @staticmethod
    def generate_pdf_statement(db: Session, empresa_id: int, fecha_inicio: date, fecha_fin: date):
        import os
        from app.models.empresa import Empresa
        from app.services._templates_empaquetados import TEMPLATES_EMPAQUETADOS
        from weasyprint import HTML
        from jinja2 import Environment, select_autoescape
        
        # 1. Obtener Datos
        data = CashFlowService.calculate_statement(db, empresa_id, fecha_inicio, fecha_fin)
        
        # 2. Informacion Empresa
        empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
        empresa_nombre = empresa.razon_social if empresa else "EMPRESA DESCONOCIDA"
        empresa_nit = empresa.nit if empresa else "N/A"
        empresa_dir = getattr(empresa, 'direccion', '') or ''
        empresa_tel = getattr(empresa, 'telefono', '') or ''
        
        # 3. Obtener plantilla (con fallback a template inline si no esta en disco ni empaquetada)
        template_key = 'reports/cash_flow_report.html'
        template_str = TEMPLATES_EMPAQUETADOS.get(template_key)
        
        if not template_str:
            template_path = os.path.join(
                os.path.dirname(__file__), '..', 'templates', 'reports', 'cash_flow_report.html'
            )
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    template_str = f.read()
        
        if not template_str:
            # Generar template inline para flujo de efectivo
            template_str = CashFlowService._get_inline_template()
        
        # 4. Preparar Contexto
        env = Environment(loader=None, autoescape=select_autoescape(['html', 'xml']))
        template = env.from_string(template_str)
        
        context = {
            # Variables de string directo (para template inline)
            "empresa_nombre": empresa_nombre,
            "empresa_nit": empresa_nit,
            "empresa_dir": empresa_dir,
            "empresa_tel": empresa_tel,
            # Objeto empresa (para templates genericos que lo usen)
            "empresa": type('EmpresaProxy', (), {
                'razon_social': empresa_nombre,
                'nit': empresa_nit,
                'direccion': empresa_dir,
                'telefono': empresa_tel,
                'logo_url': getattr(empresa, 'logo_url', None) if empresa else None,
                'email': getattr(empresa, 'email', '') if empresa else '',
            })(),
            "fecha_inicio": fecha_inicio.strftime('%d/%m/%Y'),
            "fecha_fin": fecha_fin.strftime('%d/%m/%Y'),
            "fecha_generacion": date.today().strftime('%d/%m/%Y'),
            "data": data
        }
        
        # 5. Renderizar PDF
        html_out = template.render(context)
        return HTML(string=html_out).write_pdf()

    @staticmethod
    def _get_inline_template():
        """Plantilla HTML inline para el Estado de Flujos de Efectivo."""
        return '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <style>
        @page { size: letter; margin: 2cm; }
        body { font-family: Helvetica, Arial, sans-serif; font-size: 10pt; color: #333; }
        .header { text-align: center; margin-bottom: 20px; border-bottom: 2px solid #333; padding-bottom: 10px; }
        .header h1 { font-size: 14pt; text-transform: uppercase; margin: 0 0 4px 0; }
        .header h2 { font-size: 12pt; margin: 0 0 4px 0; color: #444; }
        .header p { margin: 2px 0; font-size: 9pt; color: #666; }
        .section { margin-bottom: 20px; }
        .section-title { background: #2c3e50; color: white; padding: 6px 10px; font-size: 10pt; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 0; }
        th { background: #ecf0f1; padding: 5px 10px; font-size: 9pt; border-bottom: 1px solid #bdc3c7; }
        td { padding: 5px 10px; font-size: 9pt; border-bottom: 1px solid #eee; }
        .text-right { text-align: right; font-family: monospace; }
        .total-row td { font-weight: bold; border-top: 1px solid #333; background: #f8f9fa; }
        .summary { margin-top: 20px; border: 1px solid #333; }
        .summary tr:last-child td { font-weight: bold; font-size: 11pt; background: #2c3e50; color: white; }
        .positive { color: #27ae60; } .negative { color: #c0392b; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ empresa_nombre }}</h1>
        <h2>NIT: {{ empresa_nit }}</h2>
        {% if empresa_dir %}<p>{{ empresa_dir }} &nbsp;|&nbsp; Tel: {{ empresa_tel }}</p>{% endif %}
        <h2 style="margin-top:8px;color:#2c3e50;">Estado de Flujos de Efectivo</h2>
        <p>Periodo: {{ fecha_inicio }} al {{ fecha_fin }} &nbsp;&nbsp; Generado: {{ fecha_generacion }}</p>
    </div>

    {% macro fmt(val) %}
        {% if val is number and val < 0 %}
            <span class="negative">({{ "${:,.0f}".format(val|abs) }})</span>
        {% elif val is number %}
            {{ "${:,.0f}".format(val) }}
        {% else %}
            {{ val }}
        {% endif %}
    {% endmacro %}

    <!-- Actividades de Operacion -->
    <div class="section">
        <div class="section-title">ACTIVIDADES DE OPERACION</div>
        <table>
            <thead><tr><th class="text-left">Concepto</th><th class="text-right">Valor</th></tr></thead>
            <tbody>
            {% for item in data.flujos_operacion.detalles %}
            <tr><td>{{ item.concepto }}</td><td class="text-right">{{ "${:,.0f}".format(item.valor|float) }}</td></tr>
            {% else %}
            <tr><td colspan="2" style="text-align:center;color:#999;font-style:italic;">Sin movimientos</td></tr>
            {% endfor %}
            <tr class="total-row"><td>Flujo Neto de Operacion</td><td class="text-right">{{ "${:,.0f}".format(data.flujos_operacion.total|float) }}</td></tr>
            </tbody>
        </table>
    </div>

    <!-- Actividades de Inversion -->
    <div class="section">
        <div class="section-title">ACTIVIDADES DE INVERSION</div>
        <table>
            <thead><tr><th class="text-left">Concepto</th><th class="text-right">Valor</th></tr></thead>
            <tbody>
            {% for item in data.flujos_inversion.detalles %}
            <tr><td>{{ item.concepto }}</td><td class="text-right">{{ "${:,.0f}".format(item.valor|float) }}</td></tr>
            {% else %}
            <tr><td colspan="2" style="text-align:center;color:#999;font-style:italic;">Sin movimientos</td></tr>
            {% endfor %}
            <tr class="total-row"><td>Flujo Neto de Inversion</td><td class="text-right">{{ "${:,.0f}".format(data.flujos_inversion.total|float) }}</td></tr>
            </tbody>
        </table>
    </div>

    <!-- Actividades de Financiacion -->
    <div class="section">
        <div class="section-title">ACTIVIDADES DE FINANCIACION</div>
        <table>
            <thead><tr><th class="text-left">Concepto</th><th class="text-right">Valor</th></tr></thead>
            <tbody>
            {% for item in data.flujos_financiacion.detalles %}
            <tr><td>{{ item.concepto }}</td><td class="text-right">{{ "${:,.0f}".format(item.valor|float) }}</td></tr>
            {% else %}
            <tr><td colspan="2" style="text-align:center;color:#999;font-style:italic;">Sin movimientos</td></tr>
            {% endfor %}
            <tr class="total-row"><td>Flujo Neto de Financiacion</td><td class="text-right">{{ "${:,.0f}".format(data.flujos_financiacion.total|float) }}</td></tr>
            </tbody>
        </table>
    </div>

    <!-- Conciliacion -->
    <table class="summary">
        <tr><td style="padding:6px 10px;">Saldo Inicial de Efectivo</td><td class="text-right" style="padding:6px 10px;">{{ "${:,.0f}".format(data.saldo_inicial|float) }}</td></tr>
        <tr><td style="padding:6px 10px;">(+) Flujos Netos del Periodo</td><td class="text-right" style="padding:6px 10px;">{{ "${:,.0f}".format(data.flujos_netos_totales|float) }}</td></tr>
        <tr><td style="padding:8px 10px;">SALDO FINAL DE EFECTIVO</td><td class="text-right" style="padding:8px 10px;">{{ "${:,.0f}".format(data.saldo_final_calculado|float) }}</td></tr>
    </table>

    <div style="text-align:center;font-size:8pt;color:#aaa;margin-top:20px;">Generado por Finaxis Cloud</div>
</body>
</html>
        '''
