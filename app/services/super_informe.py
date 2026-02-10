# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, cast, String, Boolean
from fastapi import HTTPException
from datetime import date
from typing import List, Dict, Any
import math

from app.models import (
    Empresa as models_empresa,
    Documento as models_doc,
    MovimientoContable as models_mov,
    TipoDocumento as models_tipo,
    Tercero as models_tercero,
    PlanCuenta as models_plan,
    CentroCosto as models_centro_costo,
    DocumentoEliminado as models_doc_elim,
    MovimientoEliminado as models_mov_elim,
    LogOperacion as models_log,
    Usuario as models_usuario,
    Producto as models_producto # Importamos modelo Producto
)
from app.schemas import documento as schemas_doc
# ReportLab Imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, LongTable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
import time as time_module
from datetime import datetime
from weasyprint import HTML
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, LongTable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
import time as time_module
from datetime import datetime

# --- INICIO: ARQUITECTURA DE PLANTILLAS REFACTORIZADA ---
# 1. Importamos el nuevo diccionario con las plantillas pre-compiladas.
from app.services._templates_empaquetados import TEMPLATES_EMPAQUETADOS

# 2. Importamos Jinja2 Environment.
from jinja2 import Environment, select_autoescape

# 3. Creamos una instancia del entorno de Jinja2 para este módulo.
GLOBAL_JINJA_ENV = Environment(loader=None, autoescape=select_autoescape(['html', 'xml']))
# --- FIN: ARQUITECTURA DE PLANTILLAS REFACTORIZADA ---


