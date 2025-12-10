from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime

def generar_pdf_receta(receta, empresa):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph(f"RECETA DE PRODUCCIÓN: {receta.nombre}", styles['Title']))
    producto_nombre = receta.producto.nombre if receta.producto else "Producto Eliminado"
    elements.append(Paragraph(f"Para Producto: {producto_nombre}", styles['Heading2']))
    elements.append(Spacer(1, 12))

    # Info
    info_data = [
        ["Código Receta:", str(receta.id), "Estado:", "ACTIVA" if receta.activa else "INACTIVA"],
        ["Cantidad Base:", f"{receta.cantidad_base}", "Descripción:", receta.descripcion or "N/A"]
    ]
    t_info = Table(info_data, colWidths=[100, 150, 100, 150])
    t_info.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ('BACKGROUND', (2,0), (2,-1), colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 20))

    # Insumos Table
    elements.append(Paragraph("LISTA DE MATERIALES E INSUMOS", styles['Heading3']))
    insumos_data = [["Código", "Insumo / Material", "Unidad", "Cantidad"]]
    
    for det in receta.detalles:
        insumo_nombre = det.insumo.nombre if det.insumo else f"Insumo #{det.insumo_id}"
        unidad = "Und" # det.insumo.unidad_medida if det.insumo else "Und" (Campo eliminado del modelo)
        insumos_data.append([
            str(det.insumo_id),
            insumo_nombre,
            unidad,
            f"{det.cantidad:,.4f}"
        ])

    t_insumos = Table(insumos_data, colWidths=[60, 250, 80, 80])
    t_insumos.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e0e7ff')), # Indigo-50 ish
        ('fontName', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (3,1), (-1,-1), 'RIGHT'),
    ]))
    elements.append(t_insumos)
    elements.append(Spacer(1, 20))

    # Recursos (CIF/MOD)
    if receta.recursos:
        elements.append(Paragraph("RECURSOS DE PRODUCCIÓN (MOD / CIF)", styles['Heading3']))
        recursos_data = [["Descripción", "Tipo", "Costo Estimado"]]
        total_p = 0
        for rec in receta.recursos:
            recursos_data.append([
                rec.descripcion,
                rec.tipo.replace('_', ' '),
                f"${rec.costo_estimado:,.2f}"
            ])
            total_p += rec.costo_estimado

        t_res = Table(recursos_data, colWidths=[250, 150, 100])
        t_res.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#dcfce7')), # Green-50 ish
            ('fontName', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('ALIGN', (2,1), (-1,-1), 'RIGHT'),
        ]))
        elements.append(t_res)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def generar_pdf_orden_produccion(orden, empresa):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph(f"ORDEN DE PRODUCCIÓN #{orden.numero_orden}", styles['Title']))
    elements.append(Spacer(1, 10))

    # Header Styled like Remision
    fecha_inicio = orden.fecha_inicio.strftime('%d/%m/%Y') if orden.fecha_inicio else "N/A"
    fecha_fin = orden.fecha_fin.strftime('%d/%m/%Y') if orden.fecha_fin else "En Proceso"
    
    header_data = [
        ["Producto:", orden.producto.nombre if orden.producto else "N/A", "Estado:", orden.estado],
        ["Cantidad Planeada:", f"{orden.cantidad_planeada}", "Cantidad Real:", f"{orden.cantidad_real}" if orden.cantidad_real else "N/A"],
        ["Fecha Inicio:", fecha_inicio, "Fecha Cierre:", fecha_fin],
        ["Bodega Destino:", orden.bodega_destino.nombre if orden.bodega_destino else "N/A", "Receta:", orden.receta.nombre if orden.receta else "N/A"]
    ]

    t_header = Table(header_data, colWidths=[100, 200, 100, 150])
    t_header.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ('BACKGROUND', (2,0), (2,-1), colors.lightgrey),
    ]))
    elements.append(t_header)
    elements.append(Spacer(1, 20))

    # Costos Summary (Only if closed or in progress showing partials)
    elements.append(Paragraph("Resumen de Costos", styles['Heading3']))
    
    costos_data = [
        ["Concepto", "Valor"],
        ["Materia Prima (MP)", f"${orden.costo_total_mp:,.2f}"],
        ["Mano de Obra (MOD)", f"${orden.costo_total_mod:,.2f}"],
        ["Costos Ind. Fab. (CIF)", f"${orden.costo_total_cif:,.2f}"],
        ["COSTO TOTAL", f"${(orden.costo_total_mp + orden.costo_total_mod + orden.costo_total_cif):,.2f}"]
    ]
    t_costos = Table(costos_data, colWidths=[200, 150])
    t_costos.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('FONTNAME', (-2,-1), (-1,-1), 'Helvetica-Bold'),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
    ]))
    elements.append(t_costos)
    
    # Observaciones
    if orden.observaciones:
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Observaciones:", styles['Heading4']))
        elements.append(Paragraph(orden.observaciones, styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
