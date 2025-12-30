# app/services/reportes_facturacion.py (VERSIÓN CON FIX DE AttributeError)
# [AÑADIDA FUNCIÓN]: Se agrega 'generar_pdf_rentabilidad_producto' para que el Router no falle con 500.

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case, and_, select, literal_column, or_, cast, String as SAString, desc
from typing import List, Dict, Optional
from fastapi import HTTPException, status
import json
from decimal import Decimal, ROUND_HALF_UP
import io
from datetime import date, datetime
import traceback


# WeasyPrint y Jinja
from weasyprint import HTML
from ..services._templates_empaquetados import TEMPLATES_EMPAQUETADOS
from jinja2 import Environment, select_autoescape
from datetime import datetime

# 1. Inicializamos el entorno
GLOBAL_JINJA_ENV = Environment(loader=None, autoescape=select_autoescape(['html', 'xml']))

# --- DEFINICIÓN DE HERRAMIENTAS (FILTROS) ---

# A. Filtro de Fecha
def date_format(value, format="%d/%m/%Y"):
    if value is None: return ""
    try:
        return value.strftime(format)
    except AttributeError:
        try:
            return datetime.strptime(str(value)[:10], "%Y-%m-%d").strftime(format)
        except:
            return str(value)

# B. Filtro de Decimales (CORREGIDO: Respeta la precisión dinámica)
def format_decimal_filter(value, precision=2):
    try:
        val = float(value)
        # Usamos la variable 'precision' para el formato
        return f"{val:,.{precision}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0"
    
# C. Filtro de Moneda (CORREGIDO: Ahora sí respeta la precisión dinámica)
def format_currency_filter(value, precision=2):
    try:
        val = float(value)
        # Usamos la variable 'precision' dentro del formato f-string
        formatted = f"{val:,.{precision}f}".replace(",", "X").replace(".", ",").replace("X", ".")

        return f"${formatted}"
    
    except (ValueError, TypeError):
        return "$ 0" # Sin decimales por defecto en error
    
# --- REGISTRO DE HERRAMIENTAS ---
GLOBAL_JINJA_ENV.filters['date'] = date_format
GLOBAL_JINJA_ENV.filters['format_decimal'] = format_decimal_filter
GLOBAL_JINJA_ENV.filters['format_currency'] = format_currency_filter

# --- INYECCIÓN DE VARIABLES GLOBALES ---
GLOBAL_JINJA_ENV.globals['now'] = datetime.now


from ..models.empresa import Empresa as models_empresa

# Seguridad
from ..core.security import create_signed_token, validate_signed_token, create_pdf_jwt
from ..core.config import settings

# Modelos
from ..models import documento as models_doc
from ..models import producto as models_prod
from ..models import movimiento_contable as models_mov_con
from ..models import tercero as models_tercero
from ..models import grupo_inventario as models_grupo
from ..models import tipo_documento as models_tipo_doc
from ..models import bodega as models_bodega 
from ..models import plan_cuenta as models_plan_cuenta 
from ..models import lista_precio as models_lista_precio 

# Schemas
from ..schemas import reportes_facturacion as schemas_reportes
from ..schemas import reporte_rentabilidad as schemas_rentabilidad 


# =================================================================================
# === FUNCIONES AUXILIARES DE BI (TRAZABILIDAD COMPLETA) ===
# =================================================================================

def _get_trazabilidad_documentos(db: Session, producto_id: int, fecha_inicio: date, fecha_fin: date, tercero_ids: Optional[List[int]]) -> List[schemas_rentabilidad.TopDocumentoTrazabilidad]:
    """
    Función auxiliar para obtener TODOS los documentos (sin límite) para un producto.
    [FIX CRÍTICO: Aplica el filtro de tercero_ids para amarrar la trazabilidad al cliente.]
    """
    # 1. Subconsulta base de Movimientos de Inventario (Costo)
    # Se suman todos los costos de salida del producto por documento.
    sq_mov_costo = (
        select(
            models_prod.MovimientoInventario.documento_id,
            func.sum(models_prod.MovimientoInventario.costo_total).label("costo_total")
        )
        .filter(
            models_prod.MovimientoInventario.producto_id == producto_id,
            models_prod.MovimientoInventario.tipo_movimiento == 'SALIDA_VENTA'
        )
        .group_by(models_prod.MovimientoInventario.documento_id)
        .subquery()
    )

    # 2. Subconsulta base de Movimientos Contables (Venta)
    # Se suman todos los créditos de la cuenta de ingreso asociados al producto y documento.
    sq_mov_venta = (
        select(
            models_mov_con.MovimientoContable.documento_id,
            func.sum(models_mov_con.MovimientoContable.credito).label("venta_total")
        )
        .join(models_prod.Producto, models_mov_con.MovimientoContable.producto_id == models_prod.Producto.id)
        .join(models_grupo.GrupoInventario, models_prod.Producto.grupo_id == models_grupo.GrupoInventario.id)
        .filter(
            models_mov_con.MovimientoContable.producto_id == producto_id,
            models_mov_con.MovimientoContable.cuenta_id == models_grupo.GrupoInventario.cuenta_ingreso_id
        )
        .group_by(models_mov_con.MovimientoContable.documento_id)
        .subquery()
    )


    # 3. Consulta principal que une Documentos con Costo y Venta
    query = (
        select(
            models_doc.Documento.id.label("documento_id"),
            models_doc.Documento.fecha.label("fecha"),
            func.concat(models_tipo_doc.TipoDocumento.codigo, '-', cast(models_doc.Documento.numero, SAString)).label("documento_ref"),
            func.coalesce(sq_mov_venta.c.venta_total, Decimal('0.0')).label("venta_total_raw"), 
            func.coalesce(sq_mov_costo.c.costo_total, Decimal('0.0')).label("costo_total_raw"), 
            (func.coalesce(sq_mov_venta.c.venta_total, Decimal('0.0')) - func.coalesce(sq_mov_costo.c.costo_total, Decimal('0.0'))).label("utilidad_bruta_valor")
        )
        .join(models_tipo_doc.TipoDocumento, models_doc.Documento.tipo_documento_id == models_tipo_doc.TipoDocumento.id)
        .outerjoin(sq_mov_costo, models_doc.Documento.id == sq_mov_costo.c.documento_id)
        .outerjoin(sq_mov_venta, models_doc.Documento.id == sq_mov_venta.c.documento_id)
        .filter(
            models_doc.Documento.fecha.between(fecha_inicio, fecha_fin),
            models_doc.Documento.anulado == False,
            or_(sq_mov_costo.c.costo_total.isnot(None), sq_mov_venta.c.venta_total.isnot(None))
        )
    )
    
    # --- FIX CRÍTICO: FILTRAR POR TERCERO (CLIENTE) EN LA TRAZABILIDAD ---
    if tercero_ids:
        print(f"--- SONDA BI: Aplicando filtro de Tercero(s) a la Trazabilidad ({len(tercero_ids)} IDs).")
        query = query.filter(models_doc.Documento.beneficiario_id.in_(tercero_ids))
    # --- FIN FIX CRÍTICO ---

    query = query.order_by(desc(literal_column("utilidad_bruta_valor")))
    # [FIX CRÍTICO]: Se elimina la línea .limit(5) para mostrar TODOS los documentos.
    
    resultados = db.execute(query).all()

    print("\n--- SONDA CONTABLE (TRAZABILIDAD COMPLETA): AUDITORÍA DE MAGNITUD ---")
    
    documentos_trazabilidad = []
    for row in resultados:
        utilidad_calculada = Decimal(str(row.venta_total_raw)) - Decimal(str(row.costo_total_raw))
        
        # Sonda agregada para revelar los valores crudos y la utilidad calculada
        print(f"  > Doc: {row.documento_ref}, Venta: {row.venta_total_raw}, Costo: {row.costo_total_raw}, Utilidad Sonda: {utilidad_calculada}")
        
        documentos_trazabilidad.append(
            schemas_rentabilidad.TopDocumentoTrazabilidad(
                documento_id=row.documento_id,
                documento_ref=row.documento_ref,
                fecha=row.fecha,
                # Usamos la utilidad calculada por la consulta SQL (row.utilidad_bruta_valor)
                utilidad_bruta_valor=Decimal(str(row.utilidad_bruta_valor or '0.0')) 
            )
        )
    print(f"--- FIN SONDA CONTABLE: {len(documentos_trazabilidad)} Documentos Encontrados (Sin Límite) ---")
    
    return documentos_trazabilidad

