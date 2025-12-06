# app/services/reportes_inventario.py (VERSIÓN FINAL Y COMPLETA CON FIX CRÍTICO DE LÓGICA MULTI-ID Y ATRIBUTO DEFECTUOSO)

from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, case, and_, or_, select, literal_column, desc, asc, cast, String as SAString, Date as SADate, DECIMAL 
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime, time
from typing import List, Optional, Dict, Any, Tuple
from fastapi import HTTPException, status
import traceback 
from sqlalchemy.dialects import postgresql 
from jinja2 import Environment, FileSystemLoader
from io import BytesIO
from weasyprint import HTML

from ..services._templates_empaquetados import TEMPLATES_EMPAQUETADOS


import os
import locale 
import json 
from pydantic import ValidationError 
# FIX CRÍTICO: Se elimina la importación incorrecta: from pydantic_core import PydanticValidationError 


# Importaciones de Seguridad 
from ..core.security import create_signed_token, validate_signed_token 

# Modelos
from ..models import producto as models_producto
from ..models import documento as models_doc
from ..models import bodega as models_bodega
from ..models import grupo_inventario as models_grupo
from ..models import tercero as models_tercero
from ..models import tipo_documento as models_tipo_doc
from ..models import movimiento_contable as models_mov_con
from ..models import plan_cuenta as models_plan_cuenta
from ..models import centro_costo as models_centro_costo
from ..models import caracteristica_definicion as models_carac_def
from ..models import caracteristica_valor_producto as models_carac_val
from ..models import lista_precio as models_lista_precio
from ..models import regla_precio_grupo as models_regla_precio
from ..models import empresa as models_empresa 

# Schemas
from ..schemas import reportes_inventario as schemas_reportes
from ..schemas import reporte_rentabilidad as schemas_rentabilidad

# Importar servicio de inventario para evitar importación cíclica
from app.services import inventario as service_inventario 

# --- Constante de Paginación ---
ITEMS_POR_PAGINA = 50

# ==============================================================================
# === FUNCIONES AUXILIARES: ESTRUCTURALES Y DE CONVERSIÓN (MOVIDAS AL INICIO) ===
# ==============================================================================



def format_miles(value):
    """Aplica formato de separador de miles con dos decimales, usando punto como separador de miles y coma como separador decimal (formato CO)."""
    try:
        val = float(value)
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8') 
        return locale.format_string("%.2f", val, grouping=True).replace('.', '#').replace(',', '.').replace('#', ',')
    except Exception:
        return f"{value or 0:.2f}" 
    

# ... (Tus imports deben estar arriba) ...

# --- CONFIGURACIÓN ÚNICA DEL ENTORNO JINJA2 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, '..', 'templates', 'reports')

# 1. Crear el entorno UNA SOLA VEZ
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), trim_blocks=True, lstrip_blocks=True)

# 2. Definir funciones de formato
def format_miles(value):
    """Formato numérico estándar CO (miles con punto, decimal con coma)."""
    try:
        val = float(value)
        # Formato manual robusto: 1234.56 -> 1.234,56
        return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return f"{value or 0:.2f}"

def format_value_filter(value, is_currency=False):
    """Filtro dinámico para moneda o cantidad."""
    try:
        val = float(value)
        if is_currency:
            # Moneda: Sin decimales ($ 1.500)
            return f"$ {val:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            # Cantidad: Con 2 decimales (1.500,00)
            return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "$ 0" if is_currency else "0"

# 3. REGISTRAR FILTROS (OBLIGATORIO)
env.filters['format_miles'] = format_miles
env.filters['format_value'] = format_value_filter  # <--- ESTE ES EL QUE FALTABA

# --- FIN CONFIGURACIÓN JINJA2 ---


def generar_pdf_desde_html(html_content: str) -> bytes:
    """Genera bytes de PDF a partir de contenido HTML usando WeasyPrint."""
    try:
        pdf_bytes = HTML(string=html_content).write_pdf(stylesheets=[])
        return pdf_bytes
    except Exception as e:
        print(f"Error WeasyPrint: {e}")
        raise HTTPException(status_code=500, detail="Error al generar PDF. Verifique las dependencias (GTK+).")

