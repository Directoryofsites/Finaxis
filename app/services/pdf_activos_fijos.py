# app/services/pdf_activos_fijos.py - Generación de PDFs para Activos Fijos

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from datetime import datetime, date
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal

from ..models.activo_fijo import ActivoFijo
from ..models.activo_categoria import ActivoCategoria
from ..models.activo_novedad import ActivoNovedad
from ..models.empresa import Empresa

def generar_reporte_maestro_activos(db: Session, empresa_id: int, categoria_id: Optional[int] = None) -> BytesIO:
    """
    Genera PDF con el reporte maestro de todos los activos fijos
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Obtener datos
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    
    query = db.query(ActivoFijo).filter(ActivoFijo.empresa_id == empresa_id)
    if categoria_id:
        query = query.filter(ActivoFijo.categoria_id == categoria_id)
    
    activos = query.order_by(ActivoFijo.codigo).all()
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Contenido
    story = []
    
    # Encabezado
    story.append(Paragraph(f"<b>{empresa.razon_social}</b>", title_style))
    story.append(Paragraph(f"NIT: {empresa.nit}", styles['Normal']))
    story.append(Paragraph("<b>REPORTE MAESTRO DE ACTIVOS FIJOS</b>", title_style))
    story.append(Paragraph(f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    if not activos:
        story.append(Paragraph("No se encontraron activos fijos registrados.", styles['Normal']))
    else:
        # Tabla de activos
        data = [
            ['Código', 'Nombre', 'Categoría', 'Fecha Compra', 'Costo Adquisición', 'Dep. Acumulada', 'Valor Neto', 'Estado']
        ]
        
        total_costo = Decimal('0')
        total_depreciacion = Decimal('0')
        
        for activo in activos:
            valor_neto = activo.costo_adquisicion - activo.depreciacion_acumulada_niif
            
            data.append([
                activo.codigo,
                activo.nombre[:30] + ('...' if len(activo.nombre) > 30 else ''),
                activo.categoria.nombre if activo.categoria else 'N/A',
                activo.fecha_compra.strftime('%d/%m/%Y') if activo.fecha_compra else 'N/A',
                f"${activo.costo_adquisicion:,.0f}",
                f"${activo.depreciacion_acumulada_niif:,.0f}",
                f"${valor_neto:,.0f}",
                activo.estado.value
            ])
            
            total_costo += activo.costo_adquisicion
            total_depreciacion += activo.depreciacion_acumulada_niif
        
        # Fila de totales
        total_neto = total_costo - total_depreciacion
        data.append([
            '', '', '', 'TOTALES:', 
            f"${total_costo:,.0f}",
            f"${total_depreciacion:,.0f}",
            f"${total_neto:,.0f}",
            ''
        ])
        
        # Crear tabla
        table = Table(data, colWidths=[0.8*inch, 2*inch, 1.2*inch, 0.8*inch, 1*inch, 1*inch, 1*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (4, 1), (-2, -1), 'RIGHT'),  # Alinear números a la derecha
        ]))
        
        story.append(table)
        
        # Resumen por categorías
        story.append(Spacer(1, 30))
        story.append(Paragraph("<b>RESUMEN POR CATEGORÍAS</b>", styles['Heading2']))
        
        categorias_resumen = {}
        for activo in activos:
            cat_nombre = activo.categoria.nombre if activo.categoria else 'Sin categoría'
            if cat_nombre not in categorias_resumen:
                categorias_resumen[cat_nombre] = {
                    'cantidad': 0,
                    'costo_total': Decimal('0'),
                    'depreciacion_total': Decimal('0')
                }
            
            categorias_resumen[cat_nombre]['cantidad'] += 1
            categorias_resumen[cat_nombre]['costo_total'] += activo.costo_adquisicion
            categorias_resumen[cat_nombre]['depreciacion_total'] += activo.depreciacion_acumulada_niif
        
        data_resumen = [['Categoría', 'Cantidad', 'Costo Total', 'Depreciación Acum.', 'Valor Neto']]
        
        for cat_nombre, datos in categorias_resumen.items():
            valor_neto = datos['costo_total'] - datos['depreciacion_total']
            data_resumen.append([
                cat_nombre,
                str(datos['cantidad']),
                f"${datos['costo_total']:,.0f}",
                f"${datos['depreciacion_total']:,.0f}",
                f"${valor_neto:,.0f}"
            ])
        
        table_resumen = Table(data_resumen, colWidths=[2*inch, 1*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        table_resumen.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ]))
        
        story.append(table_resumen)
    
    # Generar PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

def generar_reporte_depreciacion_mensual(db: Session, empresa_id: int, anio: int, mes: int) -> BytesIO:
    """
    Genera PDF con el reporte de depreciación del mes
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Obtener datos
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    
    # Buscar novedades de depreciación del mes
    from datetime import date as date_class
    import calendar
    
    primer_dia = date_class(anio, mes, 1)
    ultimo_dia = date_class(anio, mes, calendar.monthrange(anio, mes)[1])
    
    novedades = db.query(ActivoNovedad).join(ActivoFijo).filter(
        ActivoFijo.empresa_id == empresa_id,
        ActivoNovedad.tipo == 'DEPRECIACION',
        ActivoNovedad.fecha >= primer_dia,
        ActivoNovedad.fecha <= ultimo_dia
    ).order_by(ActivoFijo.codigo).all()
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Contenido
    story = []
    
    # Encabezado
    story.append(Paragraph(f"<b>{empresa.razon_social}</b>", title_style))
    story.append(Paragraph(f"NIT: {empresa.nit}", styles['Normal']))
    story.append(Paragraph("<b>REPORTE DE DEPRECIACIÓN MENSUAL</b>", title_style))
    story.append(Paragraph(f"Período: {mes:02d}/{anio}", styles['Heading2']))
    story.append(Paragraph(f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    if not novedades:
        story.append(Paragraph(f"No se registraron depreciaciones para el período {mes:02d}/{anio}.", styles['Normal']))
    else:
        # Tabla de depreciaciones
        data = [
            ['Código', 'Nombre del Activo', 'Categoría', 'Costo Adquisición', 'Dep. Acum. Anterior', 'Dep. del Mes', 'Dep. Acum. Total', 'Valor Neto']
        ]
        
        total_depreciacion_mes = Decimal('0')
        total_costo = Decimal('0')
        total_depreciacion_acum = Decimal('0')
        
        for novedad in novedades:
            activo = novedad.activo
            dep_acum_anterior = activo.depreciacion_acumulada_niif - novedad.valor
            valor_neto = activo.costo_adquisicion - activo.depreciacion_acumulada_niif
            
            data.append([
                activo.codigo,
                activo.nombre[:25] + ('...' if len(activo.nombre) > 25 else ''),
                activo.categoria.nombre if activo.categoria else 'N/A',
                f"${activo.costo_adquisicion:,.0f}",
                f"${dep_acum_anterior:,.0f}",
                f"${novedad.valor:,.0f}",
                f"${activo.depreciacion_acumulada_niif:,.0f}",
                f"${valor_neto:,.0f}"
            ])
            
            total_depreciacion_mes += novedad.valor
            total_costo += activo.costo_adquisicion
            total_depreciacion_acum += activo.depreciacion_acumulada_niif
        
        # Fila de totales
        total_neto = total_costo - total_depreciacion_acum
        data.append([
            '', '', 'TOTALES:', 
            f"${total_costo:,.0f}",
            '',
            f"${total_depreciacion_mes:,.0f}",
            f"${total_depreciacion_acum:,.0f}",
            f"${total_neto:,.0f}"
        ])
        
        # Crear tabla
        table = Table(data, colWidths=[0.7*inch, 1.8*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),  # Alinear números a la derecha
        ]))
        
        story.append(table)
        
        # Resumen contable
        story.append(Spacer(1, 30))
        story.append(Paragraph("<b>ASIENTO CONTABLE SUGERIDO</b>", styles['Heading2']))
        
        asiento_data = [
            ['Cuenta', 'Descripción', 'Débito', 'Crédito'],
            ['516005', 'Depreciación Equipos de Oficina', f"${total_depreciacion_mes:,.0f}", ''],
            ['159205', 'Dep. Acum. Equipos de Oficina', '', f"${total_depreciacion_mes:,.0f}"],
            ['', 'TOTALES:', f"${total_depreciacion_mes:,.0f}", f"${total_depreciacion_mes:,.0f}"]
        ]
        
        asiento_table = Table(asiento_data, colWidths=[1*inch, 3*inch, 1.5*inch, 1.5*inch])
        asiento_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ]))
        
        story.append(asiento_table)
    
    # Generar PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