# [CORRECCIÓN]: Renombramos la función original para que apunte a la nueva lógica.
# Hacemos esto para mantener el código base limpio. 
_get_top_5_documentos_original = _get_trazabilidad_documentos # Renombramos la función Top 5 original al cuerpo de la nueva trazabilidad completa.


# =================================================================================
# === NUEVA FUNCIÓN: GENERADOR DE PDF PARA EL REPORTE PRINCIPAL ===
# =================================================================================

def generar_pdf_rentabilidad_producto(db: Session, empresa_id: int, filtros: schemas_rentabilidad.RentabilidadProductoFiltros):
    """
    [FIX ATÓMICO]: Función que el router estaba buscando. Llama a get_rentabilidad_por_grupo 
    y genera el PDF del reporte principal (por producto/grupo).
    """
    # 1. Obtener los datos usando la lógica de BI
    report_data = get_rentabilidad_por_grupo(db=db, empresa_id=empresa_id, filtros=filtros) 
    
    if not report_data or not report_data.items:
        html_string = "<html><body><h1>Rentabilidad por Producto</h1><p>No se encontraron datos para los filtros seleccionados.</p></body></html>"
        return HTML(string=html_string).write_pdf()

    # 2. Obtener la empresa para el encabezado del PDF
    empresa = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    if not empresa: raise HTTPException(status_code=404, detail="Empresa no encontrada.")

    # 3. Preparar el contexto para la plantilla Jinja
    filtros_serializables = {
        "fecha_inicio": filtros.fecha_inicio.isoformat(),
        "fecha_fin": filtros.fecha_fin.isoformat(),
        "grupos": [g for g in filtros.grupo_ids],
        "productos": [p for p in filtros.producto_ids],
        "terceros": [t for t in filtros.tercero_ids],
        "margen_minimo": filtros.margen_minimo_porcentaje,
        "solo_perdidas": filtros.mostrar_solo_perdidas,
    }

    context = {
        "empresa": empresa,
        "filtros": filtros_serializables,
        "data": report_data,
        "titulo_reporte": "Análisis de Rentabilidad por Producto/Grupo"
    }

    try:
        # [CRÍTICO]: Asegúrate de tener esta plantilla. Usaremos la misma del documento por ahora.
        template_name = 'reports/rentabilidad_producto_grupo_report.html' 
        
        # --- Lógica de Fallback (Mantenida) ---
        if template_name not in TEMPLATES_EMPAQUETADOS:
             template_name_fallback = 'reports/rentabilidad_documento_report.html'
             print(f"WARN: Plantilla '{template_name}' no encontrada. Usando fallback '{template_name_fallback}'.")
             if template_name_fallback not in TEMPLATES_EMPAQUETADOS:
                  raise KeyError(f"Plantilla principal '{template_name}' ni fallback '{template_name_fallback}' encontradas.")
             template_name = template_name_fallback
        # --- Fin Lógica de Fallback ---

        template_string = TEMPLATES_EMPAQUETADOS[template_name]
        template = GLOBAL_JINJA_ENV.from_string(template_string)
        rendered_html = template.render(context)
        return HTML(string=rendered_html).write_pdf()

    except Exception as e:
        print(f"ERROR FATAL generando PDF rentabilidad producto: {e}"); traceback.print_exc()
        error_detail = f"Error al generar el PDF: {str(e)}"
        raise HTTPException(status_code=500, detail=error_detail)


