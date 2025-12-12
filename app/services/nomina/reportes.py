from datetime import date
from typing import Dict, Any
from jinja2 import Template
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
from app.models import nomina as models
from app.services.nomina.templates import NOMINA_TEMPLATE
from app.services.nomina.templates_resumen import NOMINA_RESUMEN_TEMPLATE
from decimal import Decimal
from datetime import datetime

# Global Font Config Cache
font_config = FontConfiguration()

class ReportesNominaService:

    @staticmethod
    def currency_format(value):
        if value is None: return "$ 0"
        return "${:,.0f}".format(value).replace(",", ".")

    @staticmethod
    def generar_pdf_desprendible(db, detalle_id: int):
        detalle = db.query(models.DetalleNomina).get(detalle_id)
        if not detalle:
            raise ValueError("Detalle de nómina no encontrado")
            
        empleado = detalle.empleado
        nomina = detalle.nomina
        empresa = nomina.empresa
        tercero = empleado.tercero 
        
        # Prepare context
        context = {
            "empresa": {
                "nombre": empresa.razon_social if empresa else "Empresa Demo",
                "nit": empresa.nit if empresa else "NIT",
                "dv": getattr(empresa, 'dv', '0') if empresa else "0"
            },
            "empleado": {
                "nombre": f"{empleado.nombres} {empleado.apellidos}",
                "documento": empleado.numero_documento,
                "cargo": empleado.cargo
            },
            "periodo": f"{nomina.anio}-{nomina.mes:02d}",
            "fecha_pago": nomina.fecha_liquidacion.strftime("%Y-%m-%d"),
            "dias_trabajados": detalle.dias_trabajados,
            
            # Values
            "sueldo": detalle.sueldo_basico_periodo,
            "auxilio": detalle.auxilio_transporte_periodo,
            "extras": detalle.horas_extras_total,
            "comisiones": detalle.comisiones,
            "total_devengado": detalle.total_devengado,
            
            "salud": detalle.salud_empleado,
            "pension": detalle.pension_empleado,
            "fsp": detalle.fondo_solidaridad,
            "total_deducciones": detalle.total_deducciones,
            "neto": detalle.neto_pagar
        }
        
        # Helper currency format
        formatted_context = context.copy()
        numeric_keys = ["sueldo", "auxilio", "extras", "comisiones", "total_devengado", "salud", "pension", "fsp", "total_deducciones", "neto"]
        for key in numeric_keys:
             formatted_context[f"{key}_fmt"] = ReportesNominaService.currency_format(context[key])

        template = Template(NOMINA_TEMPLATE)
        html_content = template.render(**formatted_context)
        
        pdf_bytes = HTML(string=html_content).write_pdf(font_config=font_config)
        return pdf_bytes, f"Nomina_{empleado.numero_documento}_{nomina.anio}_{nomina.mes}.pdf"

    @staticmethod
    def generar_pdf_resumen_nomina(db, empresa_id: int, anio: int, mes: int, tipo_nomina_id: int = None):
        # 1. Buscar DETALLES uniendo con Nómina
        query_detalles = db.query(models.DetalleNomina).join(models.Nomina).filter(
            models.Nomina.empresa_id == empresa_id,
            models.Nomina.anio == anio,
            models.Nomina.mes == mes
        )
        
        if tipo_nomina_id:
             query_detalles = query_detalles.join(models.Empleado).filter(models.Empleado.tipo_nomina_id == tipo_nomina_id)
        
        detalles = query_detalles.all()
        
        if not detalles:
             raise ValueError(f"No se encontraron empleados liquidados para el periodo {anio}-{mes}")

        # Obtener datos de empresa
        empresa = detalles[0].nomina.empresa

        # 3. Preparar Datos
        lista_detalles = []
        totales = {
            "basico": 0, "auxilio": 0, "extras": 0, "comisiones": 0,
            "total_dev": 0, "salud": 0, "pension": 0, "fsp": 0,
            "total_ded": 0, "neto": 0
        }
        
        for d in detalles:
            emp = d.empleado
            item = {
                "nombre": f"{emp.nombres} {emp.apellidos}",
                "documento": emp.numero_documento,
                "dias": d.dias_trabajados,
                "basico_fmt": ReportesNominaService.currency_format(d.sueldo_basico_periodo),
                "auxilio_fmt": ReportesNominaService.currency_format(d.auxilio_transporte_periodo),
                "extras_fmt": ReportesNominaService.currency_format(d.horas_extras_total),
                "comisiones_fmt": ReportesNominaService.currency_format(d.comisiones),
                "total_dev_fmt": ReportesNominaService.currency_format(d.total_devengado),
                "salud_fmt": ReportesNominaService.currency_format(d.salud_empleado),
                "pension_fmt": ReportesNominaService.currency_format(d.pension_empleado),
                "fsp_fmt": ReportesNominaService.currency_format(d.fondo_solidaridad),
                "total_ded_fmt": ReportesNominaService.currency_format(d.total_deducciones),
                "neto_fmt": ReportesNominaService.currency_format(d.neto_pagar)
            }
            lista_detalles.append(item)
            
            # Sumar Totales
            totales["basico"] += d.sueldo_basico_periodo or 0
            totales["auxilio"] += d.auxilio_transporte_periodo or 0
            totales["extras"] += d.horas_extras_total or 0
            totales["comisiones"] += d.comisiones or 0
            totales["total_dev"] += d.total_devengado or 0
            totales["salud"] += d.salud_empleado or 0
            totales["pension"] += d.pension_empleado or 0
            totales["fsp"] += d.fondo_solidaridad or 0
            totales["total_ded"] += d.total_deducciones or 0
            totales["neto"] += d.neto_pagar or 0

        # Formatear Totales
        totales_fmt = {}
        for k, v in totales.items():
            totales_fmt[f"{k}_fmt"] = ReportesNominaService.currency_format(v)

        context = {
            "empresa": {
                 "nombre": empresa.razon_social if empresa else "Empresa Demo",
                 "nit": f"{empresa.nit}" if empresa else "NIT"
            },
            "periodo": f"{anio}-{mes:02d}",
            "fecha_generacion": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "detalles": lista_detalles,
            "totales": totales_fmt
        }
        
        template = Template(NOMINA_RESUMEN_TEMPLATE)
        html_content = template.render(**context)
        
        pdf_bytes = HTML(string=html_content).write_pdf(font_config=font_config)
        return pdf_bytes, f"Resumen_Nomina_{anio}_{mes}.pdf"