def generar_hoja_vida_activo(db: Session, activo_id: int, empresa_id: int) -> BytesIO:
    """
    Genera PDF con la hoja de vida completa de un activo específico
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Obtener datos
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    activo = db.query(ActivoFijo).filter(
        ActivoFijo.id == activo_id,
        ActivoFijo.empresa_id == empresa_id
    ).first()
    
    if not activo:
        raise ValueError("Activo no encontrado")
    
    # Obtener historial de novedades
    novedades = db.query(ActivoNovedad).filter(
        ActivoNovedad.activo_id == activo_id
    ).order_by(ActivoNovedad.fecha.desc()).all()
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Contenido
    story = []
    
    # Encabezado
    story.append(Paragraph(f"<b>{empresa.razon_social}</b>", title_style))
    story.append(Paragraph(f"NIT: {empresa.nit}", styles['Normal']))
    story.append(Paragraph("<b>HOJA DE VIDA DEL ACTIVO FIJO</b>", title_style))
    story.append(Spacer(1, 20))
    
    # Información básica del activo
    info_data = [
        ['Código:', activo.codigo],
        ['Nombre:', activo.nombre],
        ['Descripción:', activo.descripcion or 'N/A'],
        ['Categoría:', activo.categoria.nombre if activo.categoria else 'N/A'],
        ['Serial:', activo.serial or 'N/A'],
        ['Marca:', activo.marca or 'N/A'],
        ['Modelo:', activo.modelo or 'N/A'],
        ['Estado:', activo.estado.value],
        ['Ubicación:', activo.ubicacion or 'N/A'],
        ['Responsable:', activo.responsable.razon_social if activo.responsable else 'N/A'],
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 20))
    
    # Información financiera
    story.append(Paragraph("<b>INFORMACIÓN FINANCIERA</b>", styles['Heading2']))
    
    valor_neto = activo.costo_adquisicion - activo.depreciacion_acumulada_niif
    
    financiera_data = [
        ['Fecha de Compra:', activo.fecha_compra.strftime('%d/%m/%Y') if activo.fecha_compra else 'N/A'],
        ['Fecha Inicio Uso:', activo.fecha_inicio_uso.strftime('%d/%m/%Y') if activo.fecha_inicio_uso else 'N/A'],
        ['Costo de Adquisición:', f"${activo.costo_adquisicion:,.0f}"],
        ['Valor Residual:', f"${activo.valor_residual:,.0f}"],
        ['Depreciación Acumulada:', f"${activo.depreciacion_acumulada_niif:,.0f}"],
        ['Valor Neto Actual:', f"${valor_neto:,.0f}"],
        ['Vida Útil (meses):', str(activo.categoria.vida_util_niif_meses) if activo.categoria else 'N/A'],
        ['Método Depreciación:', activo.categoria.metodo_depreciacion.value if activo.categoria else 'N/A'],
    ]
    
    financiera_table = Table(financiera_data, colWidths=[2*inch, 4*inch])
    financiera_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(financiera_table)
    story.append(Spacer(1, 20))
    
    # Historial de movimientos
    story.append(Paragraph("<b>HISTORIAL DE MOVIMIENTOS</b>", styles['Heading2']))
    
    if novedades:
        historial_data = [['Fecha', 'Tipo', 'Valor', 'Observación']]
        
        for novedad in novedades:
            historial_data.append([
                novedad.fecha.strftime('%d/%m/%Y'),
                novedad.tipo.value,
                f"${novedad.valor:,.0f}" if novedad.valor else 'N/A',
                novedad.observacion or 'N/A'
            ])
        
        historial_table = Table(historial_data, colWidths=[1*inch, 1.5*inch, 1.5*inch, 3*inch])
        historial_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
        ]))
        
        story.append(historial_table)
    else:
        story.append(Paragraph("No se registran movimientos para este activo.", styles['Normal']))
    
    # Generar PDF
    doc.build(story)
    buffer.seek(0)
    return buffer