# =================================================================================
# === RESTAURADA FUNCIÓN: RETORNA DATOS JSON DEL REPORTE DETALLADO (No Rentabilidad) ===
# =================================================================================
def get_reporte_facturacion_data(db: Session, empresa_id: int, filtros: schemas_reportes.ReporteFacturacionFiltros) -> schemas_reportes.ReporteFacturacionResponse:
    """Función para el reporte detallado de ventas/compras."""
    # 1. Construcción de la consulta SQL
    query_items = (
        db.query(
            models_doc.Documento.id.label("documento_id"),
            models_doc.Documento.fecha,
            func.concat(models_tipo_doc.TipoDocumento.codigo, '-', cast(models_doc.Documento.numero, SAString)).label("documento_ref"),
            models_tercero.Tercero.razon_social.label("tercero_nombre"),
            models_prod.Producto.codigo.label("producto_codigo"),
            models_prod.Producto.nombre.label("producto_nombre"),
            models_prod.MovimientoInventario.cantidad,
            models_prod.MovimientoInventario.costo_unitario,
            func.sum(case(
                (models_mov_con.MovimientoContable.cuenta_id == models_grupo.GrupoInventario.cuenta_ingreso_id, models_mov_con.MovimientoContable.credito),
                else_=Decimal('0.0')
            )).label("valor_venta_linea")
        )
        .join(models_doc.Documento, models_doc.Documento.id == models_prod.MovimientoInventario.documento_id)
        .join(models_tipo_doc.TipoDocumento, models_doc.Documento.tipo_documento_id == models_tipo_doc.TipoDocumento.id)
        .join(models_prod.Producto, models_prod.MovimientoInventario.producto_id == models_prod.Producto.id)
        .join(models_tercero.Tercero, models_doc.Documento.beneficiario_id == models_tercero.Tercero.id)
        .join(models_grupo.GrupoInventario, models_prod.Producto.grupo_id == models_grupo.GrupoInventario.id)
        .outerjoin(models_mov_con.MovimientoContable, and_(
            models_mov_con.MovimientoContable.documento_id == models_doc.Documento.id,
            models_mov_con.MovimientoContable.producto_id == models_prod.Producto.id
        ))
        .filter(models_doc.Documento.empresa_id == empresa_id)
        .filter(models_doc.Documento.fecha.between(filtros.fecha_inicio, filtros.fecha_fin))
        .filter(models_doc.Documento.anulado == False)
    )

    if filtros.tipo_reporte == 'ventas':
        query_items = query_items.filter(models_prod.MovimientoInventario.tipo_movimiento == 'SALIDA_VENTA')
    elif filtros.tipo_reporte == 'compras':
        query_items = query_items.filter(models_prod.MovimientoInventario.tipo_movimiento == 'ENTRADA_COMPRA')

    if filtros.tercero_id:
        query_items = query_items.filter(models_doc.Documento.beneficiario_id == filtros.tercero_id)
    if filtros.centro_costo_id:
        query_items = query_items.filter(models_doc.Documento.centro_costo_id == filtros.centro_costo_id)

    query_items = query_items.group_by(
        models_doc.Documento.id,
        models_doc.Documento.fecha,
        literal_column("documento_ref"),
        literal_column("tercero_nombre"),
        literal_column("producto_codigo"),
        literal_column("producto_nombre"),
        models_prod.MovimientoInventario.cantidad,
        models_prod.MovimientoInventario.costo_unitario
    ).order_by(models_doc.Documento.fecha.desc(), literal_column("documento_ref"))

    resultados_items = query_items.all()

    # 2. Post-procesamiento y cálculo de KPIs
    items_finales = []
    documentos_procesados = set()
    total_valor = Decimal('0.0')
    total_costo = Decimal('0.0')

    for item in resultados_items:
        documentos_procesados.add(item.documento_id)
        cantidad = Decimal(str(item.cantidad or '0.0'))
        costo_unitario = Decimal(str(item.costo_unitario or '0.0'))
        costo_total_linea = cantidad * costo_unitario

        if filtros.tipo_reporte == 'ventas':
            valor_total_linea = Decimal(str(item.valor_venta_linea or '0.0'))
            valor_unitario = valor_total_linea / cantidad if cantidad != Decimal('0.0') else Decimal('0.0')
            utilidad_bruta_valor = valor_total_linea - costo_total_linea
            utilidad_bruta_porcentaje = (utilidad_bruta_valor / valor_total_linea) * Decimal('100.0') if valor_total_linea != Decimal('0.0') else Decimal('0.0')
            total_valor += valor_total_linea
            total_costo += costo_total_linea
        else: # Compras
            valor_total_linea = costo_total_linea
            valor_unitario = costo_unitario
            utilidad_bruta_valor = None
            utilidad_bruta_porcentaje = None
            total_valor += valor_total_linea

        items_finales.append(schemas_reportes.ReporteFacturacionItem(
            documento_id=item.documento_id,
            fecha=item.fecha,
            documento_ref=item.documento_ref,
            tercero_nombre=item.tercero_nombre,
            producto_codigo=item.producto_codigo,
            producto_nombre=item.producto_nombre,
            cantidad=float(cantidad),
            valor_unitario=float(valor_unitario),
            valor_total_linea=float(valor_total_linea),
            costo_unitario=float(costo_unitario),
            costo_total_linea=float(costo_total_linea),
            utilidad_bruta_valor=float(utilidad_bruta_valor) if utilidad_bruta_valor is not None else None,
            utilidad_bruta_porcentaje=float(utilidad_bruta_porcentaje) if utilidad_bruta_porcentaje is not None else None,
        ))

    # 3. Cálculo de KPIs y retorno
    numero_facturas = len(documentos_procesados)
    promedio_por_factura = total_valor / Decimal(str(numero_facturas or '1'))
    utilidad_bruta_valor_total = total_valor - total_costo
    margen_general = (utilidad_bruta_valor_total / total_valor) * Decimal('100.0') if total_valor != Decimal('0.0') else Decimal('0.0')

    kpis = schemas_reportes.ReporteFacturacionKPIs(
        total_valor=float(total_valor),
        total_base=float(total_valor), 
        total_impuestos=0, 
        numero_facturas=numero_facturas,
        promedio_por_factura=float(promedio_por_factura),
        total_costo=float(total_costo) if filtros.tipo_reporte == 'ventas' else None,
        utilidad_bruta_valor_total=float(utilidad_bruta_valor_total) if filtros.tipo_reporte == 'ventas' else None,
        utilidad_bruta_porcentaje_promedio=float(margen_general) if filtros.tipo_reporte == 'ventas' else None
    )

    return schemas_reportes.ReporteFacturacionResponse(kpis=kpis, items=items_finales)

# app/services/reportes_facturacion.py (CORRECCIÓN)

