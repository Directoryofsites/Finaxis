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
    tipo_documento_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Obtiene una lista plana de movimientos contables para la tabla del Libro Diario en el frontend.
    """
    try:
        query = db.query(
            models_doc.fecha,
            models_tipo.nombre.label("tipo_documento"),
            models_doc.numero.label("numero_documento"),
            models_tercero.razon_social.label("beneficiario_nombre"),
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

        if tipo_documento_id:
            query = query.filter(models_doc.tipo_documento_id == tipo_documento_id)

        movimientos_raw = query.order_by(models_doc.fecha, models_doc.numero, models_mov.id).all()

        report_data = [
            {
                "fecha": mov.fecha,
                "tipo_documento": mov.tipo_documento,
                "numero_documento": mov.numero_documento,
                "beneficiario_nombre": mov.beneficiario_nombre or "N/A",
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
    tipo_documento_id: Optional[int] = None
):
    """
    Genera el archivo PDF para el reporte del Libro Diario, construyendo la estructura
    de datos exacta que la plantilla journal_report.html espera.
    """
    movimientos_planos = get_data_for_libro_diario(db, empresa_id, fecha_inicio, fecha_fin, tipo_documento_id)
    
    report_data_agrupado = {}
    total_debito = 0.0
    total_credito = 0.0

    for mov in movimientos_planos:
        fecha_str = mov['fecha'].strftime('%Y-%m-%d')
        if fecha_str not in report_data_agrupado:
            report_data_agrupado[fecha_str] = []
        
        report_data_agrupado[fecha_str].append(mov)
        
        total_debito += mov['debito']
        total_credito += mov['credito']
    
    empresa_info = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    if not empresa_info:
        raise HTTPException(status_code=404, detail=f"No se encontró la empresa con ID {empresa_id}")

    context = {
        "empresa_nombre": empresa_info.razon_social,
        "empresa_nit": empresa_info.nit,
        "fecha_inicio": fecha_inicio.strftime('%d/%m/%Y'),
        "fecha_fin": fecha_fin.strftime('%d/%m/%Y'),
        "report_data_agrupado": report_data_agrupado,
        "total_debito": total_debito,
        "total_credito": total_credito
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
        saldos_iniciales_query = db.query(
            models_mov.cuenta_id,
            func.sum(models_mov.debito - models_mov.credito).label("saldo_inicial")
        ).join(models_doc, models_mov.documento_id == models_doc.id) \
        .filter(
            models_doc.empresa_id == empresa_id,
            models_doc.fecha < fecha_inicio,
            models_doc.anulado.is_(False)
        ).group_by(models_mov.cuenta_id).all()
        saldos_iniciales_map = {row.cuenta_id: float(row.saldo_inicial or 0.0) for row in saldos_iniciales_query}
        movimientos_periodo_query = db.query(
            models_plan.id.label("cuenta_id"),
            models_plan.codigo.label("cuenta_codigo"),
            models_plan.nombre.label("cuenta_nombre"),
            models_doc.fecha,
            models_tipo.codigo.label("tipo_doc_codigo"),
            models_doc.numero,
            models_tercero.razon_social.label("beneficiario"),
            models_mov.concepto,
            models_mov.debito,
            models_mov.credito
        ).join(models_doc, models_mov.documento_id == models_doc.id) \
        .join(models_plan, models_mov.cuenta_id == models_plan.id) \
        .join(models_tipo, models_doc.tipo_documento_id == models_tipo.id) \
        .outerjoin(models_tercero, models_doc.beneficiario_id == models_tercero.id) \
        .filter(
            models_doc.empresa_id == empresa_id,
            models_doc.fecha.between(fecha_inicio, fecha_fin),
            models_doc.anulado.is_(False)
        ).order_by(models_plan.codigo, models_doc.fecha, models_doc.numero)
        movimientos_del_periodo = movimientos_periodo_query.all()
        cuentas_procesadas = {}
        for mov in movimientos_del_periodo:
            cuenta_id = mov.cuenta_id
            if cuenta_id not in cuentas_procesadas:
                saldo_inicial = saldos_iniciales_map.get(cuenta_id, 0.0)
                cuentas_procesadas[cuenta_id] = {
                    "cuenta_codigo": mov.cuenta_codigo,
                    "cuenta_nombre": mov.cuenta_nombre,
                    "saldo_inicial": saldo_inicial,
                    "movimientos": [],
                    "total_debito": 0.0,
                    "total_credito": 0.0,
                    "nuevo_saldo": saldo_inicial
                }
            cuentas_procesadas[cuenta_id]["movimientos"].append({
                "fecha": mov.fecha,
                "documento": f"{mov.tipo_doc_codigo}-{mov.numero}",
                "beneficiario": mov.beneficiario,
                "concepto": mov.concepto,
                "debito": float(mov.debito or 0),
                "credito": float(mov.credito or 0),
            })
            cuentas_procesadas[cuenta_id]["total_debito"] += float(mov.debito or 0)
            cuentas_procesadas[cuenta_id]["total_credito"] += float(mov.credito or 0)
            cuentas_procesadas[cuenta_id]["nuevo_saldo"] += float(mov.debito or 0) - float(mov.credito or 0)
        gran_total_debito = sum(cuenta["total_debito"] for cuenta in cuentas_procesadas.values())
        gran_total_credito = sum(cuenta["total_credito"] for cuenta in cuentas_procesadas.values())
        return {
            "cuentas": list(cuentas_procesadas.values()),
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
    
