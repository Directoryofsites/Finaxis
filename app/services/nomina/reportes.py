from datetime import date
from typing import Dict, Any
from jinja2 import Template
from weasyprint import HTML
from app.models import nomina as models
from app.services.nomina.templates import NOMINA_TEMPLATE
from decimal import Decimal

class ReportesNominaService:

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
        def currency_format(value):
            if value is None: return "$ 0"
            return "${:,.0f}".format(value).replace(",", ".")
            
        template = Template(NOMINA_TEMPLATE)
        # Add filter manually if needed or just format inside logic. Jinja env is better but simple Template works too if filters registered.
        # Jinja2 Template class doesn't share env filters easily. 
        # Easier to just format in context or pre-process.
        # Let's fix template to use {{ sueldo }} and we pass formatted string?
        # Or simpler:
        for k, v in context.items():
            if isinstance(v, (int, float, Decimal)):
                pass # keep val
                
        # Actually simplest is using a localized jinja env or pre-format.
        # Let's use pre-formatting for simplicity in Beta.
        formatted_context = context.copy()
        numeric_keys = ["sueldo", "auxilio", "extras", "comisiones", "total_devengado", "salud", "pension", "fsp", "total_deducciones", "neto"]
        for key in numeric_keys:
             formatted_context[f"{key}_fmt"] = currency_format(context[key])

        html_content = template.render(**formatted_context)
        
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes, f"Nomina_{empleado.numero_documento}_{nomina.anio}_{nomina.mes}.pdf"
