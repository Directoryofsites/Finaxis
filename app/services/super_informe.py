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
from weasyprint import HTML

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
    # (Esta función no necesita cambios, ya que solo prepara datos)
    print(f"--- BUSCANDO EN SUPER INFORME CON FILTROS: {filtros.model_dump()} ---")

    try:
        tipo_entidad = filtros.tipoEntidad
        query = None

        # Alias para tercero de movimiento
        from sqlalchemy.orm import aliased
        TerceroMov = aliased(models_tercero)

        if tipo_entidad == 'movimientos':
            if filtros.estadoDocumento in ['activos', 'anulados']:
                query = db.query(
                    models_mov.id.label('movimiento_id'),
                    models_doc.id.label('documento_id'),
                    models_doc.fecha,
                    models_tipo.nombre.label("tipo_documento"),
                    models_doc.numero,
                    models_tercero.razon_social.label("beneficiario_doc"), # Renamed for clarity, fallback
                    TerceroMov.razon_social.label("beneficiario"), # Priority: Movimiento Tercero
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
                    # --- NUEVAS COLUMNAS DE PRODUCTO ---
                    models_producto.codigo.label("producto_codigo"),
                    models_producto.nombre.label("producto_nombre"),
                    models_mov.cantidad.label("cantidad_movimiento")
                    # -----------------------------------
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
                .filter(models_doc.empresa_id == empresa_id)

                if filtros.estadoDocumento == 'activos':
                    query = query.filter(models_doc.anulado == False, models_doc.estado == 'ACTIVO')
                elif filtros.estadoDocumento == 'anulados':
                    query = query.filter(models_doc.anulado == True, models_doc.estado == 'ANULADO')

            elif filtros.estadoDocumento == 'eliminados':
                 # (Mantener lógica original para eliminados, ya que no tienen tercero_id aun)
                 query = db.query(
                    models_mov_elim.id.label('movimiento_id'),
                    models_doc_elim.id.label('documento_id'),
                    models_doc_elim.fecha,
                    models_tipo.nombre.label("tipo_documento"),
                    models_doc_elim.numero,
                    models_tercero.razon_social.label("beneficiario"), # Solo Header
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
                    models_log.usuario_id.label('usuario_operacion_id')
                ).join(models_doc_elim, models_mov_elim.documento_eliminado_id == models_doc_elim.id)\
                .join(models_log, models_doc_elim.log_eliminacion_id == models_log.id)\
                .join(models_plan, models_mov_elim.cuenta_id == models_plan.id)\
                .join(models_tipo, models_doc_elim.tipo_documento_id == models_tipo.id)\
                .outerjoin(models_tercero, models_doc_elim.beneficiario_id == models_tercero.id)\
                .outerjoin(models_centro_costo, models_mov_elim.centro_costo_id == models_centro_costo.id)\
                .filter(models_doc_elim.empresa_id == empresa_id)

            if query:
                table_doc = models_doc_elim if filtros.estadoDocumento == 'eliminados' else models_doc
                table_mov = models_mov_elim if filtros.estadoDocumento == 'eliminados' else models_mov

                if filtros.fechaInicio: query = query.filter(table_doc.fecha >= filtros.fechaInicio)
                if filtros.fechaFin: query = query.filter(table_doc.fecha <= filtros.fechaFin)
                if filtros.tipoDocIds: query = query.filter(table_doc.tipo_documento_id.in_(filtros.tipoDocIds))

                if filtros.numero:
                    try:
                        # Logic for multi-value filtering (comma separated)
                        raw_nums = str(filtros.numero).replace(' ', '').split(',')
                        
                        if filtros.estadoDocumento == 'eliminados':
                            # For 'eliminados', numero is treated as string in this logic (though model might store it as int/str)
                            # Looking at model def, models_doc_elim.numero is usually String or Integer? 
                            # Previous code cast it to str(). Let's stick to str for 'eliminados' if that was expected.
                            # But wait, original code: query.filter(table_doc.numero == str(filtros.numero))
                            if len(raw_nums) > 1:
                                query = query.filter(table_doc.numero.in_(raw_nums))
                            else:
                                query = query.filter(table_doc.numero == raw_nums[0])
                        else:
                            # For active/anulados (models_doc.numero is likely Integer)
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
                
                # --- NUEVO FILTRO DE PRODUCTOS ---
                if filtros.productoIds and filtros.estadoDocumento != 'eliminados':
                     # Solo aplicamos a movimientos activos que tienen la col producto_id
                     query = query.filter(table_mov.producto_id.in_(filtros.productoIds))
                # ---------------------------------
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

                user_ids = set()
                for r in resultados_orm:
                    if r.usuario_creador_id: user_ids.add(r.usuario_creador_id)
                    if hasattr(r, 'usuario_operacion_id') and r.usuario_operacion_id: user_ids.add(r.usuario_operacion_id)

                user_map = {}
                if user_ids:
                    usuarios_db = db.query(models_usuario.id, models_usuario.nombre_completo, models_usuario.email).filter(models_usuario.id.in_(user_ids)).all()
                    user_map = {user.id: {'nombre': user.nombre_completo, 'email': user.email} for user in usuarios_db}

                resultados_finales = []
                for r in resultados_orm:
                    fila = r._asdict()

                    # Fallback de Beneficiario (Movimiento > Documento)
                    if not fila.get('beneficiario') and fila.get('beneficiario_doc'):
                         fila['beneficiario'] = fila['beneficiario_doc']

                    creador_data = user_map.get(r.usuario_creador_id)
                    if creador_data:
                        fila['usuario_creador'] = creador_data['nombre'] if creador_data['nombre'] else creador_data['email']
                    else:
                        fila['usuario_creador'] = 'N/A'

                    operacion_data = user_map.get(r.usuario_operacion_id if hasattr(r, 'usuario_operacion_id') else None)
                    if operacion_data:
                         fila['usuario_operacion'] = operacion_data['nombre'] if operacion_data['nombre'] else operacion_data['email']
                    else:
                        fila['usuario_operacion'] = 'N/A'

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
    filtros.traerTodo = True
    response_data = generate_super_informe(db, filtros, empresa_id)

    resultados = response_data["resultados"]
    empresa_info = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    title_parts = [f"Informe de {filtros.tipoEntidad.replace('_', ' ').title()}"]
    if filtros.fechaInicio and filtros.fechaFin:
        fecha_str = f"del {filtros.fechaInicio.strftime('%d/%m/%Y')} al {filtros.fechaFin.strftime('%d/%m/%Y')}"
    else:
        fecha_str = "de todo el período"
    title_parts.append(fecha_str)
    report_title = " ".join(title_parts)
    headers, processed_rows, totales = [], [], {"debito": 0.0, "credito": 0.0}

    def _format_currency(value):
        # User requested NO decimals ("quítale los decimales")
        return f"${float(value or 0):,.0f}"

    if filtros.tipoEntidad == 'movimientos':
        # Removed "Producto", "Cant." as requested.
        # Adjusted Column Widths:
        # Original ~14 columns. Now 12.
        # Gained space from Prod/Cant allocated to Concept (high priority) and Debit/Credit.
        headers = ["Fecha", "Documento", "Num", "Beneficiario", "Cuenta", "C. Costo", "Concepto", "Débito", "Crédito", "Usuario Creador", "Justificación", "Usuario Op."]
        
        column_widths = [
            "6%",  # Fecha
            "6%",  # Documento
            "4%",  # Num
            "10%", # Beneficiario
            "10%", # Cuenta
            "7%",  # C. Costo
            "23%", # Concepto (Significantly increased)
            "9%",  # Débito (Increased)
            "9%",  # Crédito (Increased)
            "6%",  # Usuario Creador
            "5%",  # Justificación
            "5%"   # Usuario Op.
        ]

        for item in resultados:
            totales["debito"] += float(item.get('debito') or 0)
            totales["credito"] += float(item.get('credito') or 0)
            processed_rows.append({
                'cells': [
                    item.get('fecha').strftime('%d/%m/%Y') if item.get('fecha') else 'N/A',
                    (item.get('tipo_documento') or '').strip() or f"Doc {item.get('documento_id') or 'N/A'}",
                    item.get('numero') or 'N/A',
                    item.get('beneficiario') or 'N/A',
                    f"{item.get('cuenta_codigo', '')} - {item.get('cuenta_nombre', '')}",
                    # REMOVED: Producto
                    # REMOVED: Cantidad
                    item.get('centro_costo') or 'N/A',
                    item.get('concepto') or '',
                    _format_currency(item.get('debito')),
                    _format_currency(item.get('credito')),
                    item.get('usuario_creador') or 'N/A',
                    item.get('justificacion') or 'N/A',
                    item.get('usuario_operacion') or 'N/A'
                ], 
                'estado': item.get('estado')
            })
    else:
        raise HTTPException(status_code=400, detail=f"PDF no soportado para entidad '{filtros.tipoEntidad}'.")

    context = {
        "empresa": empresa_info,
        "report_title": report_title,
        "fecha_generacion": date.today().strftime('%d/%m/%Y'),
        "headers": headers,
        "column_widths": column_widths, # INJECTED WIDTHS
        "processed_rows": processed_rows,
        "totales": {
            "debito": f"${totales['debito']:,.0f}", # No decimals
            "credito": f"${totales['credito']:,.0f}", # No decimals
            "diferencia": f"${(totales['debito'] - totales['credito']):,.0f}" # No decimals
        },
        "show_totals": filtros.tipoEntidad == 'movimientos'
    }

    # --- MOTOR RUST DESACTIVADO A PETICIÓN DEL USUARIO ---
    # (El usuario prefirió la estética original aunque fuera más lento)
    # try:
    #     import rust_reports
    #     # ... (Lógica Rust comentada para futura referencia o eliminación) ...
    # except ImportError:
    #     pass
    
    # FALLBACK: WeasyPrint (Lento pero seguro y con el diseño original exacto)
    try:
        print("[PDF] Usando motor original WeasyPrint (Python native)")
        template_string = TEMPLATES_EMPAQUETADOS['reports/super_informe_report.html']
        template = GLOBAL_JINJA_ENV.from_string(template_string)
        html_string = template.render(context)
        return HTML(string=html_string).write_pdf()
    except KeyError:
        raise HTTPException(status_code=500, detail="La plantilla 'reports/super_informe_report.html' no fue encontrada en el paquete.")
    except Exception as e:
        print(f"ERROR AL RENDERIZAR PLANTILLA: {e}")
        raise HTTPException(status_code=500, detail=f"Error al generar el PDF: {e}")
    # --- FIN: CÓDIGO REFACTORIZADO ---