# app/services/libros_oficiales.py
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import date
from typing import Optional, Dict, Any, List
from fastapi import HTTPException
from weasyprint import HTML
from jinja2 import Environment, select_autoescape
import itertools
import operator
import locale

from app.services._templates_empaquetados import TEMPLATES_EMPAQUETADOS
from ..models import (
    Documento as models_doc, MovimientoContable as models_mov,
    TipoDocumento as models_tipo, Tercero as models_tercero,
    PlanCuenta as models_plan, Empresa as models_empresa
)

# --- LÓGICA DE PLANTILLAS ---
def format_currency(value):
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, '')
        except locale.Error:
            pass
    numeric_value = float(value or 0.0)
    return f"${numeric_value:,.2f}"

GLOBAL_JINJA_ENV = Environment(loader=None, autoescape=select_autoescape(['html', 'xml']))
GLOBAL_JINJA_ENV.filters['groupby'] = lambda value, attribute: itertools.groupby(sorted(value, key=operator.itemgetter(attribute)), operator.itemgetter(attribute))
GLOBAL_JINJA_ENV.globals['list'] = list
GLOBAL_JINJA_ENV.filters['currency'] = format_currency

# --- FUNCIÓN DE DATOS PARA FRONTEND (YA CORREGIDA Y FUNCIONAL) ---
def get_data_for_libro_diario(
    db: Session,
    empresa_id: int,
    fecha_inicio: date,
    fecha_fin: date,
    tipos_documento_ids: Optional[List[int]] = None,
    cuenta_filtro: Optional[str] = None,
    numero_documento: Optional[str] = None,
    beneficiario_filtro: Optional[str] = None,
    concepto_filtro: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Obtiene una lista plana de movimientos contables para la tabla del Libro Diario en el frontend.
    """
    try:
        query = db.query(
            models_doc.id.label("documento_id"), # NUEVO
            models_mov.id.label("movimiento_id"), # NUEVO
            models_doc.fecha,
            models_tipo.nombre.label("tipo_documento"),
            models_tipo.codigo.label("tipo_documento_codigo"), 
            models_doc.numero.label("numero_documento"),
            models_tercero.razon_social.label("beneficiario_nombre"),
            models_tercero.nit.label("beneficiario_nit"),
            models_mov.concepto,
            models_plan.codigo.label("cuenta_codigo"),
            models_plan.nombre.label("cuenta_nombre"),
            models_mov.debito,
            models_mov.credito
        ).join(models_mov, models_doc.id == models_mov.documento_id)\
         .join(models_tipo, models_doc.tipo_documento_id == models_tipo.id)\
         .join(models_plan, models_mov.cuenta_id == models_plan.id)\
         .outerjoin(models_tercero, models_doc.beneficiario_id == models_tercero.id)\
         .filter(
            models_doc.empresa_id == empresa_id,
            models_doc.fecha.between(fecha_inicio, fecha_fin),
            models_doc.anulado == False
        )

        if tipos_documento_ids:
            query = query.filter(models_doc.tipo_documento_id.in_(tipos_documento_ids))
            
        if cuenta_filtro:
            filtro = f"%{cuenta_filtro}%"
            query = query.filter(or_(
                models_plan.codigo.ilike(filtro),
                models_plan.nombre.ilike(filtro)
            ))

        if numero_documento:
            query = query.filter(models_doc.numero.ilike(f"%{numero_documento}%"))

        if beneficiario_filtro:
            filtro_ben = f"%{beneficiario_filtro}%"
            query = query.filter(or_(
                models_tercero.razon_social.ilike(filtro_ben),
                models_tercero.nit.ilike(filtro_ben)
            ))

        if concepto_filtro:
            query = query.filter(models_mov.concepto.ilike(f"%{concepto_filtro}%"))

        movimientos_raw = query.order_by(models_doc.fecha, models_doc.numero, models_mov.id).all()

        report_data = [
            {
                "id": mov.movimiento_id, # Key única para React
                "documento_id": mov.documento_id, # ID para impresión
                "fecha": mov.fecha,
                "tipo_documento": mov.tipo_documento, 
                "tipo_documento_codigo": mov.tipo_documento_codigo, 
                "numero_documento": mov.numero_documento,
                "beneficiario_nombre": mov.beneficiario_nombre or "N/A",
                "beneficiario_nit": mov.beneficiario_nit or "N/A",
                "cuenta_codigo": mov.cuenta_codigo,
                "cuenta_nombre": mov.cuenta_nombre,
                "concepto": mov.concepto,
                "debito": float(mov.debito or 0.0),
                "credito": float(mov.credito or 0.0)
            }
            for mov in movimientos_raw
        ]
        
        return report_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar datos del Libro Diario: {str(e)}")


# --- FUNCIÓN DE PDF (CORREGIDA Y COMPLETA) ---
def generate_libro_diario_pdf(
    db: Session,
    empresa_id: int,
    fecha_inicio: date,
    fecha_fin: date,
    tipos_documento_ids: Optional[List[int]] = None,
    cuenta_filtro: Optional[str] = None,
    numero_documento: Optional[str] = None,
    beneficiario_filtro: Optional[str] = None,
    concepto_filtro: Optional[str] = None
):
    """
    Genera el archivo PDF para el reporte del Libro Diario, construyendo la estructura
    de datos exacta que la plantilla journal_report.html espera.
    """
    movimientos_planos = get_data_for_libro_diario(
        db, empresa_id, fecha_inicio, fecha_fin, 
        tipos_documento_ids=tipos_documento_ids, 
        cuenta_filtro=cuenta_filtro,
        numero_documento=numero_documento,
        beneficiario_filtro=beneficiario_filtro,
        concepto_filtro=concepto_filtro
    )
    
    
    # Calcular totales globales
    total_debito = sum(m['debito'] for m in movimientos_planos)
    total_credito = sum(m['credito'] for m in movimientos_planos)

    report_data_structured = []
    
    # Agrupamiento: Fecha -> Documento
    # Nota: movimientos_planos ya viene ordenado por fecha.
    for fecha, group_fecha in itertools.groupby(movimientos_planos, key=lambda x: x['fecha']):
        # Se convierte a lista para re-ordenar por documento
        group_fecha_list = list(group_fecha)
        # Ordenar por Tipo y Número para agrupar documentos correctamente
        group_fecha_list.sort(key=lambda x: (x['tipo_documento'], x['numero_documento']))
        
        date_entry = {
            'fecha': fecha,
            'documents': []
        }
        
        for doc_key, group_doc in itertools.groupby(group_fecha_list, key=lambda x: (x['tipo_documento'], x['numero_documento'], x['beneficiario_nombre'])):
            tipo, num, ben = doc_key
            rows = list(group_doc)
            
            sub_deb = sum(r['debito'] for r in rows)
            sub_cred = sum(r['credito'] for r in rows)
            
            date_entry['documents'].append({
                'tipo_documento': tipo,
                'numero_documento': num,
                'beneficiario_nombre': ben,
                'rows': rows,
                'total_debito': sub_deb,
                'total_credito': sub_cred
            })
            
        report_data_structured.append(date_entry)

    empresa_info = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    if not empresa_info:
        raise HTTPException(status_code=404, detail=f"No se encontró la empresa con ID {empresa_id}")

    # Construir descripción de filtros para el encabezado del PDF
    desc_filtros = []
    if tipos_documento_ids:
        desc_filtros.append(f"Tipos Doc: {tipos_documento_ids}")
    if cuenta_filtro:
        desc_filtros.append(f"Cuenta: {cuenta_filtro}")
    if numero_documento:
        desc_filtros.append(f"Número: {numero_documento}")
    if beneficiario_filtro:
        desc_filtros.append(f"Beneficiario: {beneficiario_filtro}")
    if concepto_filtro:
        desc_filtros.append(f"Concepto: {concepto_filtro}")
    
    filtros_str = " | ".join(desc_filtros) if desc_filtros else None

    context = {
        "empresa_nombre": empresa_info.razon_social,
        "empresa_nit": empresa_info.nit,
        "fecha_inicio": fecha_inicio.strftime('%d/%m/%Y'),
        "fecha_fin": fecha_fin.strftime('%d/%m/%Y'),
        "report_data_structured": report_data_structured,
        "total_debito": total_debito,
        "total_credito": total_credito,
        "filtros_aplicados": filtros_str
    }
    
    try:
        template_string = TEMPLATES_EMPAQUETADOS['reports/journal_report.html']
        template = GLOBAL_JINJA_ENV.from_string(template_string)
        rendered_html = template.render(context)
        return HTML(string=rendered_html).write_pdf()
    except KeyError:
        raise HTTPException(status_code=500, detail="La plantilla 'reports/journal_report.html' no fue encontrada.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al renderizar el PDF del Libro Diario: {e}")


# --- OTRAS FUNCIONES DEL ARCHIVO (COMPLETAS Y SIN CAMBIOS) ---
def get_data_for_libro_mayor_y_balances(
    db: Session,
    empresa_id: int,
    fecha_inicio: date,
    fecha_fin: date
) -> Dict[str, Any]:
    try:
        # 1. Obtener todas las cuentas del PUC (jerarquía completa) para nombres
        all_accounts = db.query(models_plan).filter(
            models_plan.empresa_id == empresa_id
        ).all()
        # Mapa: '1105' -> 'CAJA', '1' -> 'ACTIVO'
        mapa_nombres = {c.codigo: c.nombre for c in all_accounts}

        # Asegurar nombres por defecto para niveles superiores si no existen
        defaults = {
            '1': 'ACTIVO', '2': 'PASIVO', '3': 'PATRIMONIO', 
            '4': 'INGRESOS', '5': 'GASTOS', '6': 'COSTOS DE VENTA',
            '7': 'COSTOS DE PRODUCCIÓN', '8': 'CUENTAS DE ORDEN'
        }
        for code, name in defaults.items():
            if code not in mapa_nombres:
                mapa_nombres[code] = name

        # 2. Inicializar diccionario de agregación
        # Se usará para acumular valores en niveles 1, 2 y 4
        # data_tree = { '1': {...}, '11': {...}, '1105': {...} }
        data_tree = {}

        def get_or_create_node(codigo):
            if codigo not in data_tree:
                data_tree[codigo] = {
                    "cuenta_codigo": codigo,
                    "cuenta_nombre": mapa_nombres.get(codigo, "SIN NOMBRE"),
                    "saldo_inicial": 0.0,
                    "total_debito": 0.0,
                    "total_credito": 0.0,
                    "nivel": len(codigo)
                }
            return data_tree[codigo]

        # 3. Función Helper para acumular en cascada (4 -> 2 -> 1)
        def acumular_valores(codigo_full, s_ini, deb, cred):
            # Solo nos interesa hasta nivel 4 (Major)
            # Ignoramos auxiliares de 6+ dígitos, pero sus valores se suman a los padres 4, 2, 1
            
            # Determinar código nivel 4 (si el movimiento es de una cuenta >= 4 dígitos)
            code_4 = codigo_full[:4] if len(codigo_full) >= 4 else None
            code_2 = codigo_full[:2] if len(codigo_full) >= 2 else None
            code_1 = codigo_full[:1] if len(codigo_full) >= 1 else None

            # Acumular en Nivel 4
            if code_4:
                node = get_or_create_node(code_4)
                node["saldo_inicial"] += float(s_ini)
                node["total_debito"] += float(deb)
                node["total_credito"] += float(cred)
            
            # Acumular en Nivel 2
            if code_2:
                node = get_or_create_node(code_2)
                node["saldo_inicial"] += float(s_ini)
                node["total_debito"] += float(deb)
                node["total_credito"] += float(cred)

            # Acumular en Nivel 1
            if code_1:
                node = get_or_create_node(code_1)
                node["saldo_inicial"] += float(s_ini)
                node["total_debito"] += float(deb)
                node["total_credito"] += float(cred)

        # 4. Obtener Saldos Iniciales Bulk
        saldos_ini_query = db.query(
            models_plan.codigo,
            func.sum(models_mov.debito - models_mov.credito).label("saldo")
        ).join(models_doc, models_mov.documento_id == models_doc.id)\
         .join(models_plan, models_mov.cuenta_id == models_plan.id)\
         .filter(
            models_doc.empresa_id == empresa_id,
            models_doc.fecha < fecha_inicio,
            models_doc.anulado == False
        ).group_by(models_plan.codigo).all()

        for row in saldos_ini_query:
            acumular_valores(row.codigo, row.saldo or 0, 0, 0)

        # 5. Obtener Movimientos del Periodo Bulk
        movimientos_query = db.query(
            models_plan.codigo,
            func.sum(models_mov.debito).label("debito"),
            func.sum(models_mov.credito).label("credito")
        ).join(models_doc, models_mov.documento_id == models_doc.id)\
         .join(models_plan, models_mov.cuenta_id == models_plan.id)\
         .filter(
            models_doc.empresa_id == empresa_id,
            models_doc.fecha.between(fecha_inicio, fecha_fin),
            models_doc.anulado == False
        ).group_by(models_plan.codigo).all()

        for row in movimientos_query:
            acumular_valores(row.codigo, 0, row.debito or 0, row.credito or 0)

        # 6. Preparar lista final ordenada
        # Filtramos nodos que tengan algún valor != 0
        lista_final = []
        
        # Totales Generales (Solo sumamos Nivel 1 para el gran total aritmético, o deb/cred de nivel 1)
        gran_total_debito = 0.0
        gran_total_credito = 0.0

        for codigo, nodo in data_tree.items():
            # Nuevo saldo = Inicial + Debito - Credito
            nodo["nuevo_saldo"] = nodo["saldo_inicial"] + nodo["total_debito"] - nodo["total_credito"]
            
            # Filtro de ceros
            if (abs(nodo["saldo_inicial"]) > 0.01 or 
                abs(nodo["total_debito"]) > 0.01 or 
                abs(nodo["total_credito"]) > 0.01):
                
                lista_final.append(nodo)
                
                # Para totales generales, solo sumamos los del nivel 4 (los movimientos reales base) PARA EVITAR DUPLICIDAD
                # O sumamos nivel 1. Arisméticamente es igual. Usaremos Nivel 4 para cuadre.
                if nodo["nivel"] == 4:
                    gran_total_debito += nodo["total_debito"]
                    gran_total_credito += nodo["total_credito"]

        # Ordenar estrictamente por código (1, 11, 1105, 1110, 12...)
        lista_final.sort(key=lambda x: x["cuenta_codigo"])

        # Separar resumen por clase (Nivel 1) para la tabla final
        resumen_clase = [n for n in lista_final if n["nivel"] == 1]

        return {
            "cuentas": lista_final, # Contiene niveles 1, 2 y 4 mezclados, ordenados
            "resumen_por_clase": resumen_clase,
            "totales_generales": {
                "debito": gran_total_debito,
                "credito": gran_total_credito
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar los datos del Libro Mayor y Balances: {str(e)}"
        )

def generate_libro_mayor_y_balances_pdf(
    db: Session,
    empresa_id: int,
    fecha_inicio: date,
    fecha_fin: date
):
    report_data = get_data_for_libro_mayor_y_balances(db, empresa_id, fecha_inicio, fecha_fin)
    empresa_info = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    if not empresa_info:
        raise HTTPException(status_code=404, detail=f"No se encontró la empresa con ID {empresa_id}")
    
    # Nota: Ya no modificamos 'report_data' in-place con claves _val porque la plantilla usa formateo directo Jinja

    context = {
        "empresa_nombre": empresa_info.razon_social,
        "empresa_nit": empresa_info.nit,
        "fecha_inicio": fecha_inicio.strftime('%d/%m/%Y'),
        "fecha_fin": fecha_fin.strftime('%d/%m/%Y'),
        "reporte": report_data
    }
    
    try:
        # USA LA NUEVA VERSIÓN V2 DE LA PLANTILLA
        template_string = TEMPLATES_EMPAQUETADOS['reports/mayor_y_balances_v2.html']
        template = GLOBAL_JINJA_ENV.from_string(template_string)
        rendered_html = template.render(context)
        return HTML(string=rendered_html).write_pdf()
    except KeyError:
        raise HTTPException(status_code=500, detail="La plantilla 'reports/mayor_y_balances_v2.html' no fue encontrada.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el PDF del Libro Mayor: {e}")

def generate_libro_mayor_y_balances_pdf(
    db: Session,
    empresa_id: int,
    fecha_inicio: date,
    fecha_fin: date
):
    report_data = get_data_for_libro_mayor_y_balances(db, empresa_id, fecha_inicio, fecha_fin)
    empresa_info = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    if not empresa_info:
        raise HTTPException(status_code=404, detail=f"No se encontró la empresa con ID {empresa_id}")
    
    for cuenta in report_data.get("cuentas", []):
        cuenta['saldo_inicial_val'] = cuenta.get('saldo_inicial', 0)
        cuenta['total_debito_val'] = cuenta.get('total_debito', 0)
        cuenta['total_credito_val'] = cuenta.get('total_credito', 0)
        cuenta['nuevo_saldo_val'] = cuenta.get('nuevo_saldo', 0)
        for mov in cuenta.get("movimientos", []):
            mov['debito_val'] = mov.get('debito', 0)
            mov['credito_val'] = mov.get('credito', 0)

    context = {
        "empresa_nombre": empresa_info.razon_social,
        "empresa_nit": empresa_info.nit,
        "fecha_inicio": fecha_inicio.strftime('%d/%m/%Y'),
        "fecha_fin": fecha_fin.strftime('%d/%m/%Y'),
        "reporte": report_data
    }
    
    try:
        template_string = TEMPLATES_EMPAQUETADOS['reports/mayor_y_balances_report.html']
        template = GLOBAL_JINJA_ENV.from_string(template_string)
        rendered_html = template.render(context)
        return HTML(string=rendered_html).write_pdf()
    except KeyError:
        raise HTTPException(status_code=500, detail="La plantilla 'reports/mayor_y_balances_report.html' no fue encontrada.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el PDF del Libro Mayor: {e}")

def generate_balance_sheet_report(db: Session, empresa_id: int, fecha_corte: date):
    saldos_query = db.query(
        models_plan.codigo,
        models_plan.nombre,
        func.sum(models_mov.debito - models_mov.credito).label('saldo')
    ).join(models_mov, models_plan.id == models_mov.cuenta_id)\
     .join(models_doc, models_mov.documento_id == models_doc.id)\
     .filter(
        models_doc.empresa_id == empresa_id,
        models_doc.fecha <= fecha_corte,
        models_doc.anulado == False,
        or_(
            models_plan.codigo.startswith('1'), 
            models_plan.codigo.startswith('2'), 
            models_plan.codigo.startswith('3'), 
            models_plan.codigo.startswith('4'), 
            models_plan.codigo.startswith('5'), 
            models_plan.codigo.startswith('6'), 
        )
     ).group_by(models_plan.codigo, models_plan.nombre).all()

    activos, pasivos, patrimonio = [], [], []
    total_ingresos, total_costos, total_gastos = 0.0, 0.0, 0.0

    for cuenta in saldos_query:
        saldo = float(cuenta.saldo)
        if cuenta.codigo.startswith('1'):
            activos.append({'codigo': cuenta.codigo, 'nombre': cuenta.nombre, 'saldo': saldo})
        elif cuenta.codigo.startswith('2'):
            pasivos.append({'codigo': cuenta.codigo, 'nombre': cuenta.nombre, 'saldo': -saldo}) 
        elif cuenta.codigo.startswith('3'):
            patrimonio.append({'codigo': cuenta.codigo, 'nombre': cuenta.nombre, 'saldo': -saldo}) 
        elif cuenta.codigo.startswith('4'):
            total_ingresos += -saldo 
        elif cuenta.codigo.startswith('5'):
            total_gastos += saldo
        elif cuenta.codigo.startswith('6'):
            total_costos += saldo
            
    utilidad_ejercicio = total_ingresos - total_costos - total_gastos

    total_activos = sum(c['saldo'] for c in activos)
    total_pasivos = sum(c['saldo'] for c in pasivos)
    total_patrimonio = sum(c['saldo'] for c in patrimonio) + utilidad_ejercicio
    
    return {
        "activos": sorted(activos, key=lambda x: x['codigo']),
        "pasivos": sorted(pasivos, key=lambda x: x['codigo']),
        "patrimonio": sorted(patrimonio, key=lambda x: x['codigo']),
        "total_activos": total_activos,
        "total_pasivos": total_pasivos,
        "total_patrimonio": total_patrimonio,
        "utilidad_ejercicio": utilidad_ejercicio,
        "total_pasivo_patrimonio": total_pasivos + total_patrimonio,
    }

def get_data_for_inventarios_y_balances(
    db: Session,
    empresa_id: int,
    fecha_corte: date
) -> Dict[str, Any]:
    try:
        report_data = generate_balance_sheet_report(
            db=db,
            empresa_id=empresa_id,
            fecha_corte=fecha_corte
        )
        return report_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar los datos del Libro de Inventarios y Balances: {str(e)}"
        )
        
def generate_inventarios_y_balances_pdf(
    db: Session,
    empresa_id: int,
    fecha_corte: date
):
    report_data = get_data_for_inventarios_y_balances(db, empresa_id, fecha_corte)
    empresa_info = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    if not empresa_info:
        raise HTTPException(status_code=404, detail=f"No se encontró la empresa con ID {empresa_id}")
    context = {
        "empresa": empresa_info,
        "fecha_corte": fecha_corte,
        "reporte": report_data
    }
    try:
        template_string = TEMPLATES_EMPAQUETADOS['reports/inventarios_y_balances_report.html']
        template = GLOBAL_JINJA_ENV.from_string(template_string)
        rendered_html = template.render(context)
        return HTML(string=rendered_html).write_pdf()
    except KeyError:
        raise HTTPException(status_code=500, detail="La plantilla 'reports/inventarios_y_balances_report.html' no fue encontrada.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el PDF del Libro de Inventarios: {e}")

# --- NUEVO: LIBRO DIARIO RESUMEN (POR TIPO DE DOCUMENTO) ---
def get_data_for_libro_diario_resumen(
    db: Session,
    empresa_id: int,
    fecha_inicio: date,
    fecha_fin: date,
    tipos_documento_ids: Optional[List[int]] = None
) -> List[Dict[str, Any]]:
    """
    Obtiene los movimientos agrupados por Tipo de Documento.
    Se suman los dÃ©bitos y crÃ©ditos por cuenta para cada tipo de documento en el rango.
    """
    try:
        # Base Query
        query = db.query(
            models_tipo.nombre.label("tipo_documento_nombre"),
            models_plan.codigo.label("cuenta_codigo"),
            models_plan.nombre.label("cuenta_nombre"),
            func.sum(models_mov.debito).label("total_debito"),
            func.sum(models_mov.credito).label("total_credito")
        ).join(models_doc, models_mov.documento_id == models_doc.id)\
         .join(models_tipo, models_doc.tipo_documento_id == models_tipo.id)\
         .join(models_plan, models_mov.cuenta_id == models_plan.id)\
         .filter(
            models_doc.empresa_id == empresa_id,
            models_doc.fecha.between(fecha_inicio, fecha_fin),
            models_doc.anulado == False
        )

        # Filtro opcional por lista de IDs de tipos de documento
        if tipos_documento_ids:
            query = query.filter(models_doc.tipo_documento_id.in_(tipos_documento_ids))

        # AgrupaciÃ³n
        query = query.group_by(
            models_tipo.nombre,
            models_plan.codigo,
            models_plan.nombre
        ).order_by(models_tipo.nombre, models_plan.codigo)

        results = query.all()

        # Estructurar respuesta agrupada por Tipo de Documento
        agrupado = {}
        for row in results:
            tipo = row.tipo_documento_nombre
            if tipo not in agrupado:
                agrupado[tipo] = {
                    "tipo_documento": tipo,
                    "cuentas": [],
                    "total_debito_grupo": 0.0,
                    "total_credito_grupo": 0.0
                }
            
            deb = float(row.total_debito or 0)
            cred = float(row.total_credito or 0)
            
            agrupado[tipo]["cuentas"].append({
                "cuenta_codigo": row.cuenta_codigo,
                "cuenta_nombre": row.cuenta_nombre,
                "debito": deb,
                "credito": cred
            })
            agrupado[tipo]["total_debito_grupo"] += deb
            agrupado[tipo]["total_credito_grupo"] += cred

        return list(agrupado.values())

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar datos del Resumen Diario: {str(e)}")

def generate_libro_diario_resumen_pdf(
    db: Session,
    empresa_id: int,
    fecha_inicio: date,
    fecha_fin: date,
    tipos_documento_ids: Optional[List[int]] = None
):
    report_data = get_data_for_libro_diario_resumen(db, empresa_id, fecha_inicio, fecha_fin, tipos_documento_ids)
    
    empresa_info = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    if not empresa_info:
        raise HTTPException(status_code=404, detail=f"No se encontrÃ³ la empresa con ID {empresa_id}")

    # Calcular Gran Total
    gran_total_debito = sum(g['total_debito_grupo'] for g in report_data)
    gran_total_credito = sum(g['total_credito_grupo'] for g in report_data)

    context = {
        "empresa_nombre": empresa_info.razon_social,
        "empresa_nit": empresa_info.nit,
        "fecha_inicio": fecha_inicio.strftime('%d/%m/%Y'),
        "fecha_fin": fecha_fin.strftime('%d/%m/%Y'),
        "report_data": report_data,
        "gran_total_debito": gran_total_debito,
        "gran_total_credito": gran_total_credito
    }
    
    try:
        template_string = TEMPLATES_EMPAQUETADOS.get('reports/journal_summary_report.html')
        if not template_string:
             # Fallback: Read from file if not packaged yet (dev mode)
             import os
             base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
             template_path = os.path.join(base_dir, 'templates', 'reports', 'journal_summary_report.html')
             with open(template_path, 'r', encoding='utf-8') as f:
                 template_string = f.read()

        template = GLOBAL_JINJA_ENV.from_string(template_string)
        rendered_html = template.render(context)
        return HTML(string=rendered_html).write_pdf()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el PDF del Resumen Diario: {e}")

def get_data_for_analisis_cuenta_por_documento(
    db: Session,
    empresa_id: int,
    fecha_inicio: date,
    fecha_fin: date,
    cuenta_filtro: Optional[str] = None
) -> Dict[str, Any]:
    """
    Obtiene datos para el Análisis de Cuenta por Documento.
    Agrupa los movimientos por Tipo de Documento dentro de cada Cuenta.
    Usa consultas masivas para eficiencia.
    """
    # 0. Filtros comunes
    filters_common = [models_plan.empresa_id == empresa_id, models_plan.permite_movimiento == True]
    if cuenta_filtro:
        filters_common.append(
            or_(models_plan.codigo.ilike(f"{cuenta_filtro}%"), models_plan.nombre.ilike(f"%{cuenta_filtro}%"))
        )

    # 1. Saldos Iniciales Bulk (Fecha < Inicio)
    sq_saldo_ini = db.query(
        models_mov.cuenta_id,
        func.sum(models_mov.debito - models_mov.credito).label("saldo_inicial")
    ).join(models_doc, models_mov.documento_id == models_doc.id).join(models_plan, models_mov.cuenta_id == models_plan.id).filter(
        models_doc.empresa_id == empresa_id,
        models_doc.fecha < fecha_inicio,
        models_doc.anulado.is_(False),
        *filters_common
    ).group_by(models_mov.cuenta_id).all()
    
    mapa_saldos_ini = {r.cuenta_id: float(r.saldo_inicial or 0) for r in sq_saldo_ini}

    # 2. Movimientos Agrupados Bulk (En Rango)
    sq_movs = db.query(
        models_mov.cuenta_id,
        models_tipo.codigo.label("tipo_codigo"),
        models_tipo.nombre.label("tipo_nombre"),
        func.sum(models_mov.debito).label("total_debito"),
        func.sum(models_mov.credito).label("total_credito")
    ).join(models_doc, models_mov.documento_id == models_doc.id).join(models_tipo, models_doc.tipo_documento_id == models_tipo.id).join(models_plan, models_mov.cuenta_id == models_plan.id).filter(
        models_doc.empresa_id == empresa_id,
        models_doc.fecha.between(fecha_inicio, fecha_fin),
        models_doc.anulado.is_(False),
        *filters_common
    ).group_by(models_mov.cuenta_id, models_tipo.id, models_tipo.codigo, models_tipo.nombre).all()
    
    mapa_movs = {} # cuenta_id -> list[dicts]
    for r in sq_movs:
        if r.cuenta_id not in mapa_movs: mapa_movs[r.cuenta_id] = []
        mapa_movs[r.cuenta_id].append({
            "tipo_codigo": r.tipo_codigo,
            "tipo_nombre": r.tipo_nombre,
            "debito": float(r.total_debito or 0),
            "credito": float(r.total_credito or 0)
        })

    # 3. Obtener info de Cuentas (Union de Keys)
    all_account_ids = set(mapa_saldos_ini.keys()) | set(mapa_movs.keys())
    
    if not all_account_ids:
         return {"cuentas": [], "totales_generales": {"debito": 0, "credito": 0}}
    
    cuentas_info = db.query(models_plan).filter(models_plan.id.in_(all_account_ids)).all()
    mapa_cuentas = {c.id: c for c in cuentas_info}

    report_data = []
    gran_total_debito = 0.0
    gran_total_credito = 0.0

    # Procesar resultados
    # Ordenar por código (ya que all_account_ids es set desordenado)
    sorted_ids = sorted(all_account_ids, key=lambda x: mapa_cuentas[x].codigo if x in mapa_cuentas else "")

    for cid in sorted_ids:
        cuenta = mapa_cuentas.get(cid)
        if not cuenta: continue

        saldo_ini = mapa_saldos_ini.get(cid, 0.0)
        movs = mapa_movs.get(cid, [])
        
        # Saltar si no hay actividad ni saldo (aunque el set all_account_ids ya filtra esto implícitamente)
        if abs(saldo_ini) < 0.001 and not movs:
            continue

        total_deb_cuenta = sum(m['debito'] for m in movs)
        total_cred_cuenta = sum(m['credito'] for m in movs)
        nuevo_saldo = saldo_ini + (total_deb_cuenta - total_cred_cuenta)
        
        report_data.append({
            "cuenta_id": cuenta.id,
            "cuenta_codigo": cuenta.codigo,
            "cuenta_nombre": cuenta.nombre,
            "saldo_inicial": saldo_ini,
            "movimientos_por_tipo": sorted(movs, key=lambda x: x['tipo_codigo']),
            "total_debito": total_deb_cuenta,
            "total_credito": total_cred_cuenta,
            "nuevo_saldo": nuevo_saldo
        })

        gran_total_debito += total_deb_cuenta
        gran_total_credito += total_cred_cuenta

    return {
        "cuentas": report_data,
        "totales_generales": {
            "debito": gran_total_debito,
            "credito": gran_total_credito
        }
    }

def generate_analisis_cuenta_por_documento_pdf(
    db: Session,
    empresa_id: int,
    fecha_inicio: date,
    fecha_fin: date,
    cuenta_filtro: Optional[str] = None
):
    report_data = get_data_for_analisis_cuenta_por_documento(db, empresa_id, fecha_inicio, fecha_fin, cuenta_filtro)
    
    empresa_info = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    if not empresa_info:
        raise HTTPException(status_code=404, detail=f"No se encontrÃ³ la empresa con ID {empresa_id}")

    context = {
        "empresa_nombre": empresa_info.razon_social,
        "empresa_nit": empresa_info.nit,
        "fecha_inicio": fecha_inicio.strftime('%d/%m/%Y'),
        "fecha_fin": fecha_fin.strftime('%d/%m/%Y'),
        "reporte": report_data
    }
    
    try:
        template_string = TEMPLATES_EMPAQUETADOS.get('reports/analisis_cuenta_doc_report.html')
        if not template_string:
             import os
             base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
             template_path = os.path.join(base_dir, 'templates', 'reports', 'analisis_cuenta_doc_report.html')
             with open(template_path, 'r', encoding='utf-8') as f:
                 template_string = f.read()

        template = GLOBAL_JINJA_ENV.from_string(template_string)
        rendered_html = template.render(context)
        return HTML(string=rendered_html).write_pdf()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el PDF de AnÃ¡lisis de Cuentas: {e}")
    
