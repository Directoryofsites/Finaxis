from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime

def generar_pdf_remision_individual(remision, empresa):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph(f"REMISIÓN #{remision.numero}", styles['Title']))
    elements.append(Spacer(1, 12))

    # Header Info
    header_data = [
        ["Fecha:", remision.fecha.strftime('%d/%m/%Y'), "Vencimiento:", remision.fecha_vencimiento.strftime('%d/%m/%Y') if remision.fecha_vencimiento else "N/A"],
        ["Cliente:", remision.tercero_nombre, "Bodega:", remision.bodega_nombre],
        ["Estado:", remision.estado, "Elaborado por:", f"Usuario ID {remision.usuario_id}"]
    ]
    t_header = Table(header_data, colWidths=[80, 200, 80, 200])
    t_header.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    elements.append(t_header)
    elements.append(Spacer(1, 20))

    # Details Table
    det_data = [["Código", "Producto", "Cant. Sol.", "Pendiente", "Precio", "Total"]]
    total_gral = 0
    for det in remision.detalles:
        total = det.cantidad_solicitada * det.precio_unitario
        total_gral += total
        det_data.append([
            det.producto_codigo,
            det.producto_nombre[:40],
            f"{det.cantidad_solicitada:,.2f}",
            f"{det.cantidad_pendiente:,.2f}",
            f"${det.precio_unitario:,.2f}",
            f"${total:,.2f}"
        ])
    
    det_data.append(["", "", "", "", "TOTAL:", f"${total_gral:,.2f}"])

    t_det = Table(det_data, colWidths=[60, 200, 60, 60, 70, 80])
    t_det.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (2,1), (-1,-1), 'RIGHT'), # Numbers right aligned
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-2), 0.5, colors.black),
        ('FONTNAME', (-2,-1), (-1,-1), 'Helvetica-Bold'), # Total row bold
    ]))
    elements.append(t_det)

    # Observations
    if remision.observaciones:
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Observaciones:", styles['Heading4']))
        elements.append(Paragraph(remision.observaciones, styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def generar_pdf_listado_remisiones(remisiones, empresa, filtros_desc):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("LISTADO DE REMISIONES", styles['Title']))
    elements.append(Paragraph(f"Filtros: {filtros_desc}", styles['Normal']))
    elements.append(Spacer(1, 12))

    data = [["Número", "Fecha", "Cliente", "Bodega", "Estado"]]
    for r in remisiones:
        data.append([
             str(r.numero),
             r.fecha.strftime('%d/%m/%Y'),
             r.tercero_nombre[:30],
             r.bodega_nombre[:20],
             r.estado
        ])

    t = Table(data, colWidths=[50, 70, 200, 120, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def generar_pdf_reporte_completo(datos_reporte, empresa):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=20, leftMargin=20)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("REPORTE REMISIONADO VS FACTURADO", styles['Title']))
    elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 12))

    data = [["Rem #", "Fecha", "Cliente", "Producto", "Solicita", "Factura", "Pend", "Estado"]]
    for row in datos_reporte:
        data.append([
             str(row['remision_numero']),
             row['fecha'].strftime('%d/%m/%Y'),
             row['tercero_nombre'][:20],
             row['producto_nombre'][:25],
             f"{row['cantidad_solicitada']:.1f}",
             f"{row['cantidad_facturada']:.1f}",
             f"{row['cantidad_pendiente']:.1f}",
             row['estado_remision'][:3] # Short status
        ])

    t = Table(data, colWidths=[40, 60, 130, 150, 45, 45, 45, 45])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ALIGN', (4,1), (-1,-1), 'RIGHT'),
    ]))
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