def generate_super_informe(db: Session, filtros: schemas_doc.DocumentoGestionFiltros, empresa_id: int) -> Dict[str, Any]:
    """
    Motor de búsqueda dinámico para el Super Informe, con lógica de paginación completa
    y enriquecido con datos de auditoría mediante una estrategia de dos pasos.
    """
    # (Esta función ha sido optimizada para hacer joins directos con Usuario)
    print(f"--- BUSCANDO EN SUPER INFORME CON FILTROS (OPTIMIZADO): {filtros.model_dump()} ---")

    try:
        tipo_entidad = filtros.tipoEntidad
        query = None

        # Alias para joins
        from sqlalchemy.orm import aliased
        TerceroMov = aliased(models_tercero)
        UsuarioCreator = aliased(models_usuario)
        UsuarioOperator = aliased(models_usuario)

        if tipo_entidad == 'movimientos':
            if filtros.estadoDocumento in ['activos', 'anulados']:
                base_query = db.query(
                    models_mov.id.label('movimiento_id'),
                    models_doc.id.label('documento_id'),
                    models_doc.fecha,
                    models_tipo.nombre.label("tipo_documento"),
                    models_doc.numero,
                    func.coalesce(models_tercero.razon_social, '').label("beneficiario_doc"),
                    func.coalesce(TerceroMov.razon_social, '').label("beneficiario_mov"),
                    models_plan.codigo.label("cuenta_codigo"),
                    models_plan.nombre.label("cuenta_nombre"),
                    models_centro_costo.nombre.label("centro_costo"),
                    models_mov.concepto,
                    models_mov.debito,
                    models_mov.credito,
                    models_doc.anulado,
                    models_doc.estado,
                    models_doc.usuario_creador_id,
                    models_log.razon.label('justificacion'),
                    models_log.usuario_id.label('usuario_operacion_id'),
                    # --- NUEVAS COLUMNAS DE USUARIO (Optimize joins) ---
                    func.coalesce(UsuarioCreator.nombre_completo, UsuarioCreator.email, 'N/A').label('usuario_creador_nombre'),
                    func.coalesce(UsuarioOperator.nombre_completo, UsuarioOperator.email, 'N/A').label('usuario_operacion_nombre'),
                    # --- COLUMNAS DE PRODUCTO ---
                    models_producto.codigo.label("producto_codigo"),
                    models_producto.nombre.label("producto_nombre"),
                    models_mov.cantidad.label("cantidad_movimiento")
                ).join(models_doc, models_mov.documento_id == models_doc.id)\
                .join(models_plan, models_mov.cuenta_id == models_plan.id)\
                .join(models_tipo, models_doc.tipo_documento_id == models_tipo.id)\
                .outerjoin(models_tercero, models_doc.beneficiario_id == models_tercero.id)\
                .outerjoin(TerceroMov, models_mov.tercero_id == TerceroMov.id)\
                .outerjoin(models_centro_costo, models_mov.centro_costo_id == models_centro_costo.id)\
                .outerjoin(models_producto, models_mov.producto_id == models_producto.id)\
                .outerjoin(models_log, and_(
                    models_log.tipo_operacion == 'ANULACION',
                    models_log.documento_id_asociado == models_doc.id
                ))\
                .outerjoin(UsuarioCreator, models_doc.usuario_creador_id == UsuarioCreator.id)\
                .outerjoin(UsuarioOperator, models_log.usuario_id == UsuarioOperator.id)\
                .filter(models_doc.empresa_id == empresa_id)

                if filtros.estadoDocumento == 'activos':
                    query = base_query.filter(models_doc.anulado == False, models_doc.estado == 'ACTIVO')
                elif filtros.estadoDocumento == 'anulados':
                    query = base_query.filter(models_doc.anulado == True, models_doc.estado == 'ANULADO')

            elif filtros.estadoDocumento == 'eliminados':
                 query = db.query(
                    models_mov_elim.id.label('movimiento_id'),
                    models_doc_elim.id.label('documento_id'),
                    models_doc_elim.fecha,
                    models_tipo.nombre.label("tipo_documento"),
                    models_doc_elim.numero,
                    models_tercero.razon_social.label("beneficiario"),
                    models_plan.codigo.label("cuenta_codigo"),
                    models_plan.nombre.label("cuenta_nombre"),
                    models_centro_costo.nombre.label("centro_costo"),
                    models_mov_elim.concepto,
                    models_mov_elim.debito,
                    models_mov_elim.credito,
                    cast(True, Boolean).label('anulado'),
                    cast('ELIMINADO', String).label('estado'),
                    models_doc_elim.usuario_creador_id,
                    models_log.razon.label('justificacion'),
                    models_log.usuario_id.label('usuario_operacion_id'),
                    # --- NUEVAS COLUMNAS DE USUARIO (Optimizadas) ---
                    func.coalesce(UsuarioCreator.nombre_completo, UsuarioCreator.email, 'N/A').label('usuario_creador_nombre'),
                    func.coalesce(UsuarioOperator.nombre_completo, UsuarioOperator.email, 'N/A').label('usuario_operacion_nombre')
                ).join(models_doc_elim, models_mov_elim.documento_eliminado_id == models_doc_elim.id)\
                .join(models_log, models_doc_elim.log_eliminacion_id == models_log.id)\
                .join(models_plan, models_mov_elim.cuenta_id == models_plan.id)\
                .join(models_tipo, models_doc_elim.tipo_documento_id == models_tipo.id)\
                .outerjoin(models_tercero, models_doc_elim.beneficiario_id == models_tercero.id)\
                .outerjoin(models_centro_costo, models_mov_elim.centro_costo_id == models_centro_costo.id)\
                .outerjoin(UsuarioCreator, models_doc_elim.usuario_creador_id == UsuarioCreator.id)\
                .outerjoin(UsuarioOperator, models_log.usuario_id == UsuarioOperator.id)\
                .filter(models_doc_elim.empresa_id == empresa_id)

            if query:
                table_doc = models_doc_elim if filtros.estadoDocumento == 'eliminados' else models_doc
                table_mov = models_mov_elim if filtros.estadoDocumento == 'eliminados' else models_mov

                if filtros.fechaInicio: query = query.filter(table_doc.fecha >= filtros.fechaInicio)
                if filtros.fechaFin: query = query.filter(table_doc.fecha <= filtros.fechaFin)
                if filtros.tipoDocIds: query = query.filter(table_doc.tipo_documento_id.in_(filtros.tipoDocIds))

                if filtros.numero:
                    try:
                        raw_nums = str(filtros.numero).replace(' ', '').split(',')
                        
                        if filtros.estadoDocumento == 'eliminados':
                            if len(raw_nums) > 1:
                                query = query.filter(table_doc.numero.in_(raw_nums))
                            else:
                                query = query.filter(table_doc.numero == raw_nums[0])
                        else:
                            parsed_nums = [int(n) for n in raw_nums if n.isdigit()]
                            if parsed_nums:
                                if len(parsed_nums) > 1:
                                    query = query.filter(table_doc.numero.in_(parsed_nums))
                                else:
                                    query = query.filter(table_doc.numero == parsed_nums[0])
                            
                    except (ValueError, TypeError):
                        pass

                if filtros.terceroIds: query = query.filter(table_doc.beneficiario_id.in_(filtros.terceroIds))
                if filtros.cuentaIds: query = query.filter(table_mov.cuenta_id.in_(filtros.cuentaIds))
                if filtros.centroCostoIds: query = query.filter(table_mov.centro_costo_id.in_(filtros.centroCostoIds))
                
                if filtros.productoIds and filtros.estadoDocumento != 'eliminados':
                     query = query.filter(table_mov.producto_id.in_(filtros.productoIds))
                
                if filtros.conceptoKeyword: query = query.filter(table_mov.concepto.ilike(f"%{filtros.conceptoKeyword}%"))

                if filtros.valorOperador and filtros.valorMonto is not None:
                    monto = filtros.valorMonto
                    if filtros.valorOperador == 'mayor':
                        query = query.filter(or_(table_mov.debito > monto, table_mov.credito > monto))
                    elif filtros.valorOperador == 'menor':
                        query = query.filter(or_(
                            and_(table_mov.debito < monto, table_mov.debito > 0),
                            and_(table_mov.credito < monto, table_mov.credito > 0)
                        ))
                    elif filtros.valorOperador == 'igual':
                        query = query.filter(or_(table_mov.debito == monto, table_mov.credito == monto))

                total_count_query = query.with_entities(func.count(table_mov.id))
                total_registros = total_count_query.scalar() or 0

                if filtros.traerTodo:
                    resultados_orm = query.order_by(table_doc.fecha.desc(), table_doc.numero.desc()).all()
                else:
                    pagina_actual = filtros.pagina
                    limite = filtros.limite
                    offset = (pagina_actual - 1) * limite
                    resultados_orm = query.order_by(table_doc.fecha.desc(), table_doc.numero.desc()).offset(offset).limit(limite).all()

                # --- RESULTADOS DIRECTOS SIN BUCLE DE MAPEO ---
                resultados_finales = []
                for r in resultados_orm:
                    fila = r._asdict()

                    # Fallback lógica de beneficiario
                    if fila.get('beneficiario_mov'):
                        fila['beneficiario'] = fila['beneficiario_mov']
                    elif fila.get('beneficiario_doc'):
                         fila['beneficiario'] = fila['beneficiario_doc']

                    # Mapear nombres directos
                    fila['usuario_creador'] = fila.get('usuario_creador_nombre', 'N/A')
                    fila['usuario_operacion'] = fila.get('usuario_operacion_nombre', 'N/A')

                    resultados_finales.append(fila)

                total_paginas = 1 if filtros.traerTodo else (math.ceil(total_registros / filtros.limite) if total_registros > 0 else 1)

                return {
                    "total_registros": total_registros,
                    "total_paginas": total_paginas,
                    "pagina_actual": filtros.pagina if not filtros.traerTodo else 1,
                    "resultados": resultados_finales
                }
        else:
             raise HTTPException(status_code=400, detail=f"Tipo de entidad '{tipo_entidad}' no soportado.")

    except Exception as e:
        print(f"Error inesperado en get_super_informe: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ocurrió un error inesperado al procesar la solicitud: {str(e)}")


