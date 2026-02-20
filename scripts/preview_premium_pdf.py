
import sys
import os

# Ajustar path para importar desde app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.services.documento import get_documento_by_id, GLOBAL_JINJA_ENV
from weasyprint import HTML
import json

def generate_premium_preview(documento_id, empresa_id):
    db = SessionLocal()
    try:
        # 1. Obtener la data real del documento
        doc_model = get_documento_by_id(db, documento_id, empresa_id)
        if not doc_model:
            print(f"Error: No se encontró el documento {documento_id}")
            return

        # 2. Preparar el contexto para la plantilla (simulando la lógica de generar_pdf_documento)
        # Extraemos los datos necesarios para que la plantilla no falle
        
        items = []
        subtotal = 0
        iva_19 = 0
        
        # Procesar movimientos para la tabla de items
        for mov in doc_model.movimientos:
            if mov.credito > 0 and (mov.cuenta.codigo.startswith('4') or mov.cuenta.codigo.startswith('14')):
                items.append({
                    "producto_nombre": mov.producto.nombre if mov.producto else (mov.concepto or "Servicio General"),
                    "producto_codigo": mov.producto.codigo if mov.producto else "GEN",
                    "cantidad": float(mov.cantidad or 1),
                    "precio_unitario": f"{float(mov.credito / (mov.cantidad or 1)):,.2f}",
                    "subtotal": f"{float(mov.credito):,.2f}"
                })
                subtotal += float(mov.credito)
        
        # Totales ficticios o calculados básicos
        totales = {
            "subtotal": f"{subtotal:,.2f}",
            "descuentos": "0.00",
            "iva_19": f"{subtotal * 0.19:,.2f}",
            "total": f"{subtotal * 1.19:,.2f}",
            "valor_letras": "VALOR EN PESOS M/CTE (DEMO PREVIEW)"
        }

        context = {
            "documento": {
                "tipo_nombre": doc_model.tipo_documento.nombre,
                "prefix": "FE",
                "consecutivo": f"{doc_model.numero}",
                "fecha_emision": doc_model.fecha.strftime("%d/%m/%Y"),
                "fecha_vencimiento": (doc_model.fecha_vencimiento or doc_model.fecha).strftime("%d/%m/%Y"),
                "observaciones": doc_model.observaciones,
                "dian_cufe": "CUFE-SIMULADO-PARA-PREVIEW-PREMIUM-FINAXIS-2026",
                "qr_base64": None # Sin QR en preview
            },
            "empresa": doc_model.empresa,
            "tercero": doc_model.beneficiario,
            "items": items,
            "totales": totales
        }

        # 3. Cargar la plantilla Premium
        template_path = os.path.join('app', 'templates', 'reports', 'invoice_premium_template.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        # 4. Renderizar HTML
        template = GLOBAL_JINJA_ENV.from_string(template_content)
        html_out = template.render(**context)

        # 5. Generar PDF
        output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'preview_premium_factura.pdf'))
        HTML(string=html_out).write_pdf(output_path)
        
        print(f"✅ Preview generado exitosamente en: {output_path}")
        return output_path

    finally:
        db.close()

if __name__ == "__main__":
    # Usamos los IDs detectados: Empresa 134, Doc 12672
    generate_premium_preview(12672, 134)