def generar_pdf_reporte_facturacion(db: Session, empresa_id: int, filtros: schemas_reportes.ReporteFacturacionFiltros):
    """Genera el PDF del reporte detallado de facturación."""
    # FIX: Usar la función que devuelve los datos JSON
    report_data = get_reporte_facturacion_data(db=db, empresa_id=empresa_id, filtros=filtros) 
    
    if not report_data or not report_data.items:
        html_string = "<html><body><h1>Reporte Detallado</h1><p>No se encontraron datos para los filtros seleccionados.</p></body></html>"
        return HTML(string=html_string).write_pdf()

    empresa = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    if not empresa: raise HTTPException(status_code=404, detail="Empresa no encontrada.")

    filtros_serializables = {
        "fecha_inicio": filtros.fecha_inicio.isoformat(),
        "fecha_fin": filtros.fecha_fin.isoformat(),
        "tipo_reporte": filtros.tipo_reporte,
        "tercero_id": filtros.tercero_id,
        "centro_costo_id": filtros.centro_costo_id,
    }

    context = {
        "empresa": empresa,
        "filtros": filtros_serializables,
        "data": report_data,
        "titulo_reporte": f"Reporte Detallado de {filtros.tipo_reporte.capitalize()}"
    }

    try:
        template_name = 'reports/reporte_facturacion_detallado.html'
        # --- Lógica de Fallback (Mantenida por ahora) ---
        if template_name not in TEMPLATES_EMPAQUETADOS:
             template_name_fallback = 'reports/estado_inventarios_report.html' # Ejemplo, ajustar si es otro
             print(f"WARN: Plantilla {template_name} no encontrada. Usando {template_name_fallback} como fallback.")
             if template_name_fallback not in TEMPLATES_EMPAQUETADOS:
                  raise KeyError(f"Plantilla principal '{template_name}' ni fallback '{template_name_fallback}' encontradas.")
             template_name = template_name_fallback
        # --- Fin Lógica de Fallback ---

        template_string = TEMPLATES_EMPAQUETADOS[template_name]
        template = GLOBAL_JINJA_ENV.from_string(template_string)
        rendered_html = template.render(context)
        return HTML(string=rendered_html).write_pdf()
    except KeyError: raise HTTPException(status_code=500, detail=f"Plantilla '{template_name}' no encontrada en _templates_empaquetados.")
    except Exception as e:
        print(f"Error generando PDF reporte facturación: {e}"); traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al generar el PDF: {str(e)}")


def generar_url_firmada_reporte_facturacion(empresa_id: int, filtros: schemas_reportes.ReporteFacturacionFiltros) -> str:
    """Genera la URL firmada para la descarga del PDF del reporte detallado."""
    payload_dict = {
        "emp_id": empresa_id,
        "filtros": filtros.model_dump_json() # Usar model_dump_json para Pydantic V2
    }
    # Convertir fechas a string para serialización JSON
    payload_dict["filtros"] = json.loads(payload_dict["filtros"])
    payload_dict["filtros"]["fecha_inicio"] = payload_dict["filtros"]["fecha_inicio"]
    payload_dict["filtros"]["fecha_fin"] = payload_dict["filtros"]["fecha_fin"]
    payload_str = json.dumps(payload_dict)

    token = create_signed_token(data=payload_str, salt="report_print") # Asegúrate que 'report_print' sea el salt correcto
    base_url = settings.BASE_URL if settings.BASE_URL else "http://localhost:8000"
    signed_url = f"{base_url}/api/reportes-facturacion/imprimir-pdf/{token}"
    return signed_url