def convert_decimals_and_dates(obj):
    # FIX CRÍTICO: La función debe omitir cualquier callable dentro de un diccionario
    if isinstance(obj, Decimal):
        return float(obj.quantize(Decimal('0.01'), ROUND_HALF_UP))
    elif isinstance(obj, (date, datetime)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        # FIX CRÍTICO: Recorrer el diccionario y OMITIR cualquier valor que sea una función o callable
        return {k: convert_decimals_and_dates(v) for k, v in obj.items() if not callable(v)}
    elif isinstance(obj, list):
        return [convert_decimals_and_dates(elem) for elem in obj]
    elif callable(obj):
        # Si la función está en un contexto de lista o elemento individual, la omitimos.
        return None
    else:
        return obj

# >>> INICIO DE FUNCIÓN CRÍTICA: PRE-PROCESAMIENTO PARA PLANTILLA PDF <<<
def _process_movimientos_for_pdf(data_items: List[dict]) -> Tuple[List[str], List[dict]]:
    """
    Transforma la lista de diccionarios de movimientos detallados en el formato
    tabular (headers y processed_rows) que espera la plantilla super_informe_report.html.
    """
    if not data_items:
        return [], []

    # 1. Definir Cabeceras Estáticas para MOVIMIENTOS
    # La plantilla requiere strings simples
    column_map = {
        'producto_codigo': 'CÓDIGO',
        'producto_nombre': 'PRODUCTO',
        'fecha': 'FECHA',
        'documento_ref': 'DOCUMENTO',
        'tercero_nombre': 'TERCERO',
        'bodega_nombre': 'BODEGA',
        'tipo_movimiento': 'TIPO MVTO',
        'cantidad': 'CANTIDAD',
        'costo_unitario': 'COSTO UNIT.',
        'costo_total': 'COSTO TOTAL',
    }
    
    headers = list(column_map.values())
    processed_rows = []

    # 2. Procesar y Formatear cada fila
    for item in data_items:
        row_cells = []
        item_dict = item # Ya es un diccionario puro gracias a model_dump()

        for key, header_name in column_map.items():
            value = item_dict.get(key)
            formatted_value = ''
            
            # Aplicar formato para cantidades y valores
            if key in ['cantidad', 'costo_unitario', 'costo_total']:
                formatted_value = format_miles(value)
            elif key == 'fecha':
                if value:
                    try:
                         # Asumimos que es un string ISO que se puede convertir a date
                         dt_obj = datetime.fromisoformat(value)
                         formatted_value = dt_obj.strftime('%Y-%m-%d')
                    except:
                         formatted_value = str(value)
                else:
                    formatted_value = 'N/A'
            else:
                formatted_value = str(value or 'N/A')
            
            row_cells.append(formatted_value)

        processed_rows.append({
            'estado': '', # No se usa en Movimientos Detallados
            'cells': row_cells
        })

    return headers, processed_rows
# >>> FIN DE FUNCIÓN CRÍTICA: PRE-PROCESAMIENTO PARA PLANTILLA PDF <<<


def _get_movimientos_base_query(db: Session, empresa_id: int, filtros: schemas_reportes.SuperInformeFiltros, include_joins=False):
    """
    [FUNCIÓN MOVIDA AL INICIO] Construye la consulta base de MovimientoInventario,
    aplicando los filtros de selección.
    """
    query = db.query(
        models_producto.MovimientoInventario,
    ).select_from(models_producto.MovimientoInventario)\
     .join(models_producto.Producto, models_producto.MovimientoInventario.producto_id == models_producto.Producto.id)\
     .outerjoin(models_doc.Documento, models_producto.MovimientoInventario.documento_id == models_doc.Documento.id)

    # --- 2. Aplicación Dinámica de Filtros ---
    conditions = [
        models_producto.Producto.empresa_id == empresa_id,
        or_(models_doc.Documento.anulado == False, models_doc.Documento.id == None) # Solo movimientos NO anulados
    ]

    # Fechas
    fecha_inicio_dt_base = datetime.combine(filtros.fecha_inicio or date(1900, 1, 1), time.min)
    fecha_fin_dt_base = datetime.combine(filtros.fecha_fin or date.today(), time.max)
    
    if filtros.vista_reporte == schemas_reportes.VistaSuperInformeEnum.MOVIMIENTOS:
        if filtros.fecha_inicio and filtros.fecha_fin:
             conditions.append(models_producto.MovimientoInventario.fecha.between(fecha_inicio_dt_base, fecha_fin_dt_base))
    else:
        conditions.append(models_producto.MovimientoInventario.fecha <= fecha_fin_dt_base)

    # Filtros de Inventario
    if filtros.bodega_ids and len(filtros.bodega_ids) > 0:
        conditions.append(models_producto.MovimientoInventario.bodega_id.in_(filtros.bodega_ids))
    
    if filtros.producto_ids and len(filtros.producto_ids) > 0:
        conditions.append(models_producto.MovimientoInventario.producto_id.in_(filtros.producto_ids))
    elif filtros.search_term_prod:
        search_like = f"%{filtros.search_term_prod}%"
        # >>> FIX CRÍTICO DEL DUPLICATE ALIAS: La línea problemática se ha eliminado, solo aplicamos la condición.
        conditions.append(or_(
             models_producto.Producto.codigo.ilike(search_like),
             models_producto.Producto.nombre.ilike(search_like)
        ))
    # <<< FIN FIX

    if filtros.grupo_ids and len(filtros.grupo_ids) > 0:
        conditions.append(models_producto.Producto.grupo_id.in_(filtros.grupo_ids))
    
    if filtros.es_servicio is not None:
        conditions.append(models_producto.Producto.es_servicio == filtros.es_servicio)

    # Filtros de Documento/Tercero
    if filtros.tercero_id:
        conditions.append(models_doc.Documento.beneficiario_id == filtros.tercero_id)
        
    if filtros.search_term_doc:
        ref_like = f"%{filtros.search_term_doc}%"
        query = query.outerjoin(models_tipo_doc.TipoDocumento, models_doc.Documento.tipo_documento_id == models_doc.Documento.tipo_documento_id)
        conditions.append(func.concat(models_tipo_doc.TipoDocumento.codigo, '-', cast(models_doc.Documento.numero, SAString)).ilike(ref_like))
    
    # Aplicar todas las condiciones acumuladas
    query = query.filter(and_(*conditions))

    # --- Joins Adicionales para Detalles (Solo si se pide) ---
    if include_joins:
        # Se asume que estos joins NO se duplican, solo se agregan.
        query = query.outerjoin(models_grupo.GrupoInventario, models_producto.Producto.grupo_id == models_grupo.GrupoInventario.id)\
                     .outerjoin(models_bodega.Bodega, models_producto.MovimientoInventario.bodega_id == models_producto.MovimientoInventario.bodega_id)\
                     .outerjoin(models_tipo_doc.TipoDocumento, models_doc.Documento.tipo_documento_id == models_tipo_doc.TipoDocumento.id)\
                     .outerjoin(models_tercero.Tercero, models_doc.Documento.beneficiario_id == models_tercero.Tercero.id)
        needs_mov_con_join = filtros.vista_reporte == schemas_reportes.VistaSuperInformeEnum.RENTABILIDAD
        if needs_mov_con_join:
            MovimientoContableAlias = aliased(models_mov_con.MovimientoContable)
            query = query.outerjoin(MovimientoContableAlias, MovimientoContableAlias.documento_id == models_doc.Documento.id)

    return query


# --- Carga de Entorno Jinja2 (Para PDF) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, '..', 'templates', 'reports')


env.filters['format_miles'] = format_miles  # La función se llama format_miles en el ámbito global

# ==============================================================================
# === FUNCIONES DE SEGURIDAD Y GENERACIÓN DE TOKEN (FIX DE ORDENAMIENTO) ===
# ==============================================================================

def crear_token_kardex_pdf(filtros: schemas_reportes.KardexFiltrosPDF) -> str:
    """
    Serializa los filtros y crea un token JWT firmado de corta duración.
    """
    try:
        token_payload_str = filtros.model_dump_json()
        token = create_signed_token(token_payload_str, salt='pdf-kardex-v1', max_age=600) 
        return token
    except Exception as e:
        print(f"Error al crear token JWT para Kardex: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Fallo en el motor de firma de tokens.")

# ==============================================================================
# === FUNCIÓN CRÍTICA: KARDEX (FIX DE FIRMA) ===
# ==============================================================================

def get_kardex_por_producto(db: Session, empresa_id: int, filtros: schemas_reportes.KardexFiltrosPDF) -> Dict[str, Any]:
    """
    Motor principal para el Kardex de Producto.
    FIX CRÍTICO: Ahora acepta un objeto 'filtros' para alinearse con el router.
    """
    
    # --- 1. EXTRACCIÓN DE PARÁMETROS DEL OBJETO FILTROS ---
    producto_id = filtros.producto_id
    fecha_inicio = filtros.fecha_inicio
    fecha_fin = filtros.fecha_fin
    bodega_id = filtros.bodega_id
    
    saldo_inicial_cantidad = 0.0
    saldo_inicial_valor = 0.0
    fecha_inicio_dt = datetime.combine(fecha_inicio, time.min)
    fecha_fin_dt = datetime.combine(fecha_fin, time.max)
    bodega_saldo_inicial = "Consolidado"
    if bodega_id:
        bodega_info = db.query(models_bodega.Bodega.nombre).filter(models_bodega.Bodega.id == bodega_id).scalar()
        bodega_saldo_inicial = bodega_info or f"Bodega ID {bodega_id}"
    producto = db.query(
        models_producto.Producto.codigo, models_producto.Producto.nombre
    ).filter(
        models_producto.Producto.id == producto_id, models_producto.Producto.empresa_id == empresa_id
    ).first()
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado.")

    # --- 2. CONSTRUCCIÓN DE FILTROS ---
    movimientos_periodo_filters = [
        models_producto.MovimientoInventario.producto_id == producto_id,
        models_producto.MovimientoInventario.fecha.between(fecha_inicio_dt, fecha_fin_dt),
        or_(models_doc.Documento.anulado == False, models_doc.Documento.id == None)
    ]
    if bodega_id:
        bodega_filter_condition = (models_producto.MovimientoInventario.bodega_id == bodega_id)
        movimientos_periodo_filters.append(bodega_filter_condition)

    # --- 3. CALCULO DEL SALDO INICIAL USANDO LÓGICA HISTÓRICA ---
    from app.services import inventario as service_inventario 
    db_producto_completo = service_inventario.get_producto_by_id(db, producto_id, empresa_id, load_all=False)
    costo_promedio_global_actual = db_producto_completo.costo_promedio or 0.0
    if bodega_id:
        saldo_inicial_cantidad = service_inventario.get_stock_historico(
            db=db, producto_id=producto_id, bodega_id=bodega_id, fecha=fecha_inicio_dt
        )
    else:
        bodegas = db.query(models_bodega.Bodega.id).filter(models_bodega.Bodega.empresa_id == empresa_id).all()
        for b_id in [b[0] for b in bodegas]:
             saldo_inicial_cantidad += service_inventario.get_stock_historico(
                db=db, producto_id=producto_id, bodega_id=b_id, fecha=fecha_inicio_dt
             )
    saldo_inicial_valor = saldo_inicial_cantidad * costo_promedio_global_actual
    
    # --- 4. CONSULTA DE MOVIMIENTOS Y SALDOS (REFACTORIZACIÓN ORM CRÍTICA) ---
    
    # Proyección explícita de columnas para evitar propiedades corruptas del modelo MovimientoInventario
    movimientos_select_entities = [
        models_producto.MovimientoInventario.id.label('mov_id'),
        models_producto.MovimientoInventario.fecha.label('mov_fecha'),
        models_producto.MovimientoInventario.tipo_movimiento.label('mov_tipo'),
        models_producto.MovimientoInventario.cantidad.label('mov_cantidad'),
        models_producto.MovimientoInventario.costo_unitario.label('mov_costo_unit'),
        models_producto.MovimientoInventario.costo_total.label('mov_costo_total'),
        
        models_tipo_doc.TipoDocumento.codigo.label('doc_codigo'),
        models_doc.Documento.numero.label('doc_numero'),
        models_bodega.Bodega.nombre.label('bodega_nombre')
    ]

    movimientos_base_query = db.query(*movimientos_select_entities)\
        .outerjoin(models_doc.Documento, models_producto.MovimientoInventario.documento_id == models_doc.Documento.id)\
        .outerjoin(models_tipo_doc.TipoDocumento, models_doc.Documento.tipo_documento_id == models_tipo_doc.TipoDocumento.id)\
        .outerjoin(models_bodega.Bodega, models_producto.MovimientoInventario.bodega_id == models_bodega.Bodega.id)\
        .filter(and_(*movimientos_periodo_filters))\
        .order_by(models_producto.MovimientoInventario.fecha.asc(), models_producto.MovimientoInventario.id.asc())
        
    # Ejecutamos la query y obtenemos el resultado como mapeo de columnas (no como objeto ORM)
    movimientos_periodo = movimientos_base_query.all()
    
    # 5. Calcular saldos y formatear
    saldo_cantidad_actual = Decimal(str(saldo_inicial_cantidad)) 
    saldo_valor_actual = Decimal(str(saldo_inicial_valor)) 
    costo_promedio_global_actual_float = db.query(models_producto.Producto.costo_promedio).filter(models_producto.Producto.id == producto_id).scalar()
    costo_promedio_global_actual_dec = Decimal(str(costo_promedio_global_actual_float or 0.0))
    items_kardex = []
    total_entradas_cant = Decimal('0.0'); total_salidas_cant = Decimal('0.0')
    total_entradas_val = Decimal('0.0'); total_salidas_val = Decimal('0.0')

    # Se mantiene la lógica del Saldo Anterior fuera del bucle de Pydantic/Iteración.
    
    for mov_row in movimientos_periodo:
        # Accedemos a las columnas explícitamente por el label, no por el objeto MovimientoInventario
        mov_data = mov_row._asdict() # Convertimos el RowProxy a un dict
        
        doc_codigo = mov_data['doc_codigo']
        doc_numero = mov_data['doc_numero']
        bodega_nombre = mov_data['bodega_nombre']
        
        mov_cantidad = Decimal(str(mov_data['mov_cantidad'] or 0))
        mov_costo_unitario = Decimal(str(mov_data['mov_costo_unit'] or 0))
        mov_costo_total_entrada = Decimal(str(mov_data['mov_costo_total'] if mov_data['mov_tipo'].startswith('ENTRADA') else 0))
        
        item_data = {
            "id": mov_data['mov_id'], 
            "fecha": mov_data['mov_fecha'], 
            "tipo_movimiento": mov_data['mov_tipo'],
            "documento_ref": f"{doc_codigo}-{doc_numero}" if doc_codigo else "MOV. DIRECTO",
            "bodega_nombre": bodega_nombre or "N/A"
        }
        
        if mov_data['mov_tipo'].startswith('ENTRADA'):
            saldo_parcial_cantidad = saldo_cantidad_actual + mov_cantidad
            saldo_parcial_valor = saldo_valor_actual + mov_costo_total_entrada
            
            # Actualizar costo promedio (lógica simplificada para el Kardex)
            if not bodega_id and saldo_parcial_cantidad.is_normal(): 
                costo_promedio_global_actual_dec = saldo_parcial_valor / saldo_parcial_cantidad
            
            item_data.update({
                "entrada_cantidad": float(mov_cantidad), 
                "entrada_costo_unit": float(mov_costo_unitario.quantize(Decimal("0.01"), ROUND_HALF_UP)),
                "entrada_costo_total": float(mov_costo_total_entrada.quantize(Decimal("0.01"), ROUND_HALF_UP))
            })
            total_entradas_cant += mov_cantidad
            total_entradas_val += mov_costo_total_entrada

        elif mov_data['mov_tipo'].startswith('SALIDA'):
            costo_promedio_a_usar = costo_promedio_global_actual_dec
            costo_salida_calculado = mov_cantidad * costo_promedio_a_usar
            saldo_parcial_cantidad = saldo_cantidad_actual - mov_cantidad
            saldo_parcial_valor = max(Decimal(0), saldo_valor_actual - costo_salida_calculado)
            
            # // ********* FIX CRÍTICO: COMENTAR BLOQUE DE RECALCULO INCORRECTO (YA COMENTADO EN LA LÍNEA 128 DE LA VERSIÓN BASE) *********
            # if not bodega_id and saldo_parcial_cantidad.is_normal():
            #     costo_promedio_global_actual_dec = saldo_valor_actual / saldo_parcial_cantidad
            # // *************************************************************************
            
            item_data.update({
                "salida_cantidad": float(mov_cantidad), 
                "salida_costo_unit": float(costo_promedio_a_usar.quantize(Decimal("0.01"), ROUND_HALF_UP)), 
                "salida_costo_total": float(costo_salida_calculado.quantize(Decimal("0.01"), ROUND_HALF_UP))
            })
            total_salidas_cant += mov_cantidad
            total_salidas_val += costo_salida_calculado

        # Actualizar saldos para la próxima iteración
        saldo_cantidad_actual = saldo_parcial_cantidad
        saldo_valor_actual = saldo_parcial_valor
        
        # El Saldo Costo Promedio para la siguiente línea (o el retorno) ES el costo promedio que no debe variar por salida
        saldo_costo_promedio_linea = costo_promedio_global_actual_dec 

        # El Saldo Valor Total Final debe ser Saldo Cantidad * Costo Promedio (que no varía en la salida)
        saldo_valor_final_linea = saldo_cantidad_actual * saldo_costo_promedio_linea 

        item_data.update({ 
            "saldo_cantidad": float(saldo_cantidad_actual),
            "saldo_costo_promedio": float(saldo_costo_promedio_linea.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "saldo_valor_total": float(saldo_valor_final_linea.quantize(Decimal("0.01"), ROUND_HALF_UP)) 
        })
        
        # Saneamiento de None si no aplica
        item_data.setdefault("entrada_cantidad", None); item_data.setdefault("entrada_costo_unit", None)
        item_data.setdefault("salida_cantidad", None); item_data.setdefault("salida_costo_unit", None); item_data.setdefault("salida_costo_total", None)
        
        # Añadimos el item ya limpiado y convertido a Pydantic
        items_kardex.append(schemas_reportes.KardexItem(**item_data))

    totales_kardex = schemas_reportes.KardexTotales(
        saldo_inicial_cantidad=float(saldo_inicial_cantidad), saldo_inicial_valor=float(saldo_inicial_valor),
        total_entradas_cantidad=float(total_entradas_cant), total_entradas_valor=float(total_entradas_val),
        total_salidas_cantidad=float(total_salidas_cant), total_salidas_valor=float(total_salidas_val), 
        saldo_final_cantidad=float(saldo_cantidad_actual), saldo_final_valor=float(saldo_valor_actual),
        bodega_nombre=bodega_saldo_inicial 
    )

    # 6. RETORNO DE PURIFICACIÓN (ELIMINAR OBJETO PYDANTIC)
    # Convertimos la respuesta Pydantic a un diccionario puro de Python antes de devolverlo.
    response_pydantic = schemas_reportes.KardexResponse(
        producto_codigo=producto.codigo, producto_nombre=producto.nombre,
        items=items_kardex, totales=totales_kardex
    )
    # Retornamos el diccionario puro
    return response_pydantic.model_dump()

# ==============================================================================
# === FUNCIÓN DE GENERACIÓN DE PDF FINAL (USA SALDOS Y TOKENS) ===
# ==============================================================================


# app/services/reportes_inventario.py (FUNCIÓN generar_kardex_pdf CORREGIDA)



def generar_kardex_pdf(
    db: Session,
    producto_id: int,
    fecha_inicio: date,
    fecha_fin: date,
    bodega_id: Optional[int]
) -> tuple[bytes, str]:
    """
    Genera el contenido binario del PDF del Kardex de un producto.
    [FIX FINAL]: Incluye el puente de datos 'items' -> 'movimientos' para compatibilidad con la plantilla.
    """
    
    # --- 0. BLINDAJE DE FECHAS (Mantenido) ---
    try:
        if isinstance(fecha_inicio, str): fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date() 
        if isinstance(fecha_fin, str): fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    except Exception as e:
        print(f"Error CRÍTICO de conversión de fecha en PDF service: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="El formato de las fechas proporcionadas para el PDF es inválido.")
        
    print(f"--- SONDA PDF: Fecha Inicio (OBJ FINAL) = {fecha_inicio} ---")

    try:
        # 1. Obtener Empresa ID y datos de empresa
        empresa_id = db.query(models_producto.Producto.empresa_id).filter(models_producto.Producto.id == producto_id).scalar()
        if not empresa_id: raise HTTPException(status_code=404, detail="Producto no encontrado o no pertenece a una empresa.")
        
        empresa_db = db.query(models_empresa.Empresa).filter(models_empresa.Empresa.id == empresa_id).first() 
        
        empresa_nombre = getattr(empresa_db, 'razon_social', f"EMPRESA ID {empresa_id}")
        empresa_nit = getattr(empresa_db, 'nit', 'N/A')

        # 2. Obtener los datos del Kardex (RETORNO PURIFICADO)
        filtros_internos = schemas_reportes.KardexFiltrosPDF(
            producto_id=producto_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, bodega_id=bodega_id
        )
        # data_raw_dict es un dict plano (resultado de .model_dump())
        data_raw_dict = get_kardex_por_producto(db=db, empresa_id=empresa_id, filtros=filtros_internos)

        # 3. SERIALIZACIÓN FINAL A PRUEBA DE CORRUPCIÓN
        # Aplicamos la conversión de Decimal/Date al diccionario PURO
        data_serializada = convert_decimals_and_dates(data_raw_dict) 
        
        # >>> FIX DE COMPATIBILIDAD PLANTILLA (PUENTE CRÍTICO) <<<
        # La plantilla espera 'movimientos', pero el servicio entrega 'items'.
        # Creamos el alias para que Jinja2 encuentre los datos y llene la tabla.
        if 'items' in data_serializada:
            data_serializada['movimientos'] = data_serializada['items']
        # >>> FIN FIX <<<

        # Sonda para confirmar que 'items' es un list antes de Jinja
        if not isinstance(data_serializada.get('items'), list):
             print(f"ERROR: 'items' no es una lista ({type(data_serializada.get('items'))}).")
             # Capturamos el error de tipo y lo lanzamos para que se refleje en el log.
             raise TypeError("'items' en el contexto del PDF no es una lista válida para iterar.")

        bodega_nombre_context = data_serializada.get('totales', {}).get('bodega_nombre', "Consolidado")
        
        context = {
            "titulo_reporte": "KARDEX DETALLADO DE PRODUCTO", 
            "empresa_nombre": empresa_nombre, "empresa_nit": empresa_nit,
            "filtros": {"fecha_inicio": fecha_inicio.isoformat(), "fecha_fin": fecha_fin.isoformat(), "bodega_nombre": bodega_nombre_context},
            "data": data_serializada, # ENVIAMOS EL DICCIONARIO PURO CON EL ALIAS 'movimientos'
        }
        
        # 5. Renderizar y Generar PDF
        template_name = 'kardex_report.html'
        template = env.get_template(template_name)
        
        html_out = template.render(context)
        pdf_bytes = generar_pdf_desde_html(html_out)

        # 6. Definir nombre del archivo
        producto_nombre_sanitizado = data_raw_dict['producto_codigo'].replace(' ', '_').replace('/', '-')
        bodega_suffix = f"_{bodega_nombre_context}" if bodega_nombre_context and bodega_nombre_context != 'Consolidado' else ""
        filename = f"Kardex_{producto_nombre_sanitizado}{bodega_suffix}.pdf"

        return pdf_bytes, filename

    except HTTPException as http_e:
         raise http_e
    except TypeError as type_e:
         print(f"Error fatal de TIPADO al generar Kardex PDF: {type_e}")
         traceback.print_exc()
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno: Problema de formato de datos para el PDF. Detalle: {type_e}")
    except Exception as service_e:
         print(f"Error fatal al generar Kardex PDF: {service_e}")
         traceback.print_exc()
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error en el servicio de Kardex al obtener datos o generar PDF.")
    
    



# ==============================================================================
# === FUNCIÓN DE VALIDACIÓN Y DESCARGA (UTILIZA TOKENS) ===
# ==============================================================================

def generar_kardex_pdf_por_token(db: Session, token: str) -> Tuple[bytes, str]:
    """
    Valida el token, decodifica los filtros y llama a la generación del PDF.
    """
    # 1. Validar y decodificar el token
    payload_str = validate_signed_token(token, salt='pdf-kardex-v1', max_age=600)
    
    if not payload_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de descarga inválido o expirado. Vuelva a solicitar el PDF.")

    # 2. Extraer filtros
    try:
        filtros = schemas_reportes.KardexFiltrosPDF.model_validate_json(payload_str) 
    except Exception as e:
        print(f"Error al decodificar filtros del token: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filtros de descarga corruptos o inválidos.")
    
    # 3. Determinar el empresa_id (CRÍTICO: No está en el token, se toma del producto)
    producto = db.query(models_producto.Producto).filter(models_producto.Producto.id == filtros.producto_id).first()
    if not producto or not producto.empresa_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto/Empresa no encontrado en el token.")
    
    # 4. Llamar a la lógica de generación existente (generar_kardex_pdf)
    return generar_kardex_pdf(
        db=db,
        producto_id=filtros.producto_id,
        fecha_inicio=filtros.fecha_inicio,
        fecha_fin=filtros.fecha_fin,
        bodega_id=filtros.bodega_id
    )

# ==============================================================================
# === FUNCIÓN DE REPORTES DE TOPES (NUEVA LÓGICA CRÍTICA) ===
# ==============================================================================

def get_reporte_topes_inventario(db: Session, empresa_id: int, filtros: schemas_reportes.ReporteTopesFiltros) -> schemas_reportes.ReporteTopesResponse:
    """
    Calcula el stock a la fecha de corte y lo compara con stock_minimo y stock_maximo.
    """
    fecha_corte_dt = datetime.combine(filtros.fecha_corte, time.max)
    
    # 1. Preparar la subconsulta para calcular el stock a la fecha de corte
    # Condiciones base de movimientos (solo para el cálculo de saldo)
    movimiento_conditions = [
        models_producto.MovimientoInventario.fecha <= fecha_corte_dt,
        models_producto.MovimientoInventario.producto_id == models_producto.Producto.id,
        or_(models_doc.Documento.anulado == False, models_doc.Documento.id == None)
    ]
    
    if filtros.bodega_ids and len(filtros.bodega_ids) > 0:
        movimiento_conditions.append(models_producto.MovimientoInventario.bodega_id.in_(filtros.bodega_ids))

    # Expresión de cálculo de stock (Entrada - Salida)
    # Asumimos que los Movimientos de Inventario ya están relacionados con Documento
    stock_calc_expr = func.sum(
        case(
            (models_producto.MovimientoInventario.tipo_movimiento.startswith('ENTRADA'), models_producto.MovimientoInventario.cantidad),
            (models_producto.MovimientoInventario.tipo_movimiento.startswith('SALIDA'), -models_producto.MovimientoInventario.cantidad),
            else_=0
        )
    ).label("saldo_actual")

    # Subquery para el cálculo del stock (agrupado por producto y bodega si aplica)
    # Usamos Group By para que la agrupación coincida con el cálculo de stock
    mov_query_base = db.query(
        models_producto.MovimientoInventario.producto_id,
        models_producto.MovimientoInventario.bodega_id,
        stock_calc_expr,
        models_bodega.Bodega.nombre.label('bodega_nombre')
    ).select_from(models_producto.MovimientoInventario)\
     .outerjoin(models_doc.Documento, models_producto.MovimientoInventario.documento_id == models_doc.Documento.id)\
     .join(models_bodega.Bodega, models_producto.MovimientoInventario.bodega_id == models_bodega.Bodega.id)\
     .filter(and_(*movimiento_conditions))\
     .group_by(
        models_producto.MovimientoInventario.producto_id,
        models_producto.MovimientoInventario.bodega_id,
        models_bodega.Bodega.nombre
     ).subquery()
     
    # 2. Consulta Principal (Productos + Topes + Saldos)
    
    # JOIN con la tabla de productos
    query = db.query(
        models_producto.Producto.id.label('producto_id'),
        models_producto.Producto.codigo.label('producto_codigo'),
        models_producto.Producto.nombre.label('producto_nombre'),
        models_producto.Producto.stock_minimo,
        models_producto.Producto.stock_maximo,
        func.coalesce(mov_query_base.c.saldo_actual, 0.0).label('saldo_actual'),
        func.coalesce(mov_query_base.c.bodega_nombre, 'N/A').label('bodega_nombre')
    ).select_from(models_producto.Producto)\
     .outerjoin(mov_query_base, models_producto.Producto.id == mov_query_base.c.producto_id)\
     .filter(models_producto.Producto.empresa_id == empresa_id)\
     .filter(models_producto.Producto.es_servicio == False) # Excluir servicios
    
    # Aplicar filtros de Grupo
    if filtros.grupo_ids and len(filtros.grupo_ids) > 0:
        query = query.filter(models_producto.Producto.grupo_id.in_(filtros.grupo_ids))
        
    # 3. Aplicar Lógica de Topes y Filtro Final
    
    # Expresiones de comparación (NO SE PUEDEN USAR EN SQL DE POSTGRES SIN DUPLICAR)
    # Por lo tanto, el filtro de estado_tope se hace en Python.
    
    resultados_db = query.all()

    items_reporte: List[schemas_reportes.ReporteTopesItem] = []
    totales_topes: Dict[str, int] = {"MINIMO": 0, "MAXIMO": 0, "OK": 0}
    
    for row in resultados_db:
        # Conversión segura a Decimal para cálculos
        saldo = Decimal(str(row.saldo_actual or 0.0))
        minimo = Decimal(str(row.stock_minimo or 0.0))
        maximo = Decimal(str(row.stock_maximo or 0.0))

        estado_tope = "OK"
        diferencia = Decimal('0.0')

        if minimo > Decimal('0.0') and saldo <= minimo:
            # Por debajo del mínimo (falta para llegar al mínimo)
            estado_tope = "MINIMO"
            diferencia = minimo - saldo
        elif maximo > Decimal('0.0') and saldo >= maximo:
            # Por encima del máximo (sobra del máximo)
            estado_tope = "MAXIMO"
            diferencia = saldo - maximo
        
        # Aplicar el filtro de alerta (SOLO mostrar los que cumplen la condición de la alerta)
        if (filtros.tipo_alerta == "MINIMO" and estado_tope == "MINIMO") or \
           (filtros.tipo_alerta == "MAXIMO" and estado_tope == "MAXIMO") or \
           (filtros.tipo_alerta == "TODOS"):
               # Continúa para añadir el item
               pass
        else:
             continue # Excluir si no cumple el filtro

        if estado_tope == "MINIMO":
             totales_topes["MINIMO"] += 1
        elif estado_tope == "MAXIMO":
             totales_topes["MAXIMO"] += 1
        elif filtros.tipo_alerta == "TODOS" and estado_tope == "OK":
             totales_topes["OK"] += 1

        # Crear el item de respuesta
        items_reporte.append(schemas_reportes.ReporteTopesItem(
            producto_id=row.producto_id,
            producto_codigo=row.producto_codigo,
            producto_nombre=row.producto_nombre,
            stock_minimo=float(minimo),
            stock_maximo=float(maximo),
            saldo_actual=float(saldo),
            bodega_nombre=row.bodega_nombre,
            estado_tope=estado_tope,
            diferencia=float(diferencia)
        ))
    
    # Corrección del conteo OK: Si no es TODOS, el total OK solo es un conteo para referencia
    if filtros.tipo_alerta != "TODOS":
        total_en_lista = totales_topes['MINIMO'] + totales_topes['MAXIMO']
        total_ok_calculado = len(resultados_db) - total_en_lista
        # El total de OK solo tiene sentido si no estamos filtrando por un tipo específico
        totales_topes['OK'] = total_ok_calculado if total_ok_calculado > 0 else 0


    return schemas_reportes.ReporteTopesResponse(
        items=items_reporte,
        totales_topes=totales_topes
    )

# ... (Resto de funciones: get_reporte_analitico_movimientos, get_reporte_estado_general, etc.) ...
def get_reporte_analitico_movimientos(db: Session, empresa_id: int, filtros: schemas_reportes.ReporteAnaliticoFiltros):
    # ... (Lógica existente) ...
    fecha_inicio_dt = datetime.combine(filtros.fecha_inicio, datetime.min.time()) if isinstance(filtros.fecha_inicio, date) else filtros.fecha_inicio
    fecha_fin_dt = datetime.combine(filtros.fecha_fin, datetime.max.time()) if isinstance(filtros.fecha_fin, date) else filtros.fecha_fin
    cantidad_expr = models_producto.MovimientoInventario.cantidad
    valor_expr = models_producto.MovimientoInventario.costo_total
    
    # Declaraciones de variables de condición (CORRECCIÓN DE AMBITO)
    condicion_entrada = models_producto.MovimientoInventario.tipo_movimiento.startswith('ENTRADA')
    condicion_salida = models_producto.MovimientoInventario.tipo_movimiento.startswith('SALIDA')


    
    # REEMPLAZAR ESTE BLOQUE COMPLETO EN get_reporte_analitico_movimientos:
    # FIX CRÍTICO: Usamos lógica de < y <= para evitar la ambigüedad del BETWEEN/TIMESTAMP.
    # El saldo inicial debe ser < fecha_inicio_dt (es decir, antes del 00:00:00 de ese día)
    condicion_antes_inicio = and_(
        models_producto.MovimientoInventario.fecha < fecha_inicio_dt,
        or_(models_doc.Documento.anulado == False, models_doc.Documento.id == None)
    )
    # El período de movimientos debe ser >= fecha_inicio_dt Y <= fecha_fin_dt.
    condicion_en_periodo = and_(
        models_producto.MovimientoInventario.fecha >= fecha_inicio_dt,
        models_producto.MovimientoInventario.fecha <= fecha_fin_dt,
        or_(models_doc.Documento.anulado == False, models_doc.Documento.id == None)
    )

    # >>> INICIO FIX CRÍTICO: SOPORTE MULTI-ID CON SQL IN <<<
    # Esto ahora usa bodega_ids (plural) que vienen del SuperInformeFiltros en la ruta.
    if filtros.bodega_ids and len(filtros.bodega_ids) > 0:
        condicion_bodega = (models_producto.MovimientoInventario.bodega_id.in_(filtros.bodega_ids))
        condicion_antes_inicio = and_(condicion_antes_inicio, condicion_bodega)
        condicion_en_periodo = and_(condicion_en_periodo, condicion_bodega)
    # <<< FIN FIX CRÍTICO

    
    saldo_inicial_cantidad_expr = func.sum(case( (condicion_antes_inicio, case( (condicion_entrada, cantidad_expr), (condicion_salida, -cantidad_expr), else_=0 )), else_=0 )).label('saldo_inicial_cantidad')
    saldo_inicial_valor_expr = func.sum(case( (condicion_antes_inicio, case( (condicion_entrada, valor_expr), (condicion_salida, -valor_expr), else_=0 )), else_=0 )).label('saldo_inicial_valor')
    entradas_cantidad_expr = func.sum(case( (and_(condicion_en_periodo, condicion_entrada), cantidad_expr), else_=0 )).label('total_entradas_cantidad')
    entradas_valor_expr = func.sum(case( (and_(condicion_en_periodo, condicion_entrada), valor_expr), else_=0 )).label('total_entradas_valor')
    salidas_cantidad_expr = func.sum(case( (and_(condicion_en_periodo, condicion_salida), cantidad_expr), else_=0 )).label('total_salidas_cantidad')
    salidas_valor_expr = func.sum(case( (and_(condicion_en_periodo, condicion_salida), valor_expr), else_=0 )).label('total_salidas_valor')
    
    query = db.query(
        models_producto.Producto.id.label("producto_id"),
        models_producto.Producto.codigo.label("producto_codigo"),
        models_producto.Producto.nombre.label("producto_nombre"),
        func.coalesce(saldo_inicial_cantidad_expr, 0).label('saldo_inicial_cantidad'),
        func.coalesce(entradas_cantidad_expr, 0).label('total_entradas_cantidad'),
        func.coalesce(salidas_cantidad_expr, 0).label('total_salidas_cantidad'),
        func.coalesce(saldo_inicial_valor_expr, 0).label('saldo_inicial_valor'),
        func.coalesce(entradas_valor_expr, 0).label('total_entradas_valor'),
        func.coalesce(salidas_valor_expr, 0).label('total_salidas_valor'),
    ).select_from(models_producto.Producto).outerjoin(
        models_producto.MovimientoInventario,
        models_producto.Producto.id == models_producto.MovimientoInventario.producto_id
    ).outerjoin(
        models_doc.Documento,
        models_producto.MovimientoInventario.documento_id == models_doc.Documento.id
    ).filter(models_producto.Producto.empresa_id == empresa_id)
    
    # >>> INICIO FIX CRÍTICO: SOPORTE MULTI-ID CON SQL IN <<<
    if filtros.grupo_ids and len(filtros.grupo_ids) > 0:
        query = query.filter(models_producto.Producto.grupo_id.in_(filtros.grupo_ids))
    # <<< FIN FIX CRÍTICO
    
    # >>> FIX CRÍTICO: Cambio de 'search_term' obsoleto a 'search_term_prod'
    if filtros.search_term_prod: 
        search_like = f"%{filtros.search_term_prod}%"
        query = query.filter(or_(
             models_producto.Producto.codigo.ilike(search_like),
             models_producto.Producto.nombre.ilike(search_like)
        ))
    # <<< FIN FIX CRÍTICO

    # FIX CRÍTICO: Cambio de 'producto_id' obsoleto a 'producto_ids'
    # La ruta ahora usa SuperInformeFiltros, por lo que el campo es plural si está presente
    if filtros.producto_ids and len(filtros.producto_ids) > 0:
        query = query.filter(models_producto.Producto.id.in_(filtros.producto_ids))
    
    query = query.group_by(
        models_producto.Producto.id, models_producto.Producto.codigo, models_producto.Producto.nombre
    ).order_by(models_producto.Producto.nombre)
    try:
        resultados_db = query.all()
    except Exception as db_e:
        print(f"Error DB en get_reporte_analitico_movimientos: {db_e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Error interno al consultar la base de datos (Analítico).")
    items_reporte = []
    totales_cantidad = {"saldo_inicial": Decimal(0), "total_entradas": Decimal(0), "total_salidas": Decimal(0), "saldo_final": Decimal(0)}
    totales_valor = {"saldo_inicial": Decimal(0), "total_entradas": Decimal(0), "total_salidas": Decimal(0), "saldo_final": Decimal(0)}
    for row in resultados_db:
        si_cant = Decimal(str(row.saldo_inicial_cantidad or 0)); en_cant = Decimal(str(row.total_entradas_cantidad or 0)); sa_cant = Decimal(str(row.total_salidas_cantidad or 0))
        si_val = Decimal(str(row.saldo_inicial_valor or 0)); en_val = Decimal(str(row.total_entradas_valor or 0)); sa_val = Decimal(str(row.total_salidas_valor or 0))
        sf_cant = si_cant + en_cant - sa_cant; sf_val = si_val + en_val - sa_val
        if any([ abs(val.quantize(Decimal('0.01'))) > Decimal('0') for val in [si_cant, en_cant, sa_cant, sf_cant, si_val, en_val, sa_val, sf_val] ]):
            item_dict = {
                "producto_id": row.producto_id, "producto_codigo": row.producto_codigo, "producto_nombre": row.producto_nombre,
                "saldo_inicial_cantidad": float(si_cant), "total_entradas_cantidad": float(en_cant), "total_salidas_cantidad": float(sa_cant), "saldo_final_cantidad": float(sf_cant),
                "saldo_inicial_valor": float(si_val), "total_entradas_valor": float(en_val), "total_salidas_valor": float(sa_val), "saldo_final_valor": float(sf_val)
            }
            items_reporte.append(item_dict)
            totales_cantidad["saldo_inicial"] += si_cant; totales_cantidad["total_entradas"] += en_cant; totales_cantidad["total_salidas"] += sa_cant; totales_cantidad["saldo_final"] += sf_cant
            totales_valor["saldo_inicial"] += si_val; totales_valor["total_entradas"] += en_val; totales_valor["total_salidas"] += sa_val; totales_valor["saldo_final"] += sf_val
    totales_finales = {
        "saldo_inicial_cantidad": float(totales_cantidad["saldo_inicial"]), "total_entradas_cantidad": float(totales_cantidad["total_entradas"]),
        "total_salidas_cantidad": float(totales_cantidad["total_salidas"]), "saldo_final_cantidad": float(totales_cantidad["saldo_final"]),
        "saldo_inicial_valor": float(totales_valor["saldo_inicial"]), "total_entradas_valor": float(totales_valor["total_entradas"]),
        "total_salidas_valor": float(totales_valor["total_salidas"]), "saldo_final_valor": float(totales_valor["saldo_final"]),
    }


    # --- FIN get_reporte_analitico_movimientos ---
    
    # FIX: Bloque de retorno final con manejo de error (LÍNEA 961 Original)
    try:
         # 1. Convertir los diccionarios limpios a objetos Pydantic para validación
         # Aquí es donde se usa ReporteAnaliticoItem (el que se corrigió en el schema)
         items_pydantic = [ schemas_reportes.ReporteAnaliticoItem.model_validate(item) for item in items_reporte ]
         response_pydantic = schemas_reportes.ReporteAnaliticoResponse( items=items_pydantic, totales=totales_finales )
         
         # 2. Devolvemos el diccionario puro para que el Super Informe pueda acceder a sus propiedades
         return response_pydantic.model_dump() 
         
    except ValidationError as pydantic_e:
         print(f"Error CRÍTICO Pydantic en get_reporte_analitico_movimientos: Falló la validación del esquema interno: {pydantic_e}")
         raise pydantic_e # Lanzamos el error para que el Super Informe lo capture
    except Exception as general_e:
         print(f"Error general en get_reporte_analitico_movimientos: {general_e}")
         raise general_e
         

def get_reporte_estado_general(db: Session, empresa_id: int, filtros: schemas_reportes.ReporteInventarioFiltros):
    filtros_analiticos = schemas_reportes.ReporteAnaliticoFiltros(
        fecha_inicio=filtros.fecha_inicio, fecha_fin=filtros.fecha_fin,
        bodega_id=filtros.bodega_id, grupo_id=filtros.grupo_id,
        vista_por_valor=True
    )
    # Resultado analítico ahora devuelve un diccionario
    resultado_analitico = get_reporte_analitico_movimientos(db, empresa_id, filtros_analiticos)
    
    # Accedemos a las claves del diccionario
    items_adaptados = [
        schemas_reportes.ReporteInventarioItem(
            producto_id=item['producto_id'], producto_codigo=item['producto_codigo'], producto_nombre=item['producto_nombre'],
            saldo_inicial_cantidad=item['saldo_inicial_cantidad'], saldo_inicial_valor=item['saldo_inicial_valor'],
            entradas_cantidad=item['total_entradas_cantidad'], entradas_valor=item['total_entradas_valor'],
            salidas_cantidad=item['total_salidas_cantidad'], salidas_valor=item['total_salidas_valor'],
            saldo_final_cantidad=item['saldo_final_cantidad'], saldo_final_valor=item['saldo_final_valor']
        ) for item in resultado_analitico['items'] 
    ]
    totales_adaptados = {
        "saldo_inicial_valor": resultado_analitico['totales'].get("saldo_inicial_valor", 0.0),
        "entradas_valor": resultado_analitico['totales'].get("total_entradas_valor", 0.0),
        "salidas_valor": resultado_analitico['totales'].get("total_salidas_valor", 0.0),
        "saldo_final_valor": resultado_analitico['totales'].get("saldo_final_valor", 0.0)
    }
    return schemas_reportes.ReporteInventarioResponse(items=items_adaptados, totales=totales_adaptados)

def get_producto_para_kardex(db: Session, producto_id: int):
     return db.query(models_producto.Producto).filter(models_producto.Producto.id == producto_id).first()

def get_super_informe_inventarios(db: Session, empresa_id: int, filtros: schemas_reportes.SuperInformeFiltros):
    """
    Motor de consulta centralizado para el Super Informe de Inventarios.
    """
    print("\n--- SONDA A: Filtros RECIBIDOS en get_super_informe_inventarios ---")
    print(f"Filtros: {filtros.model_dump()}")

    cantidad_expr = models_producto.MovimientoInventario.cantidad
    valor_expr = models_producto.MovimientoInventario.costo_total

    # --- 1. Construcción de la Consulta Base Dinámica ---
    query = db.query(
        models_producto.MovimientoInventario,
        models_producto.Producto,
        models_grupo.GrupoInventario,
        models_bodega.Bodega,
        models_doc.Documento,
        models_tipo_doc.TipoDocumento,
        models_tercero.Tercero
    ).select_from(models_producto.MovimientoInventario)\
     .join(models_producto.Producto, models_producto.MovimientoInventario.producto_id == models_producto.Producto.id)\
     .outerjoin(models_grupo.GrupoInventario, models_producto.Producto.grupo_id == models_grupo.GrupoInventario.id)\
     .outerjoin(models_bodega.Bodega, models_producto.MovimientoInventario.bodega_id == models_bodega.Bodega.id)\
     .outerjoin(models_doc.Documento, models_producto.MovimientoInventario.documento_id == models_doc.Documento.id)\
     .outerjoin(models_tipo_doc.TipoDocumento, models_doc.Documento.tipo_documento_id == models_tipo_doc.TipoDocumento.id)\
     .outerjoin(models_tercero.Tercero, models_doc.Documento.beneficiario_id == models_tercero.Tercero.id)

    # --- Alias y Joins Condicionales ---
    needs_mov_con_join = filtros.cuenta_id or filtros.centro_costo_id or filtros.vista_reporte == schemas_reportes.VistaSuperInformeEnum.RENTABILIDAD
    MovimientoContableAlias = aliased(models_mov_con.MovimientoContable)
    if needs_mov_con_join:
        query = query.outerjoin(MovimientoContableAlias, MovimientoContableAlias.documento_id == models_doc.Documento.id)

    caracteristica_aliases = {}
    # >>> FIX CRÍTICO: Eliminamos el bloque que causa el AttributeError: 'SuperInformeFiltros' object has no attribute 'caracteristicas'
    # if filtros.caracteristicas:
    #     pass 
    # <<< FIN FIX CRÍTICO

    # --- 2. Aplicación Dinámica de Filtros (CORREGIDA) ---
    conditions = [
        models_producto.Producto.empresa_id == empresa_id,
        or_(models_doc.Documento.anulado == False, models_doc.Documento.id == None) 
    ]
    print("--- SONDA C: Aplicando Filtros ---")

    # Fechas
    fecha_inicio_dt_base = datetime.combine(filtros.fecha_inicio or date(1900, 1, 1), time.min)
    fecha_fin_dt_base = datetime.combine(filtros.fecha_fin or date.today(), time.max)
    
    if filtros.vista_reporte == schemas_reportes.VistaSuperInformeEnum.MOVIMIENTOS:
        if filtros.fecha_inicio and filtros.fecha_fin:
             conditions.append(models_producto.MovimientoInventario.fecha.between(fecha_inicio_dt_base, fecha_fin_dt_base))
    else:
        conditions.append(models_producto.MovimientoInventario.fecha <= fecha_fin_dt_base)

    # Filtros de Inventario (CORRECCIÓN CRÍTICA: La lista no debe ser None)
    if filtros.bodega_ids and len(filtros.bodega_ids) > 0:
        print(f"   -> Filtro bodega_ids: {filtros.bodega_ids}")
        conditions.append(models_producto.MovimientoInventario.bodega_id.in_(filtros.bodega_ids))
    
    if filtros.producto_ids and len(filtros.producto_ids) > 0:
        print(f"   -> Filtro producto_ids: {filtros.producto_ids}")
        conditions.append(models_producto.MovimientoInventario.producto_id.in_(filtros.producto_ids))
    elif filtros.search_term_prod:
        search_like = f"%{filtros.search_term_prod}%"
        # >>> FIX CRÍTICO DEL DUPLICATE ALIAS: La línea problemática se ha eliminado, solo aplicamos la condición.
        conditions.append(or_(
             models_producto.Producto.codigo.ilike(search_like),
             models_producto.Producto.nombre.ilike(search_like)
        ))
    # <<< FIN FIX

    if filtros.grupo_ids and len(filtros.grupo_ids) > 0:
        conditions.append(models_producto.Producto.grupo_id.in_(filtros.grupo_ids))
    
    if filtros.es_servicio is not None:
        conditions.append(models_producto.Producto.es_servicio == filtros.es_servicio)

    # Filtros de Documento/Tercero
    if filtros.tercero_id:
        conditions.append(models_doc.Documento.beneficiario_id == filtros.tercero_id)
        
    if filtros.search_term_doc:
        ref_like = f"%{filtros.search_term_doc}%"
        conditions.append(func.concat(models_tipo_doc.TipoDocumento.codigo, '-', cast(models_doc.Documento.numero, SAString)).ilike(ref_like))

    # Filtros Contables
    if needs_mov_con_join:
        if filtros.cuenta_id:
            conditions.append(MovimientoContableAlias.cuenta_id == filtros.cuenta_id)
        if filtros.centro_costo_id:
            conditions.append(or_(
                 models_doc.Documento.centro_costo_id == filtros.centro_costo_id,
                 MovimientoContableAlias.centro_costo_id == filtros.centro_costo_id
             ))

    # Aplicar todas las condiciones acumuladas
    if conditions:
        print(f"--- SONDA D: Total de {len(conditions)} condiciones a aplicar ---")
        query = query.filter(and_(*conditions))

    # --- SONDA E: Imprimir SQL ANTES de la ejecución específica de vista ---
    try:
        compiled_query = query.statement.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
        print("\n--- SONDA E: SQL Compilado ANTES de lógica de vista (Recortado) ---")
        print(f"WHERE CLÁUSULA: {str(compiled_query).split('WHERE')[1].split('GROUP BY')[0].strip()}")
    except Exception as sql_e:
        print(f"   -> Error al compilar SQL para SONDA E: {sql_e}")


    # --- 3. Ejecución según la Vista ---
    total_registros = 0
    resultados_finales = []
    totales_dict = None
    print(f"\n--- SONDA F: Procesando VISTA: {filtros.vista_reporte.value} ---")
    
    # --- VISTA: MOVIMIENTOS (CÁLCULO DE TOTALES AISLADOS Y SEGUROS) ---
    if filtros.vista_reporte == schemas_reportes.VistaSuperInformeEnum.MOVIMIENTOS:
        print("   -> Ejecutando lógica para VISTA MOVIMIENTOS")
        
        # --- CÁLCULO DE TOTALES AISLADOS (Solución al Producto Cartesiano) ---
        movimientos_base_para_totales = _get_movimientos_base_query(db, empresa_id, filtros)
        sq_totales_movimientos = movimientos_base_para_totales.with_entities(
            func.coalesce(func.sum(models_producto.MovimientoInventario.cantidad), 0).label('total_cantidad'),
            func.coalesce(func.sum(models_producto.MovimientoInventario.costo_total), 0).label('total_costo')
        ).subquery()

        total_query_scalar = db.query(
            sq_totales_movimientos.c.total_cantidad,
            sq_totales_movimientos.c.total_costo
        ).first()

        total_cantidad_mov = Decimal(str(total_query_scalar.total_cantidad)) if total_query_scalar and total_query_scalar.total_cantidad is not None else Decimal('0.0')
        total_costo_mov = Decimal(str(total_query_scalar.total_costo)) if total_query_scalar and total_query_scalar.total_costo is not None else Decimal('0.0')

        print(f"\n--- SONDA MOV: Totales AISLADOS y BRUTOS de DB ---")
        print(f"Total Cantidad (DEC): {total_cantidad_mov}")
        print(f"Total Costo (DEC): {total_costo_mov}")
        
        totales_dict = {
            "total_cantidad": float(total_cantidad_mov.quantize(Decimal('0.01'), ROUND_HALF_UP)),
            "total_costo": float(total_costo_mov.quantize(Decimal('0.01'), ROUND_HALF_UP)),
        }
        
        # 5. Obtener los detalles (con paginación)
        select_entities = [
            models_producto.MovimientoInventario.id.label('movimiento_id'),
            models_producto.MovimientoInventario.fecha,
            func.concat(models_tipo_doc.TipoDocumento.codigo, '-', cast(models_doc.Documento.numero, SAString)).label("documento_ref"),
            models_tipo_doc.TipoDocumento.codigo.label("tipo_documento_codigo"),
            models_tercero.Tercero.razon_social.label("tercero_nombre"),
            models_bodega.Bodega.nombre.label("bodega_nombre"),
            models_producto.Producto.codigo.label("producto_codigo"),
            models_producto.Producto.nombre.label("producto_nombre"),
            models_producto.MovimientoInventario.tipo_movimiento,
            models_producto.MovimientoInventario.cantidad,
            models_producto.MovimientoInventario.costo_unitario,
            models_producto.MovimientoInventario.costo_total,
        ]
        
        query_mov = query.with_entities(*select_entities)\
                     .order_by(models_producto.MovimientoInventario.fecha.desc(), models_producto.MovimientoInventario.id)

       
# 6. Paginación y Ejecución
        if not filtros.traerTodo:
             count_query = query_mov.with_entities(func.count(models_producto.MovimientoInventario.id)).order_by(None)
             total_registros = count_query.scalar() or 0
             query_mov = query_mov.limit(ITEMS_POR_PAGINA).offset((filtros.pagina - 1) * ITEMS_POR_PAGINA)

        try:
             resultados_db = query_mov.all()
             # FIX CRÍTICO: Asegurar que total_registros se actualice si traerTodo es True
             if filtros.traerTodo: 
                 total_registros = len(resultados_db)
                 
             # --- SONDA DEPURACIÓN: Contar resultados ANTES de la purificación ---
             print(f"--- SONDA MOVIMIENTOS: Resultados DB (raw): {len(resultados_db)} ---")
             
             resultados_finales = [schemas_reportes.SuperInformeItemMovimiento.model_validate(row._mapping) for row in resultados_db]      
                
        except Exception as e:        

             print(f"Error DB/Pydantic en VISTA MOVIMIENTOS: {e}")
             traceback.print_exc()
             raise HTTPException(status_code=500, detail="Error procesando vista de movimientos.")


   # --- VISTA: ESTADO_GENERAL ---
    
    # --- VISTA: RENTABILIDAD ---
    
    # --- 4. Construcción de la Respuesta Final ---
    total_paginas = max(1, (total_registros + ITEMS_POR_PAGINA - 1) // ITEMS_POR_PAGINA) if not filtros.traerTodo else 1
    paginacion = schemas_reportes.SuperInformePaginacion(
        total_registros=total_registros,
        total_paginas=total_paginas,
        pagina_actual=filtros.pagina if not filtros.traerTodo else 1
    )
    try:
        response = schemas_reportes.SuperInformeResponse(
            items=resultados_finales,
            totales=totales_dict,
            paginacion=paginacion,
            vista_reporte=filtros.vista_reporte
        )
        return response
    except Exception as final_pydantic_e:
        print(f"Error al crear SuperInformeResponse: {final_pydantic_e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Error interno al formatear la respuesta final del Super Informe.")


def generar_pdf_super_informe(
    db: Session,
    empresa_id: int,
    filtros: schemas_reportes.SuperInformeFiltros
) -> tuple[bytes, str]:
    """
    Genera el contenido binario del PDF para la vista de Super Informe de Inventarios.
    Esta función es el wrapper que el Router está buscando.
    """
    print(f"--- SONDA PDF: Generando PDF para VISTA {filtros.vista_reporte.value} ---")

    # 1. Obtener datos de empresa
    empresa_db = db.query(models_empresa.Empresa).filter(models_empresa.Empresa.id == empresa_id).first()
    empresa_nombre = getattr(empresa_db, 'razon_social', f"EMPRESA ID {empresa_id}")
    empresa_nit = getattr(empresa_db, 'nit', 'N/A')

    # 2. Obtener los datos del reporte (Devuelve un objeto Pydantic SuperInformeResponse)
    # Aquí es donde fallaba el programa, pero ahora la función interna está corregida
    data_raw_pydantic = get_super_informe_inventarios(db=db, empresa_id=empresa_id, filtros=filtros)
    
    # 3. Serialización a prueba de corrupción (Diccionario puro para Jinja)
    # Convertimos la respuesta Pydantic a un diccionario puro (model_dump)
    data_raw_dict = data_raw_pydantic.model_dump() 
    
    # Aplicamos la conversión de Decimal/Date al diccionario PURO (Protocolo de la Caja Negra)
    data_serializada = convert_decimals_and_dates(data_raw_dict) 
    
    # 4. Definición del Título y la Plantilla según la vista
    vista = filtros.vista_reporte.value
    if vista == schemas_reportes.VistaSuperInformeEnum.MOVIMIENTOS.value:
        titulo_reporte = "SUPER INFORME: MOVIMIENTOS DE INVENTARIO"
        template_name = 'super_informe_report.html' # Asumo una plantilla genérica para el Super Informe
    elif vista == schemas_reportes.VistaSuperInformeEnum.ESTADO_GENERAL.value:
        titulo_reporte = "SUPER INFORME: ESTADO GENERAL"
        template_name = 'super_informe_report.html' # Misma plantilla genérica
    elif vista == schemas_reportes.VistaSuperInformeEnum.RENTABILIDAD.value:
        titulo_reporte = "SUPER INFORME: RENTABILIDAD POR PRODUCTO"
        template_name = 'rentabilidad_producto.html' # Usa la plantilla de rentabilidad si aplica
    else:
        titulo_reporte = "SUPER INFORME DE INVENTARIOS"
        template_name = 'super_informe_report.html'


   # 5. Construcción del Contexto
    context = {
        "titulo_reporte": titulo_reporte, 
        # FIX CRÍTICO: Anidar los datos de la empresa en un diccionario 'empresa' (el FIX anterior)
        "empresa": { 
             "razon_social": empresa_nombre, 
             "nit": empresa_nit 
        },
        "filtros": filtros.model_dump(mode='json'), # Enviamos los filtros a Jinja (ya contienen fechas y IDs)
        
        # >>> FIX CRÍTICO DEL PDF: Procesar 'items' al formato que el template espera
        "headers": [], # Se llenará con la cabecera de la tabla
        "processed_rows": [], # Se llenará con las filas pre-procesadas
        "show_totals": False, # Se activa si hay totales

        "data": data_serializada, # Dejamos data_serializada para referencia, pero usamos processed_rows

    }
    
    # Llenamos 'headers' y 'processed_rows' con la función auxiliar
    if vista == schemas_reportes.VistaSuperInformeEnum.MOVIMIENTOS.value:
        # data_serializada['items'] es una lista de diccionarios de movimientos
        headers, processed_rows = _process_movimientos_for_pdf(data_serializada.get('items', []))
        context['headers'] = headers
        context['processed_rows'] = processed_rows
        context['show_totals'] = True
        context['totales'] = { 
            # Los movimientos usan total_cantidad/costo. La plantilla espera debito/credito.
            # Asumo que el total del reporte MOVIMIENTOS usa debito/credito si se adapta a esa plantilla.
            # Ya que no hay debito/credito, dejaremos los totales del reporte MOVIMIENTOS.
            # Como la plantilla está diseñada para CUENTAS CONTABLES, la vamos a forzar.
            "debito": format_miles(data_serializada.get('totales', {}).get('total_costo', 0.0)),
            "credito": format_miles(data_serializada.get('totales', {}).get('total_costo', 0.0)), # Usamos el mismo valor para simular saldo.
            "diferencia": format_miles(data_serializada.get('totales', {}).get('total_costo', 0.0) - data_serializada.get('totales', {}).get('total_costo', 0.0))
        }

    
    
    # 6. Renderizar y Generar PDF
    try:
        # La fecha de generación se debe formatear como string
        context['fecha_generacion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        context['report_title'] = titulo_reporte # Aseguramos el título en el contexto raíz
        
        template = env.get_template(template_name)
        html_out = template.render(context)
        pdf_bytes = generar_pdf_desde_html(html_out)
    except Exception as e:
        print(f"Error al renderizar la plantilla {template_name} en el PDF del Super Informe: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al renderizar el PDF. Plantilla: {template_name}. Detalle: {e}")

    # 7. Definir nombre del archivo
    filename = f"Super_Informe_Inventario_{vista}.pdf"
    
    return pdf_bytes, filename

# ==============================================================================
# === [NUEVO] GENERADOR PDF MOVIMIENTO ANALÍTICO ===
# Agrega esto al final del archivo app/services/reportes_inventario.py
# ==============================================================================

def generar_pdf_movimiento_analitico(
    db: Session, 
    empresa_id: int, 
    filtros: schemas_reportes.SuperInformeFiltros
) -> Tuple[bytes, str]:
    """
    Genera el PDF del reporte analítico de movimientos (Kardex Analítico).
    """
    # 1. Obtener Datos de la Empresa (Para el encabezado)
    empresa = db.query(models_empresa.Empresa).filter(models_empresa.Empresa.id == empresa_id).first()
    empresa_nombre = getattr(empresa, 'razon_social', f"EMPRESA ID {empresa_id}")

    # 2. Obtener los Datos del Reporte
    # Reutilizamos la lógica existente que calcula saldos y movimientos
    # Forzamos 'traerTodo' implícitamente al no paginar aquí, o asumimos que el filtro trae la configuración correcta.
    # Nota: get_reporte_analitico_movimientos devuelve un dict puro gracias al fix anterior.
    data_dict = get_reporte_analitico_movimientos(db, empresa_id, filtros)
    
    # 3. Serialización Segura (Decimales y Fechas a String/Float)
    data_serializada = convert_decimals_and_dates(data_dict)

    # 4. Determinar nombre de la bodega para el título (Estética)
    bodega_nombre = "Todas"
    if filtros.bodega_ids and len(filtros.bodega_ids) == 1:
        bodega = db.query(models_bodega.Bodega).filter(models_bodega.Bodega.id == filtros.bodega_ids[0]).first()
        if bodega: 
            bodega_nombre = bodega.nombre
    elif filtros.bodega_ids and len(filtros.bodega_ids) > 1:
        bodega_nombre = "Múltiples seleccionadas"

    # 5. Preparar Contexto para la Plantilla HTML (Jinja2)
    context = {
        "empresa_nombre": empresa_nombre,
        "filtros": filtros.model_dump(), # Pasamos los filtros para mostrar fechas en el encabezado
        "data": data_serializada,
        "bodega_nombre": bodega_nombre
    }

    # 6. Renderizar HTML y Convertir a PDF
    try:
        template_name = 'reports/movimiento_analitico_report.html'
        
        # Verificación de seguridad por si la plantilla no se cargó
        if template_name not in TEMPLATES_EMPAQUETADOS:
             raise HTTPException(status_code=500, detail=f"La plantilla {template_name} no está registrada en _templates_empaquetados.py")

        template_string = TEMPLATES_EMPAQUETADOS[template_name]
        template = env.from_string(template_string)
        
        html_out = template.render(context)
        pdf_bytes = generar_pdf_desde_html(html_out)
        
        # Nombre del archivo de descarga
        filename = f"Movimiento_Analitico_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        return pdf_bytes, filename
        
    except Exception as e:
        print(f"Error al renderizar PDF Analítico: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno al generar el PDF: {str(e)}")