def generate_super_informe_pdf(db: Session, filtros: schemas_doc.DocumentoGestionFiltros, empresa_id: int):
    """
    Genera el PDF del Super Informe usando REPORTLAB (Optimizado).
    Reemplaza la version anterior de WeasyPrint.
    """
    filtros.traerTodo = True

    # Validamos entidad
    if filtros.tipoEntidad != 'movimientos':
        raise HTTPException(status_code=400, detail=f"PDF no soportado para entidad '{filtros.tipoEntidad}'.")

    # Imports necesarios dentro
    from sqlalchemy.orm import aliased
    TerceroMov = aliased(models_tercero)
    UsuarioCreator = aliased(models_usuario)
    UsuarioOperator = aliased(models_usuario)

    print("--- [ReportLab] Iniciando generacion Super Informe (Contable) ---")
    start_time = time_module.time()

    # --- 1. Construir QUERY BASE (Sin ejecutar) ---
    query = None
    if filtros.estadoDocumento in ['activos', 'anulados']:
        base_query = db.query(
            models_doc.fecha.label('fecha'),
            models_doc.numero,
            models_tipo.nombre.label("tipo_documento"),
            models_doc.id.label('documento_id'),
            # Coalesce lógico para beneficiario
            func.coalesce(TerceroMov.razon_social, models_tercero.razon_social, '').label("beneficiario"),
            models_plan.codigo.label("cuenta_codigo"),
            models_plan.nombre.label("cuenta_nombre"),
            models_centro_costo.nombre.label("centro_costo"),
            models_mov.concepto,
            models_mov.debito,
            models_mov.credito,
            models_doc.estado,
            models_log.razon.label('justificacion'),
            # Usuarios directos
            func.coalesce(UsuarioCreator.nombre_completo, UsuarioCreator.email, 'N/A').label('usuario_creador'),
            func.coalesce(UsuarioOperator.nombre_completo, UsuarioOperator.email, 'N/A').label('usuario_operacion')
        ).join(models_doc, models_mov.documento_id == models_doc.id)\
        .join(models_plan, models_mov.cuenta_id == models_plan.id)\
        .join(models_tipo, models_doc.tipo_documento_id == models_tipo.id)\
        .outerjoin(models_tercero, models_doc.beneficiario_id == models_tercero.id)\
        .outerjoin(TerceroMov, models_mov.tercero_id == TerceroMov.id)\
        .outerjoin(models_centro_costo, models_mov.centro_costo_id == models_centro_costo.id)\
        .outerjoin(models_log, and_(
            models_log.tipo_operacion == 'ANULACION',
            models_log.documento_id_asociado == models_doc.id
        ))\
        .outerjoin(UsuarioCreator, models_doc.usuario_creador_id == UsuarioCreator.id)\
        .outerjoin(UsuarioOperator, models_log.usuario_id == UsuarioOperator.id)\
        .filter(models_doc.empresa_id == empresa_id)

        if filtros.estadoDocumento == 'activos':
            query = base_query.filter(models_doc.anulado == False, models_doc.estado == 'ACTIVO')
        elif filtros.estadoDocumento == 'anulados':
            query = base_query.filter(models_doc.anulado == True, models_doc.estado == 'ANULADO')

    elif filtros.estadoDocumento == 'eliminados':
         query = db.query(
            models_doc_elim.fecha,
            models_doc_elim.numero,
            models_tipo.nombre.label("tipo_documento"),
            models_doc_elim.id.label('documento_id'),
            models_tercero.razon_social.label("beneficiario"),
            models_plan.codigo.label("cuenta_codigo"),
            models_plan.nombre.label("cuenta_nombre"),
            models_centro_costo.nombre.label("centro_costo"),
            models_mov_elim.concepto,
            models_mov_elim.debito,
            models_mov_elim.credito,
            cast('ELIMINADO', String).label('estado'),
            models_log.razon.label('justificacion'),
            func.coalesce(UsuarioCreator.nombre_completo, UsuarioCreator.email, 'N/A').label('usuario_creador'),
            func.coalesce(UsuarioOperator.nombre_completo, UsuarioOperator.email, 'N/A').label('usuario_operacion')
        ).join(models_doc_elim, models_mov_elim.documento_eliminado_id == models_doc_elim.id)\
        .join(models_log, models_doc_elim.log_eliminacion_id == models_log.id)\
        .join(models_plan, models_mov_elim.cuenta_id == models_plan.id)\
        .join(models_tipo, models_doc_elim.tipo_documento_id == models_tipo.id)\
        .outerjoin(models_tercero, models_doc_elim.beneficiario_id == models_tercero.id)\
        .outerjoin(models_centro_costo, models_mov_elim.centro_costo_id == models_centro_costo.id)\
        .outerjoin(UsuarioCreator, models_doc_elim.usuario_creador_id == UsuarioCreator.id)\
        .outerjoin(UsuarioOperator, models_log.usuario_id == UsuarioOperator.id)\
        .filter(models_doc_elim.empresa_id == empresa_id)

    # --- Aplicar Filtros (Copiar logica) ---
    if query:
        table_doc = models_doc_elim if filtros.estadoDocumento == 'eliminados' else models_doc
        table_mov = models_mov_elim if filtros.estadoDocumento == 'eliminados' else models_mov

        if filtros.fechaInicio: query = query.filter(table_doc.fecha >= filtros.fechaInicio)
        if filtros.fechaFin: query = query.filter(table_doc.fecha <= filtros.fechaFin)
        if filtros.tipoDocIds: query = query.filter(table_doc.tipo_documento_id.in_(filtros.tipoDocIds))

        if filtros.numero:
            # (Simplificado para evitar duplicar logica compleja, asumir filtro limpio o ignorar si error)
            try:
                raw_nums = str(filtros.numero).replace(' ', '').split(',')
                # Logica simplificada: si son digitos filtrar
                parsed_nums = [x for x in raw_nums if x.isdigit()] # Si es eliminados y es string igual funciona con in_?
                # Para mayor seguridad, si es activos casting a int
                if filtros.estadoDocumento != 'eliminados':
                    parsed_nums = [int(x) for x in parsed_nums]

                if parsed_nums:
                    if len(parsed_nums) > 1: query = query.filter(table_doc.numero.in_(parsed_nums))
                    else: query = query.filter(table_doc.numero == parsed_nums[0])
            except: pass

        if filtros.terceroIds: query = query.filter(table_doc.beneficiario_id.in_(filtros.terceroIds))
        if filtros.cuentaIds: query = query.filter(table_mov.cuenta_id.in_(filtros.cuentaIds))
        if filtros.centroCostoIds: query = query.filter(table_mov.centro_costo_id.in_(filtros.centroCostoIds))
        if filtros.productoIds and filtros.estadoDocumento != 'eliminados':
             query = query.filter(table_mov.producto_id.in_(filtros.productoIds))
        if filtros.conceptoKeyword: query = query.filter(table_mov.concepto.ilike(f"%{filtros.conceptoKeyword}%"))
        
        # Filtro Montos
        if filtros.valorOperador and filtros.valorMonto is not None:
            monto = filtros.valorMonto
            if filtros.valorOperador == 'mayor': query = query.filter(or_(table_mov.debito > monto, table_mov.credito > monto))
            elif filtros.valorOperador == 'menor':
                query = query.filter(or_(and_(table_mov.debito < monto, table_mov.debito > 0), and_(table_mov.credito < monto, table_mov.credito > 0)))
            elif filtros.valorOperador == 'igual': query = query.filter(or_(table_mov.debito == monto, table_mov.credito == monto))


    # --- 2. Ejecutar Query ---
    if not query:
        raise HTTPException(status_code=400, detail="Criterios de búsqueda inválidos o estado de documento no especificado.")

    print("--- [ReportLab] Ejecutando Query con .all()... ---")
    t_query_start = time_module.time()
    # Usamos .all() para evitar latencia de streaming en conexiones lentas
    resultados = query.order_by(table_doc.fecha.desc(), table_doc.numero.desc()).all()
    print(f"--- [ReportLab] Query Ejecutado en {time_module.time() - t_query_start:.4f}s. Registros obtenidos: {len(resultados)} ---")

    # --- 3. Generar PDF con ReportLab ---
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=landscape(letter),
        rightMargin=0.5*inch, leftMargin=0.5*inch, 
        topMargin=0.5*inch, bottomMargin=0.5*inch
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilos Personalizados
    styles.add(ParagraphStyle(name='TituloReporte', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=12, spaceAfter=10))
    styles.add(ParagraphStyle(name='Subtitulo', parent=styles['Normal'], alignment=TA_CENTER, fontSize=10))
    styles.add(ParagraphStyle(name='CeldaHeader', parent=styles['Normal'], fontSize=7, fontName='Helvetica-Bold', alignment=TA_CENTER, textColor=colors.black))
    styles.add(ParagraphStyle(name='CeldaBody', parent=styles['Normal'], fontSize=7, fontName='Helvetica', alignment=TA_LEFT))
    styles.add(ParagraphStyle(name='CeldaNumero', parent=styles['Normal'], fontSize=7, fontName='Helvetica', alignment=TA_RIGHT))

    # Encabezado Empresa
    empresa = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    razon_social = getattr(empresa, 'razon_social', 'Empresa Desconocida')
    nit = getattr(empresa, 'nit', 'N/A')
    
    elements.append(Paragraph(f"{razon_social}", styles['TituloReporte']))
    elements.append(Paragraph(f"NIT: {nit}", styles['Subtitulo']))
    
    title_parts = [f"Informe de {filtros.tipoEntidad.replace('_', ' ').title()}"]
    if filtros.fechaInicio and filtros.fechaFin:
        fecha_str = f"Del {filtros.fechaInicio.strftime('%d/%m/%Y')} al {filtros.fechaFin.strftime('%d/%m/%Y')}"
    else: fecha_str = "Todo el período"
    elements.append(Paragraph(f"{title_parts[0]} - {fecha_str}", styles['Subtitulo']))
    elements.append(Spacer(1, 0.2*inch))

    # Tabla
    headers = ["Fecha", "Doc", "Num", "Beneficiario", "Cuenta", "C. Costo", "Concepto", "Débito", "Crédito", "Creador", "Just.", "Oper."]
    # Anchos ajustados para letter landscape (~10 inch usable)
    col_widths = [0.7*inch, 0.7*inch, 0.5*inch, 1.2*inch, 1.2*inch, 0.8*inch, 2.0*inch, 0.8*inch, 0.8*inch, 0.6*inch, 0.6*inch, 0.6*inch]

    data = []
    # Header Row
    header_row = [Paragraph(h, styles['CeldaHeader']) for h in headers]
    data.append(header_row)

    total_debito = 0.0
    total_credito = 0.0

    print("--- [ReportLab] Procesando filas... ---")
    for row in resultados:
        r = row._asdict()
        
        deb = float(r.get('debito') or 0)
        cred = float(r.get('credito') or 0)
        total_debito += deb
        total_credito += cred

        fecha_fmt = r.get('fecha').strftime('%d/%m/%Y') if r.get('fecha') else 'N/A'
        tipo_doc_fmt = (r.get('tipo_documento') or '').strip() or str(r.get('documento_id') or '')
        tipo_doc_short = (tipo_doc_fmt[:10] + '..') if len(tipo_doc_fmt) > 10 else tipo_doc_fmt
        
        cuenta_fmt = f"{r.get('cuenta_codigo', '')} - {r.get('cuenta_nombre', '')}"
        
        row_data = [
            Paragraph(fecha_fmt, styles['CeldaBody']),
            Paragraph(tipo_doc_short, styles['CeldaBody']),
            Paragraph(str(r.get('numero') or ''), styles['CeldaBody']),
            Paragraph(str(r.get('beneficiario') or 'N/A')[:25], styles['CeldaBody']),
            Paragraph(cuenta_fmt, styles['CeldaBody']),
            Paragraph(str(r.get('centro_costo') or '')[:15], styles['CeldaBody']),
            Paragraph(str(r.get('concepto') or '')[:50], styles['CeldaBody']),
            Paragraph(f"{deb:,.0f}", styles['CeldaNumero']),
            Paragraph(f"{cred:,.0f}", styles['CeldaNumero']),
            Paragraph(str(r.get('usuario_creador') or 'N/A')[:10], styles['CeldaBody']),
            Paragraph(str(r.get('justificacion') or 'N/A')[:10], styles['CeldaBody']),
            Paragraph(str(r.get('usuario_operacion') or 'N/A')[:10], styles['CeldaBody']),
        ]
        data.append(row_data)

    # Fila de Totales
    total_row = [
        "", "", "", "", "", "TOTALES:", "",
        Paragraph(f"{total_debito:,.0f}", styles['CeldaNumero']),
        Paragraph(f"{total_credito:,.0f}", styles['CeldaNumero']),
        "", "", ""
    ]
    data.append(total_row)

    # Estilo Tabla
    t = LongTable(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        # Header Style (Match original #eee background, black text)
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.93, 0.93, 0.93)), # #eee
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(0.8, 0.8, 0.8)), # #ccc
        ('fontName', (0, 0), (-1, -1), 'Helvetica'),
        ('fontSize', (0, 0), (-1, -1), 7),
        # Totales Style
        ('BACKGROUND', (0, -1), (-1, -1), colors.Color(0.93, 0.93, 0.93)), # #eee
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    
    elements.append(t)
    
    print("--- [ReportLab] Renderizando PDF final... ---")
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    print(f"--- [ReportLab] Tiempo Total: {time_module.time() - start_time:.4f}s ---")
    return pdf_bytes