# =================================================================================
# === GET RENTABILIDAD POR GRUPO (MOTOR DE BI) ===
# =================================================================================
def get_rentabilidad_por_grupo(db: Session, empresa_id: int, filtros: schemas_rentabilidad.RentabilidadProductoFiltros) -> schemas_rentabilidad.RentabilidadProductoResponse:
    """
    [ACTUALIZADO] Calcula la rentabilidad con filtros avanzados de Tercero/Lista de Precios
    y devuelve los Top 5 Documentos por producto.
    """
    # 0. Sonda de Depuración
    print("\n--- SONDA BI 1: Filtros de BI Recibidos ---")
    print(f"Terceros: {filtros.tercero_ids}, Listas: {filtros.lista_precio_ids}")
    print(f"Margen Mínimo: {filtros.margen_minimo_porcentaje}, Solo Pérdidas: {filtros.mostrar_solo_perdidas}")
    
    # 1. Base Query para Documentos: Incluye joins necesarios para los nuevos filtros
    doc_query_base = db.query(models_doc.Documento).filter(
        models_doc.Documento.empresa_id == empresa_id,
        models_doc.Documento.fecha.between(filtros.fecha_inicio, filtros.fecha_fin),
        models_doc.Documento.anulado == False
    )

    # --- APLICACIÓN DE FILTRO AVANZADO: TERCEROS y LISTAS DE PRECIOS ---
    
    # 1. Aplicar Filtro por Tercero (Cliente)
    if filtros.tercero_ids:
        print(f"--- SONDA BI: Aplicando filtro por {len(filtros.tercero_ids)} Tercero(s).")
        doc_query_base = doc_query_base.filter(models_doc.Documento.beneficiario_id.in_(filtros.tercero_ids))
    
    # 2. Aplicar Filtro por Lista de Precios
    if filtros.lista_precio_ids:
        print(f"--- SONDA BI: Aplicando filtro por {len(filtros.lista_precio_ids)} Lista(s) de Precios.")
        
        # Obtenemos los IDs de los terceros que pertenecen a esas listas de precios.
        # CRÍTICO: Asumimos que la relación está en Tercero.
        terceros_con_lista = db.query(models_tercero.Tercero.id).filter(
            models_tercero.Tercero.lista_precio_id.in_(filtros.lista_precio_ids)
        ).subquery()
        
        # Filtramos los documentos por los beneficiarios que tienen esa lista de precios.
        doc_query_base = doc_query_base.filter(models_doc.Documento.beneficiario_id.in_(terceros_con_lista))

    # --- FIN FILTRO AVANZADO ---

    # Subquery de IDs de Documentos Filtrados
    doc_ids_subquery = doc_query_base.with_entities(models_doc.Documento.id).subquery()
    
    # --- DEFINICIÓN DE SUBCONSULTAS DE VENTA Y COSTO (FIX DE NAMERROR) ---
    # Subquery de Venta (ahora usa los Documentos filtrados)
    sq_venta = (
        select(
            models_mov_con.MovimientoContable.producto_id,
            func.sum(models_mov_con.MovimientoContable.credito).label("total_venta")
        )
        .join(doc_ids_subquery, models_mov_con.MovimientoContable.documento_id == doc_ids_subquery.c.id) # Unir con IDs filtrados
        .join(models_prod.Producto, models_mov_con.MovimientoContable.producto_id == models_prod.Producto.id)
        .join(models_grupo.GrupoInventario, models_prod.Producto.grupo_id == models_grupo.GrupoInventario.id)
        .filter(
            models_mov_con.MovimientoContable.producto_id.isnot(None),
            models_mov_con.MovimientoContable.cuenta_id == models_grupo.GrupoInventario.cuenta_ingreso_id
        )
        .group_by(models_mov_con.MovimientoContable.producto_id)
        .subquery()
    )
    
    # Subquery de Costo (ahora usa los Documentos filtrados)
    sq_costo = (
        select(
            models_prod.MovimientoInventario.producto_id,
            func.sum(models_prod.MovimientoInventario.costo_total).label("total_costo")
        )
        .join(doc_ids_subquery, models_prod.MovimientoInventario.documento_id == doc_ids_subquery.c.id) # Unir con IDs filtrados
        .filter(
            models_prod.MovimientoInventario.tipo_movimiento == 'SALIDA_VENTA'
        )
        .group_by(models_prod.MovimientoInventario.producto_id)
        .subquery()
    )
    # --- FIN DEFINICIÓN DE SUBCONSULTAS ---

    # 2. Consulta Principal (Rentabilidad)
    query = (
        db.query(
            models_prod.Producto.id.label("producto_id"),
            models_prod.Producto.codigo.label("producto_codigo"),
            models_prod.Producto.nombre.label("producto_nombre"),
            func.coalesce(sq_venta.c.total_venta, Decimal('0.0')).label("total_venta"),
            func.coalesce(sq_costo.c.total_costo, Decimal('0.0')).label("total_costo")
        )
        .outerjoin(sq_venta, models_prod.Producto.id == sq_venta.c.producto_id)
        .outerjoin(sq_costo, models_prod.Producto.id == sq_costo.c.producto_id)
        .filter(models_prod.Producto.empresa_id == empresa_id)
        .filter(models_prod.Producto.es_servicio == False)
    )

    # 3. Aplicar Filtros de Producto (Existentes)
    if filtros.producto_ids:
        query = query.filter(models_prod.Producto.id.in_(filtros.producto_ids))
    elif filtros.grupo_ids:
        query = query.filter(models_prod.Producto.grupo_id.in_(filtros.grupo_ids))
    elif filtros.producto_id:
         query = query.filter(models_prod.Producto.id == filtros.producto_id)

    # Filtrar productos sin movimiento 
    query = query.filter(or_(sq_venta.c.total_venta.isnot(None), sq_costo.c.total_costo.isnot(None)))

    query = query.order_by(models_prod.Producto.nombre)

    resultados = query.all()

    # 4. Post-procesamiento, Cálculo de Margen y Top 5 Documentos
    items_finales = []
    
    # --- FIX CRÍTICO DE UNBOUNDLOCALERROR ---
    # Inicializar acumuladores para el TOTAL GENERAL ANTES de los filtros de Python.
    total_venta_general = Decimal('0.0')
    total_costo_general = Decimal('0.0')

    items_calculados = []
    
    # 4.1 Acumulación PREVIA al filtro de UI
    for row in resultados:
        # FIX DE ALIAS: Accedemos a los alias definidos en la consulta principal
        venta = Decimal(str(row.total_venta or '0.0')) 
        # FIX CRÍTICO: row.costo_total es el alias correcto del subquery sq_costo
        costo = Decimal(str(row.total_costo or '0.0')) 
        
        # Acumular TOTALES GENERALES (La suma de todos los ítems en el rango, sin importar filtros de margen)
        total_venta_general += venta
        total_costo_general += costo

        utilidad = venta - costo
        margen = (utilidad / venta) * Decimal('100.0') if venta != Decimal('0.0') else Decimal('0.0')
        
        # Guardamos el item calculado (incluyendo la utilidad y margen)
        item_data = {
            'row': row,
            'venta': venta,
            'costo': costo,
            'utilidad': utilidad,
            'margen': margen
        }
        items_calculados.append(item_data)
        
    # 4.2 Aplicación de Filtros de UI y Construcción Final
    
    # Acumuladores para la lista *filtrada* que se mostrará en la tabla
    total_venta_final = Decimal('0.0')
    total_costo_final = Decimal('0.0')
    
    for item_data in items_calculados:
        venta = item_data['venta']
        utilidad = item_data['utilidad']
        margen = item_data['margen']
        row = item_data['row']
        
        # --- LÓGICA DE FILTRO DE UI (Margen Mínimo/Solo Pérdidas) ---
        
        # 1. Filtro Mostrar Solo Pérdidas
        if filtros.mostrar_solo_perdidas and utilidad >= Decimal('0.0'):
            # print(f"--- SONDA BI: Saltando {row.producto_codigo} (Utilidad >= 0.0, solo pérdidas solicitadas).")
            continue 
        
        # 2. Filtro Margen Mínimo
        if filtros.margen_minimo_porcentaje is not None and filtros.margen_minimo_porcentaje != 0:
            margen_minimo_dec = Decimal(str(filtros.margen_minimo_porcentaje))
            if margen < margen_minimo_dec:
                 # print(f"--- SONDA BI: Saltando {row.producto_codigo} (Margen {margen}% < Mínimo {margen_minimo_dec}%).")
                 continue 
        # --- Fin Lógica de Filtro de UI ---

        # Si pasa los filtros, acumular los totales de la lista *filtrada*
        total_venta_final += venta
        total_costo_final += item_data['costo']
        
        # Obtener Trazabilidad Completa de Documentos (Función intensiva)
        # [CRÍTICO: Usamos el nuevo nombre de función y pasamos el filtro de cliente]
        trazabilidad_docs = _get_trazabilidad_documentos(
            db, 
            row.producto_id, 
            filtros.fecha_inicio, 
            filtros.fecha_fin,
            filtros.tercero_ids # <--- FIX CRÍTICO: PASAR EL FILTRO DE CLIENTE
        )
        
        # Redondeos y conversiones
        margen = margen.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        venta = venta.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        costo = item_data['costo'].quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        utilidad = utilidad.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


        items_finales.append(schemas_rentabilidad.RentabilidadProductoItem(
            producto_id=row.producto_id,
            producto_codigo=row.producto_codigo,
            producto_nombre=row.producto_nombre,
            fecha_inicio_periodo=filtros.fecha_inicio,
            fecha_fin_periodo=filtros.fecha_fin,
            total_venta=float(venta),
            total_costo=float(costo),
            total_utilidad=float(utilidad),
            margen_rentabilidad_porcentaje=float(margen),
            # [CRÍTICO]: Se usa el nuevo nombre de campo
            trazabilidad_documentos=trazabilidad_docs 
        ))

    total_utilidad_final = total_venta_final - total_costo_final
    margen_final_porcentaje = (total_utilidad_final / total_venta_final) * Decimal('100.0') if total_venta_final != Decimal('0.0') else Decimal('0.0')
    margen_final_porcentaje = margen_final_porcentaje.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


    # La respuesta total ahora usa los acumuladores FINAL_FILTRADOS
    # IMPORTANTE: total_venta_general es la suma de todos los ítems ANTES de los filtros de UI.
    totales_obj = schemas_rentabilidad.RentabilidadTotales(
        total_venta_general=float(total_venta_general.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
        total_costo_general=float(total_costo_final.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
        total_utilidad_general=float(total_utilidad_final.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
        margen_general_porcentaje=float(margen_final_porcentaje)
    )
    
    print(f"--- SONDA BI 2: Resultados finales: {len(items_finales)} ítems después del filtrado de Python.")
    print(f"--- SONDA BI 3: TOTALES ENVIADOS: Venta={total_venta_final}, Utilidad={total_utilidad_final} ---")
    return schemas_rentabilidad.RentabilidadProductoResponse(items=items_finales, totales=totales_obj)

# --- Wrapper get_rentabilidad_por_producto (ACTUALIZADO) ---
def get_rentabilidad_por_producto(db: Session, empresa_id: int, filtros: schemas_rentabilidad.RentabilidadProductoFiltros) -> schemas_rentabilidad.RentabilidadProductoResponse:
    """Wrapper. Llama a get_rentabilidad_por_grupo asegurando que solo producto_id se use."""
    # Crear un nuevo objeto de filtros basado en el recibido, pero limpiando los demás
    filtros_para_individual = schemas_rentabilidad.RentabilidadProductoFiltros(
        fecha_inicio=filtros.fecha_inicio,
        fecha_fin=filtros.fecha_fin,
        producto_id=filtros.producto_id, # Solo este filtro debe pasar
        grupo_ids=None,
        producto_ids=None,
        tercero_ids=filtros.tercero_ids,
        lista_precio_ids=filtros.lista_precio_ids,
        margen_minimo_porcentaje=filtros.margen_minimo_porcentaje,
        mostrar_solo_perdidas=filtros.mostrar_solo_perdidas
    )
    return get_rentabilidad_por_grupo(db=db, empresa_id=empresa_id, filtros=filtros_para_individual)


def generar_pdf_rentabilidad_documento(db: Session, empresa_id: int, filtros: schemas_reportes.ReporteRentabilidadDocumentoFiltros):
    """Genera el PDF del reporte de rentabilidad por documento."""
    
    report_data = get_rentabilidad_por_documento(db=db, empresa_id=empresa_id, filtros=filtros)

    if not report_data or not report_data.detalle:
        html_string = "<html><body><h1>Rentabilidad por Documento</h1><p>No se encontraron datos para el documento seleccionado.</p></body></html>"
        return HTML(string=html_string).write_pdf()

    # Obtener la empresa para el encabezado del PDF
    empresa = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    if not empresa: raise HTTPException(status_code=404, detail="Empresa no encontrada.")

    # Preparar el contexto para la plantilla Jinja
    context = {
        "empresa": empresa,
        "filtros": {
            "tipo_documento_codigo": filtros.tipo_documento_codigo,
            "numero_documento": filtros.numero_documento
        },
        "data": report_data,
        "titulo_reporte": f"Rentabilidad del Documento {report_data.documento_ref}"
    }

    try:
        template_name = 'reports/rentabilidad_documento_report.html' 
        
        # --- Lógica de Fallback (Mantenida) ---
        if template_name not in TEMPLATES_EMPAQUETADOS:
             template_name_fallback = 'reports/rentabilidad_producto_grupo_report.html'
             print(f"WARN: Plantilla '{template_name}' no encontrada. Usando fallback '{template_name_fallback}'.")
             if template_name_fallback not in TEMPLATES_EMPAQUETADOS:
                  raise KeyError(f"Plantilla principal '{template_name}' ni fallback '{template_name_fallback}' encontradas.")
             template_name = template_name_fallback
        # --- Fin Lógica de Fallback ---

        template_string = TEMPLATES_EMPAQUETADOS[template_name]
        template = GLOBAL_JINJA_ENV.from_string(template_string)
        rendered_html = template.render(context)
        return HTML(string=rendered_html).write_pdf()

    except Exception as e:
        print(f"ERROR FATAL generando PDF rentabilidad por documento: {e}"); traceback.print_exc()
        error_detail = f"Error al generar el PDF: {str(e)}"
        raise HTTPException(status_code=500, detail=error_detail)


def get_rentabilidad_por_documento(
    db: Session,
    empresa_id: int,
    # Corregido: Usar schemas_reportes que es donde está definido el ReporteRentabilidadDocumentoFiltros
    filtros: schemas_reportes.ReporteRentabilidadDocumentoFiltros 
) -> schemas_reportes.ReporteRentabilidadDocumentoResponse:
    """Calcula la rentabilidad línea por línea para un documento específico."""
    
    # --- SONDA 1: Filtros de entrada ---
    print("\n--- SONDA 1: INICIO DE BÚSQUEDA POR DOCUMENTO ---")
    print(f"Filtros recibidos: Código='{filtros.tipo_documento_codigo}', Número='{filtros.numero_documento}', Empresa ID={empresa_id}")
    
    # 1. Buscar el documento principal
    # FIX CLAVE: Buscar el tipo de documento por CÓDIGO (string) en lugar de ID (int)
    numero_doc_str = str(filtros.numero_documento).strip()
    
    # Intento de limpieza: Si el usuario envía "FV-41", extraemos "41"
    if "-" in numero_doc_str:
        possible_num = numero_doc_str.split("-")[-1].strip()
        if possible_num.isdigit():
            numero_doc_str = possible_num
            print(f"--- SONDA: Número limpiado de formato compuesto: '{numero_doc_str}'")

    # Primero buscamos el Tipo de Documento por su código
    tipo_documento = db.query(models_tipo_doc.TipoDocumento).filter(
        models_tipo_doc.TipoDocumento.empresa_id == empresa_id,
        models_tipo_doc.TipoDocumento.codigo == filtros.tipo_documento_codigo.upper()
    ).first()

    if not tipo_documento:
        # --- SONDA 2: Fallo en Tipo de Documento ---
        print(f"--- SONDA 2: FALLA - Tipo de Documento con código '{filtros.tipo_documento_codigo}' NO ENCONTRADO.")
        ref = f"Código: {filtros.tipo_documento_codigo}, No: {filtros.numero_documento}"
        raise HTTPException(status_code=404, detail=f"Tipo de Documento con código '{filtros.tipo_documento_codigo}' no encontrado para esta empresa.")

    # --- SONDA 3: Tipo de Documento encontrado ---
    print(f"--- SONDA 3: ÉXITO - Tipo Doc ID encontrado: {tipo_documento.id}. Buscando Documento...")

    # Query base para el documento
    doc_query = db.query(models_doc.Documento).filter(
        models_doc.Documento.empresa_id == empresa_id,
        models_doc.Documento.tipo_documento_id == tipo_documento.id, 
        models_doc.Documento.anulado == False
    )

    # Logica robusta para el número (Integer en DB)
    if numero_doc_str.isdigit():
        doc_query = doc_query.filter(models_doc.Documento.numero == int(numero_doc_str))
    else:
        # Fallback por si la columna fuera string en algún caso legacy o migración extraña, 
        # aunque el modelo dice Integer.
        doc_query = doc_query.filter(cast(models_doc.Documento.numero, SAString) == numero_doc_str)

    # Ordenamos por ID descendente para tomar el ÚLTIMO creado en caso de duplicados
    documento = doc_query.order_by(models_doc.Documento.id.desc()).first()

    if not documento:
        # --- SONDA 4: Fallo en Documento ---
        print(f"--- SONDA 4: FALLA - Documento con Tipo ID {tipo_documento.id} y Número '{numero_doc_str}' NO ENCONTRADO.")
        ref = f"Código: {filtros.tipo_documento_codigo}, No: {filtros.numero_documento} (Buscado: {numero_doc_str})"
        raise HTTPException(status_code=404, detail=f"Documento '{ref}' no encontrado o anulado. Revise el número exacto.")

    # --- SONDA 5: Documento encontrado ---
    print(f"--- SONDA 5: ÉXITO - Documento ID encontrado: {documento.id}. Iniciando cálculo de Rentabilidad.")
    
    # 2. Construir la consulta de movimientos y rentabilidad
    
    # ESTRATEGIA ROBUSTA (HYBRID LEDGER):
    # En lugar de depender de MovimientoInventario, usamos MovimientoContable como fuente de verdad financiera.
    # 1. Obtenemos Venta Total por producto (del Haber/Crédito de Ingresos)
    # 2. Obtenemos Costo Total por producto (del Debe/Débito de Costos)
    # 3. Obtenemos Cantidad (de MovimientoInventario, si existe)

    # 2.1 Subconsulta de Venta (Ingresos)
    sq_venta = (
        select(
            models_mov_con.MovimientoContable.producto_id,
            func.sum(models_mov_con.MovimientoContable.credito).label("valor_venta_total")
        )
        .filter(
            models_mov_con.MovimientoContable.documento_id == documento.id,
            models_mov_con.MovimientoContable.producto_id.isnot(None), 
            # Cuenta de Ingreso:
            models_mov_con.MovimientoContable.cuenta_id == models_grupo.GrupoInventario.cuenta_ingreso_id
        )
        .join(models_prod.Producto, models_mov_con.MovimientoContable.producto_id == models_prod.Producto.id)
        .join(models_grupo.GrupoInventario, models_prod.Producto.grupo_id == models_grupo.GrupoInventario.id)
        .group_by(models_mov_con.MovimientoContable.producto_id)
        .subquery()
    )
    
    # 2.2 Subconsulta de Costo (Costo de Venta desde Contabilidad)
    sq_costo_contable = (
        select(
            models_mov_con.MovimientoContable.producto_id,
            func.sum(models_mov_con.MovimientoContable.debito).label("valor_costo_total")
        )
        .filter(
            models_mov_con.MovimientoContable.documento_id == documento.id,
            models_mov_con.MovimientoContable.producto_id.isnot(None),
            # Cuenta de Costo:
            models_mov_con.MovimientoContable.cuenta_id == models_grupo.GrupoInventario.cuenta_costo_venta_id
        )
        .join(models_prod.Producto, models_mov_con.MovimientoContable.producto_id == models_prod.Producto.id)
        .join(models_grupo.GrupoInventario, models_prod.Producto.grupo_id == models_grupo.GrupoInventario.id)
        .group_by(models_mov_con.MovimientoContable.producto_id)
        .subquery()
    )

    # 2.3 Subconsulta de Cantidad (Desde Inventario - Opcional)
    sq_inventario = (
        select(
            models_prod.MovimientoInventario.producto_id,
            func.sum(models_prod.MovimientoInventario.cantidad).label("cantidad_total"),
            # Costo unitario promedio ponderado o del último movimiento (simplificado: max)
            func.max(models_prod.MovimientoInventario.costo_unitario).label("costo_unitario_ref")
        )
        .filter(
            models_prod.MovimientoInventario.documento_id == documento.id,
            models_prod.MovimientoInventario.tipo_movimiento == 'SALIDA_VENTA'
        )
        .group_by(models_prod.MovimientoInventario.producto_id)
        .subquery()
    )


    # 2.4 Consulta Principal: DRIVEN BY PRODUCTS IN ACCOUNTING
    # Buscamos productos que tengan ventas O costos en este documento.
    
    # Distinct Product IDs in this document (Union of Sales and Costs)
    # Para simplificar en SQLAlchemy y no hacer unions complejos, consultamos Producto
    # y filtramos aquellos que tengan sq_venta O sq_costo
    
    query = (
        db.query(
            models_prod.Producto.id.label("producto_id"),
            models_prod.Producto.codigo.label("producto_codigo"),
            models_prod.Producto.nombre.label("producto_nombre"),
            func.coalesce(sq_inventario.c.cantidad_total, Decimal('0.0')).label("cantidad"),
            func.coalesce(sq_inventario.c.costo_unitario_ref, Decimal('0.0')).label("costo_unitario"),
            func.coalesce(sq_costo_contable.c.valor_costo_total, Decimal('0.0')).label("costo_total"), 
            func.coalesce(sq_venta.c.valor_venta_total, Decimal('0.0')).label("valor_venta_total")
        )
        .outerjoin(sq_venta, models_prod.Producto.id == sq_venta.c.producto_id)
        .outerjoin(sq_costo_contable, models_prod.Producto.id == sq_costo_contable.c.producto_id)
        .outerjoin(sq_inventario, models_prod.Producto.id == sq_inventario.c.producto_id)
        .filter(
            models_prod.Producto.empresa_id == empresa_id,
            or_(sq_venta.c.valor_venta_total.isnot(None), sq_costo_contable.c.valor_costo_total.isnot(None))
        )
        .order_by(models_prod.Producto.nombre)
    )


    # --- SONDA 6: Ejecutando Consulta ---
    print(f"--- SONDA 6: Ejecutando consulta HÍBRIDA de Rentabilidad para Doc ID {documento.id}")
    
    resultados = query.all()
    if not resultados:
        # --- SONDA 7: No hay líneas ---
        print(f"--- SONDA 7: FALLA - Documento ID {documento.id} no tiene movimientos contables (Venta o Costo).")
        raise HTTPException(status_code=404, detail=f"Documento '{documento.tipo_documento.codigo}-{documento.numero}' vacío (sin movimientos contables de producto).")


    # 3. Post-procesamiento y Totales
    detalle_final: List[schemas_reportes.ReporteRentabilidadDocumentoItem] = []
    total_venta = Decimal('0.0')
    total_costo = Decimal('0.0')

    idx_linea = 1
    for row in resultados:
        cantidad = Decimal(str(row.cantidad or '0.0'))
        # Nota: El costo unitario puede venir de inventario, o inferirse si cant > 0
        costo_unitario_ref = Decimal(str(row.costo_unitario or '0.0'))
        
        costo_total = Decimal(str(row.costo_total or '0.0'))
        venta_total = Decimal(str(row.valor_venta_total or '0.0'))
        
        if cantidad > 0 and costo_unitario_ref == 0:
            costo_unitario_ref = costo_total / cantidad if cantidad else Decimal('0.0')

        if venta_total == Decimal('0.0'):
             utilidad = -costo_total # Pérdida pura si hay costo sin venta
             venta_unitario = Decimal('0.0')
             margen = Decimal('0.0') # O indefinido
        else:
             utilidad = venta_total - costo_total
             venta_unitario = venta_total / cantidad if cantidad != Decimal('0.0') else venta_total # Fallback si cantidad es 0
             margen = (utilidad / venta_total) * Decimal('100.0')
        
        # Acumular totales
        total_venta += venta_total
        total_costo += costo_total

        detalle_final.append(schemas_reportes.ReporteRentabilidadDocumentoItem(
            linea_documento_id=idx_linea, # ID Ficticio secuencial ya que agrupamos
            producto_codigo=row.producto_codigo,
            producto_nombre=row.producto_nombre,
            cantidad=cantidad.quantize(Decimal('0.00')),
            valor_venta_unitario=venta_unitario.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP),
            valor_venta_total=venta_total.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP),
            costo_unitario=costo_unitario_ref.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP),
            costo_total=costo_total.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP),
            utilidad_bruta_valor=utilidad.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP),
            utilidad_bruta_porcentaje=margen.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        ))
        idx_linea += 1

    # 4. Construir respuesta final
    total_utilidad = total_venta - total_costo
    total_margen = (total_utilidad / total_venta) * Decimal('100.0') if total_venta != Decimal('0.0') else Decimal('0.0')
    
    totales_obj = schemas_reportes.ReporteRentabilidadDocumentoTotales(
        total_venta=total_venta.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP),
        total_costo=total_costo.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP),
        total_utilidad_bruta_valor=total_utilidad.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP),
        total_utilidad_bruta_porcentaje=total_margen.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    )

    response = schemas_reportes.ReporteRentabilidadDocumentoResponse(
        documento_id=documento.id,
        documento_ref=f"{documento.tipo_documento.codigo}-{documento.numero}",
        fecha=documento.fecha,
        tercero_nombre=documento.beneficiario.razon_social if documento.beneficiario else "N/A",
        tercero_nit=documento.beneficiario.nit if documento.beneficiario else "N/A",
        detalle=detalle_final,
        totales=totales_obj
    )

    # --- SONDA 8: ÉXITO FINAL ---
    print(f"--- SONDA 8: ÉXITO - Rentabilidad Calculada (Híbrida). Lineas: {len(detalle_final)}. Utilidad Total: {total_utilidad} ---")
    return response


# =================================================================================
# === REGISTRY IMPLEMENTATION: RENTABILIDAD ===
# =================================================================================

@ReportRegistry.register
class RentabilidadReportService(BaseReport):
    key = "rentabilidad_producto"
    description = "Reporte de Análisis de Rentabilidad por Producto o Grupo"
    
    # Define schema for filtering
    filter_schema = schemas_rentabilidad.RentabilidadProductoFiltros

    def get_data(self, db: Session, empresa_id: int, filtros: dict):
        # Convert dictionary filters to Pydantic model
        filtros_obj = self.filter_schema(**filtros)
        return get_rentabilidad_por_grupo(db, empresa_id, filtros_obj)

    def generate_pdf(self, db: Session, empresa_id: int, filtros: dict):
        # Convert dictionary filters to Pydantic model
        filtros_obj = self.filter_schema(**filtros)
        
        # Call the existing PDF generation function
        # This function returns bytes (since it calls HTML(...).write_pdf())
        pdf_bytes = generar_pdf_rentabilidad_producto(db, empresa_id, filtros_obj)
        
        filename = f"Rentabilidad_{filtros_obj.fecha_inicio}_a_{filtros_obj.fecha_fin}.pdf"
        return pdf_bytes, filename
