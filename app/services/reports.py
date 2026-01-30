# -*- coding: utf-8 -*-
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import os
from sqlalchemy.orm import Session
from sqlalchemy import func
import math

# --- INICIO: CORRECCIÓN ---
# Se añade la importación faltante de HTTPException
from fastapi import HTTPException
# --- FIN: CORRECCIÓN ---

from fastapi.responses import Response
from weasyprint import HTML

from app.services._templates_empaquetados import TEMPLATES_EMPAQUETADOS
from jinja2 import Environment, select_autoescape

GLOBAL_JINJA_ENV = Environment(loader=None, autoescape=select_autoescape(['html', 'xml']))

from ..models import PlanCuenta, MovimientoContable, Documento, Empresa as models_empresa, Tercero
from ..schemas import reporte_balance_prueba as schemas_bce

from ..models import CentroCosto
from ..schemas import reporte_balance_prueba_cc as schemas_bce_cc
from sqlalchemy import text, and_, literal


SECRET_KEY_REPORTS = os.environ.get("SECRET_KEY_REPORTS", "un-secret-muy-largo-y-seguro-para-reportes-pdf-que-cambia-en-prod-1234567890abcdef")
url_signer = URLSafeTimedSerializer(SECRET_KEY_REPORTS)

def generate_signed_report_url(endpoint: str, expiration_seconds: int, **kwargs: Any) -> str:
    # (Esta función no necesita cambios)
    expires_at = datetime.utcnow() + timedelta(seconds=expiration_seconds)
    payload = {"exp": expires_at.isoformat(), "endpoint": endpoint, "params": kwargs}
    signed_token = url_signer.dumps(payload)
    return signed_token

def verify_signed_report_url(signed_token: str, expected_endpoint: str, max_age_seconds: int = 300) -> Optional[Dict[str, Any]]:
    # (Esta función no necesita cambios)
    try:
        payload = url_signer.loads(signed_token, max_age=max_age_seconds)
        if "exp" in payload:
            expires_at = datetime.fromisoformat(payload["exp"])
            if datetime.utcnow() > expires_at:
                return None
        if payload.get("endpoint") != expected_endpoint:
            return None
        return payload.get("params")
    except (SignatureExpired, BadTimeSignature, Exception):
        return None

def decode_signed_report_token(signed_token: str, max_age_seconds: int = 300) -> Dict[str, Any]:
    """
    Decodifica el token sin validar el endpoint específico aqui (ya que el endpoint lo usó para generar).
    Lanza excepciones para que la ruta las capture.
    """
    try:
        payload = url_signer.loads(signed_token, max_age=max_age_seconds)
        # Validar expiración explícita
        if "exp" in payload:
            expires_at = datetime.fromisoformat(payload["exp"])
            if datetime.utcnow() > expires_at:
                raise SignatureExpired("El token ha expirado (custom check)")
        
        return payload.get("params", {})
    except SignatureExpired:
        raise HTTPException(status_code=400, detail="El enlace de descarga ha expirado. Genere uno nuevo.")
    except BadTimeSignature:
        raise HTTPException(status_code=400, detail="Firma del enlace inválida.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token inválido: {str(e)}")

# --- LÓGICA PARA EL BALANCE DE PRUEBA POR CUENTAS (Sin cambios) ---
def generate_balance_de_prueba_report(db: Session, empresa_id: int, filtros: schemas_bce.FiltrosBalancePrueba) -> Dict[str, Any]:
    # (El código de esta función no necesita cambios, ya que solo prepara datos)
    cuentas = db.query(PlanCuenta).filter(PlanCuenta.empresa_id == empresa_id).order_by(PlanCuenta.codigo).all()
    cuentas_map = {c.id: {
        "data": schemas_bce.CuentaBalancePrueba(
            codigo=c.codigo, nombre=c.nombre, nivel=c.nivel,
            saldo_inicial=0.0, debito=0.0, credito=0.0, nuevo_saldo=0.0
        ),
        "children": [],
        "parent_id": c.cuenta_padre_id
    } for c in cuentas}
    root_cuentas = []
    for c_id, c_node in cuentas_map.items():
        if c_node['parent_id']:
            if c_node['parent_id'] in cuentas_map:
                cuentas_map[c_node['parent_id']]['children'].append(c_id)
        else:
            root_cuentas.append(c_id)
    saldos_iniciales_q = db.query(
        MovimientoContable.cuenta_id,
        func.sum(MovimientoContable.debito - MovimientoContable.credito).label("saldo_inicial")
    ).join(Documento).filter(
        Documento.empresa_id == empresa_id,
        Documento.fecha < filtros.fecha_inicio,
        Documento.anulado == False
    )
    if filtros.centro_costo_id:
        saldos_iniciales_q = saldos_iniciales_q.filter(MovimientoContable.centro_costo_id == filtros.centro_costo_id)
    saldos_iniciales_q = saldos_iniciales_q.group_by(MovimientoContable.cuenta_id).all()
    for row in saldos_iniciales_q:
        if row.cuenta_id in cuentas_map:
            cuentas_map[row.cuenta_id]['data'].saldo_inicial = float(row.saldo_inicial or 0.0)
    movimientos_periodo_q = db.query(
        MovimientoContable.cuenta_id,
        func.sum(MovimientoContable.debito).label("debito"),
        func.sum(MovimientoContable.credito).label("credito")
    ).join(Documento).filter(
        Documento.empresa_id == empresa_id,
        Documento.fecha.between(filtros.fecha_inicio, filtros.fecha_fin),
        Documento.anulado == False
    )
    if filtros.centro_costo_id:
        movimientos_periodo_q = movimientos_periodo_q.filter(MovimientoContable.centro_costo_id == filtros.centro_costo_id)
    movimientos_periodo_q = movimientos_periodo_q.group_by(MovimientoContable.cuenta_id).all()
    for row in movimientos_periodo_q:
        if row.cuenta_id in cuentas_map:
            cuentas_map[row.cuenta_id]['data'].debito = float(row.debito or 0.0)
            cuentas_map[row.cuenta_id]['data'].credito = float(row.credito or 0.0)
    def sumar_hacia_padre(cuenta_id):
        cuenta_node = cuentas_map[cuenta_id]
        if not cuenta_node['children']:
            cuenta_node['data'].nuevo_saldo = cuenta_node['data'].saldo_inicial + cuenta_node['data'].debito - cuenta_node['data'].credito
            return
        for child_id in cuenta_node['children']:
            sumar_hacia_padre(child_id)
        for child_id in cuenta_node['children']:
            child_node = cuentas_map[child_id]
            cuenta_node['data'].saldo_inicial += child_node['data'].saldo_inicial
            cuenta_node['data'].debito += child_node['data'].debito
            cuenta_node['data'].credito += child_node['data'].credito
        cuenta_node['data'].nuevo_saldo = cuenta_node['data'].saldo_inicial + cuenta_node['data'].debito - cuenta_node['data'].credito
    for root_id in root_cuentas:
        sumar_hacia_padre(root_id)
    filas_reporte = []
    def aplanar(cuenta_id):
        cuenta_node = cuentas_map[cuenta_id]
        tiene_movimiento = cuenta_node['data'].debito != 0 or cuenta_node['data'].credito != 0
        tiene_saldo = cuenta_node['data'].saldo_inicial != 0 or cuenta_node['data'].nuevo_saldo != 0
        mostrar = False
        if filtros.filtro_cuentas == 'TODAS':
            mostrar = True
        elif filtros.filtro_cuentas == 'CON_MOVIMIENTO':
            if tiene_movimiento: mostrar = True
        elif filtros.filtro_cuentas == 'CON_SALDO_O_MOVIMIENTO':
            if tiene_movimiento or tiene_saldo: mostrar = True
        if mostrar and cuenta_node['data'].nivel <= filtros.nivel_maximo:
            filas_reporte.append(cuenta_node['data'])
        for child_id in sorted(cuenta_node['children'], key=lambda id: cuentas_map[id]['data'].codigo):
            aplanar(child_id)
    for root_id in sorted(root_cuentas, key=lambda id: cuentas_map[id]['data'].codigo):
        aplanar(root_id)
    totales = schemas_bce.TotalesBalancePrueba(saldo_inicial=0, debito=0, credito=0, nuevo_saldo=0)
    for fila in filas_reporte:
        if fila.nivel == 1:
            totales.saldo_inicial += fila.saldo_inicial
            totales.debito += fila.debito
            totales.credito += fila.credito
    totales.nuevo_saldo = totales.saldo_inicial + totales.debito - totales.credito
    return {"filas": filas_reporte, "totales": totales}


# --- LÓGICA PARA EL BALANCE DE PRUEBA POR CC (Sin cambios) ---
def generate_balance_de_prueba_cc_report(db: Session, empresa_id: int, filtros: schemas_bce_cc.FiltrosBalancePruebaCC) -> Dict[str, Any]:
    # (El código de esta función no necesita cambios, ya que solo prepara datos)
    centros_costo = db.query(CentroCosto).filter(CentroCosto.empresa_id == empresa_id).order_by(CentroCosto.codigo).all()
    cc_map = {cc.id: {
        "data": schemas_bce_cc.CentroCostoBalancePrueba(
            codigo=cc.codigo, nombre=cc.nombre, nivel=cc.nivel,
            saldo_inicial=0.0, debito=0.0, credito=0.0, nuevo_saldo=0.0
        ),
        "children": [],
        "parent_id": cc.centro_costo_padre_id
    } for cc in centros_costo}
    root_ccs = []
    for cc_id, cc_node in cc_map.items():
        if cc_node['parent_id']:
            if cc_node['parent_id'] in cc_map:
                cc_map[cc_node['parent_id']]['children'].append(cc_id)
        else:
            root_ccs.append(cc_id)
    saldos_iniciales_q = db.query(
        MovimientoContable.centro_costo_id,
        func.sum(MovimientoContable.debito - MovimientoContable.credito).label("saldo_inicial")
    ).join(Documento).filter(
        Documento.empresa_id == empresa_id,
        Documento.fecha < filtros.fecha_inicio,
        Documento.anulado == False,
        MovimientoContable.centro_costo_id != None
    )
    if filtros.cuenta_id:
        saldos_iniciales_q = saldos_iniciales_q.filter(MovimientoContable.cuenta_id == filtros.cuenta_id)
    saldos_iniciales_q = saldos_iniciales_q.group_by(MovimientoContable.centro_costo_id).all()
    for row in saldos_iniciales_q:
        if row.centro_costo_id in cc_map:
            cc_map[row.centro_costo_id]['data'].saldo_inicial = float(row.saldo_inicial or 0.0)
    movimientos_periodo_q = db.query(
        MovimientoContable.centro_costo_id,
        func.sum(MovimientoContable.debito).label("debito"),
        func.sum(MovimientoContable.credito).label("credito")
    ).join(Documento).filter(
        Documento.empresa_id == empresa_id,
        Documento.fecha.between(filtros.fecha_inicio, filtros.fecha_fin),
        Documento.anulado == False,
        MovimientoContable.centro_costo_id != None
    )
    if filtros.cuenta_id:
        movimientos_periodo_q = movimientos_periodo_q.filter(MovimientoContable.cuenta_id == filtros.cuenta_id)
    movimientos_periodo_q = movimientos_periodo_q.group_by(MovimientoContable.centro_costo_id).all()
    for row in movimientos_periodo_q:
        if row.centro_costo_id in cc_map:
            cc_map[row.centro_costo_id]['data'].debito = float(row.debito or 0.0)
            cc_map[row.centro_costo_id]['data'].credito = float(row.credito or 0.0)
    def sumar_hacia_padre(cc_id):
        cc_node = cc_map[cc_id]
        if not cc_node['children']:
            cc_node['data'].nuevo_saldo = cc_node['data'].saldo_inicial + cc_node['data'].debito - cc_node['data'].credito
            return
        for child_id in cc_node['children']:
            sumar_hacia_padre(child_id)
        for child_id in cc_node['children']:
            child_node = cc_map[child_id]
            cc_node['data'].saldo_inicial += child_node['data'].saldo_inicial
            cc_node['data'].debito += child_node['data'].debito
            cc_node['data'].credito += child_node['data'].credito
        cc_node['data'].nuevo_saldo = cc_node['data'].saldo_inicial + cc_node['data'].debito - cc_node['data'].credito
    for root_id in root_ccs:
        sumar_hacia_padre(root_id)
    filas_reporte = []
    def aplanar(cc_id):
        cc_node = cc_map[cc_id]
        tiene_movimiento = cc_node['data'].debito != 0 or cc_node['data'].credito != 0
        tiene_saldo = cc_node['data'].saldo_inicial != 0 or cc_node['data'].nuevo_saldo != 0
        mostrar = False
        if filtros.filtro_centros_costo == 'TODAS':
            mostrar = True
        elif filtros.filtro_centros_costo == 'CON_MOVIMIENTO':
            if tiene_movimiento: mostrar = True
        elif filtros.filtro_centros_costo == 'CON_SALDO_O_MOVIMIENTO':
            if tiene_movimiento or tiene_saldo: mostrar = True
        if mostrar and cc_node['data'].nivel <= filtros.nivel_maximo:
            filas_reporte.append(cc_node['data'])
        for child_id in sorted(cc_node['children'], key=lambda id: cc_map[id]['data'].codigo):
            aplanar(child_id)
    for root_id in sorted(root_ccs, key=lambda id: cc_map[id]['data'].codigo):
        aplanar(root_id)
    totales = schemas_bce_cc.TotalesBalancePruebaCC(saldo_inicial=0, debito=0, credito=0, nuevo_saldo=0)
    for fila in filas_reporte:
        if fila.nivel == 1:
            totales.saldo_inicial += fila.saldo_inicial
            totales.debito += fila.debito
            totales.credito += fila.credito
    totales.nuevo_saldo = totales.saldo_inicial + totales.debito - totales.credito
    return {"filas": filas_reporte, "totales": totales}


# --- FUNCIÓN PDF PARA BALANCE DE PRUEBA POR CUENTAS (REFACTORIZADA) ---
def generate_balance_de_prueba_pdf(db: Session, empresa_id: int, filtros: schemas_bce.FiltrosBalancePrueba):
    report_data = generate_balance_de_prueba_report(db, empresa_id, filtros)

    empresa_info = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    periodo_str = f"Del {filtros.fecha_inicio.strftime('%d/%m/%Y')} al {filtros.fecha_fin.strftime('%d/%m/%Y')}"

    context = {
        'filas': report_data['filas'],
        'totales': report_data['totales'],
        'empresa': empresa_info,
        'periodo': periodo_str,
        'titulo_reporte': "Balance de Prueba"
    }

    try:
        template_string = TEMPLATES_EMPAQUETADOS["reports/balance_de_prueba_report.html"]
        template = GLOBAL_JINJA_ENV.from_string(template_string)
        html_string = template.render(context)
        pdf_content = HTML(string=html_string).write_pdf()
        return Response(content=pdf_content, media_type="application/pdf")
    except KeyError:
        raise HTTPException(status_code=500, detail="La plantilla 'reports/balance_de_prueba_report.html' no fue encontrada en el paquete.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el PDF de Balance de Prueba: {e}")


# --- FUNCIÓN PDF PARA BALANCE DE PRUEBA POR CC (REFACTORIZADA) ---
def generate_balance_de_prueba_cc_pdf(db: Session, empresa_id: int, filtros: schemas_bce_cc.FiltrosBalancePruebaCC):
    report_data = generate_balance_de_prueba_cc_report(db, empresa_id, filtros)

    empresa_info = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    periodo_str = f"Del {filtros.fecha_inicio.strftime('%d/%m/%Y')} al {filtros.fecha_fin.strftime('%d/%m/%Y')}"

    cuenta_info = None
    if filtros.cuenta_id:
        cuenta_filtrada = db.query(PlanCuenta).filter(PlanCuenta.id == filtros.cuenta_id).first()
        if cuenta_filtrada:
            cuenta_info = {
                "codigo": cuenta_filtrada.codigo,
                "nombre": cuenta_filtrada.nombre
            }

    context = {
        'filas': report_data['filas'],
        'totales': report_data['totales'],
        'empresa': empresa_info,
        'periodo': periodo_str,
        'titulo_reporte': "Balance de Prueba por Centro de Costo",
        'cuenta_info': cuenta_info
    }

    try:
        template_string = TEMPLATES_EMPAQUETADOS["reports/balance_de_prueba_cc_report.html"]
        template = GLOBAL_JINJA_ENV.from_string(template_string)
        html_string = template.render(context)
        pdf_content = HTML(string=html_string).write_pdf()
        return Response(content=pdf_content, media_type="application/pdf")
    except KeyError:
        raise HTTPException(status_code=500, detail="La plantilla 'reports/balance_de_prueba_cc_report.html' no fue encontrada en el paquete.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el PDF de Balance de Prueba por CC: {e}")

# --- REPORTE: RELACIÓN DE SALDOS (CUENTAS Y TERCEROS) ---
def generate_relacion_saldos_report(db: Session, empresa_id: int, filtros: Dict[str, Any]) -> List[Dict[str, Any]]:
    # 1. Filtros Básicos
    fecha_inicio = filtros['fecha_inicio']
    fecha_fin = filtros['fecha_fin']
    
    # 2. Query Base (Tercero x Cuenta)
    # Necesitamos: Saldo Anterior, Movimientos (Deb/Cred), Saldo Final
    
    # ESTRATEGIA SIMPLIFICADA (UNION ALL + GROUP BY)
    # Evita problemas de mapeo de columnas en CTEs complejos y uniones.
    
    # 1. Saldos Anteriores (Saldo Prev)
    # 1. Saldos Anteriores (Saldo Prev)
    q1 = db.query(
        MovimientoContable.cuenta_id.label("cuenta_id"),
        Documento.beneficiario_id.label("tercero_id"),
        func.sum(MovimientoContable.debito - MovimientoContable.credito).label("saldo_anterior"),
        literal(0).label("debito"),
        literal(0).label("credito")
    ).select_from(MovimientoContable).join(Documento).filter(
        Documento.empresa_id == empresa_id,
        Documento.fecha < fecha_inicio,
        Documento.anulado == False,
        Documento.beneficiario_id != None
    )
    if filtros.get('cuenta_ids'): q1 = q1.filter(MovimientoContable.cuenta_id.in_(filtros['cuenta_ids']))
    if filtros.get('tercero_ids'): q1 = q1.filter(Documento.beneficiario_id.in_(filtros['tercero_ids']))
    q1 = q1.group_by(MovimientoContable.cuenta_id, Documento.beneficiario_id)

    # 2. Movimientos del Periodo (Debito/Credito)
    q2 = db.query(
        MovimientoContable.cuenta_id.label("cuenta_id"),
        Documento.beneficiario_id.label("tercero_id"),
        literal(0).label("saldo_anterior"),
        func.sum(MovimientoContable.debito).label("debito"),
        func.sum(MovimientoContable.credito).label("credito")
    ).select_from(MovimientoContable).join(Documento).filter(
        Documento.empresa_id == empresa_id,
        Documento.fecha.between(fecha_inicio, fecha_fin),
        Documento.anulado == False,
        Documento.beneficiario_id != None
    )
    if filtros.get('cuenta_ids'): q2 = q2.filter(MovimientoContable.cuenta_id.in_(filtros['cuenta_ids']))
    if filtros.get('tercero_ids'): q2 = q2.filter(Documento.beneficiario_id.in_(filtros['tercero_ids']))
    q2 = q2.group_by(MovimientoContable.cuenta_id, Documento.beneficiario_id)

    # 3. Union y Agrupación Final
    union_q = q1.union_all(q2).subquery("union_movs")

    query_final = db.query(
        union_q.c.cuenta_id,
        union_q.c.tercero_id,
        func.sum(union_q.c.saldo_anterior).label("saldo_anterior"),
        func.sum(union_q.c.debito).label("debito"),
        func.sum(union_q.c.credito).label("credito"),
        PlanCuenta.codigo.label("cuenta_codigo"),
        PlanCuenta.nombre.label("cuenta_nombre"),
        Tercero.razon_social.label("tercero_nombre"),
        Tercero.nit.label("tercero_nit")
    ).select_from(union_q)\
     .join(PlanCuenta, union_q.c.cuenta_id == PlanCuenta.id)\
     .join(Tercero, union_q.c.tercero_id == Tercero.id)\
     .group_by(
        union_q.c.cuenta_id, union_q.c.tercero_id,
        PlanCuenta.codigo, PlanCuenta.nombre,
        Tercero.razon_social, Tercero.nit
    ).order_by(PlanCuenta.codigo, Tercero.razon_social)
    
    results = query_final.all()
    
    data = []
    for r in results:
        saldo_final = float(r.saldo_anterior) + float(r.debito) - float(r.credito)
        # Solo agregar si tiene algún valor
        if r.saldo_anterior != 0 or r.debito != 0 or r.credito != 0:
            data.append({
                "cuenta_id": r.cuenta_id,
                "cuenta_codigo": r.cuenta_codigo,
                "cuenta_nombre": r.cuenta_nombre,
                "tercero_id": r.tercero_id,
                "tercero_nombre": r.tercero_nombre or f"NIT {r.tercero_nit}",
                "tercero_nit": r.tercero_nit,
                "saldo_anterior": float(r.saldo_anterior),
                "debito": float(r.debito),
                "credito": float(r.credito),
                "saldo_final": saldo_final
            })
            
    return data

def generate_relacion_saldos_pdf(db: Session, empresa_id: int, filtros: Dict[str, Any]):
    # 1. Obtener Datos
    report_data = generate_relacion_saldos_report(db, empresa_id, filtros)
    empresa_info = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    
    # 2. Calcular Totales Generales
    total_saldo_anterior = sum(d['saldo_anterior'] for d in report_data)
    total_debito = sum(d['debito'] for d in report_data)
    total_credito = sum(d['credito'] for d in report_data)
    total_saldo_final = sum(d['saldo_final'] for d in report_data)

    # 3. Datos de Contexto
    context = {
        'empresa': empresa_info,
        'fecha_inicio': filtros['fecha_inicio'].strftime('%d/%m/%Y'),
        'fecha_fin': filtros['fecha_fin'].strftime('%d/%m/%Y'),
        'titulo_reporte': "Relación de Saldos por Cuenta y Tercero",
        'data': report_data,
        'total_anterior': total_saldo_anterior,
        'total_debito': total_debito,
        'total_credito': total_credito,
        'total_final': total_saldo_final
    }

    # 4. Plantilla HTML Profesional
    html_template = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="utf-8">
        <title>Relación de Saldos</title>
        <style>
            @page {
                size: A4 landscape;
                margin: 1cm;
            }
            body { font-family: 'Helvetica', 'Arial', sans-serif; font-size: 9pt; color: #333; margin: 0; padding: 0; }
            .header-container { width: 100%; border-bottom: 2px solid #4f46e5; padding-bottom: 10px; margin-bottom: 15px; }
            .empresa-nombre { font-size: 16pt; font-weight: bold; color: #1e1b4b; text-transform: uppercase; }
            .empresa-nit { font-size: 10pt; color: #666; margin-top: 2px; }
            .reporte-titulo { font-size: 14pt; font-weight: bold; color: #4338ca; margin-top: 10px; text-align: center; }
            .reporte-fechas { font-size: 10pt; font-weight: bold; color: #555; text-align: center; margin-top: 4px; }
            
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            th { 
                background-color: #e0e7ff; 
                color: #312e81; 
                font-weight: bold; 
                padding: 6px; 
                border: 1px solid #c7d2fe; 
                text-align: center;
                font-size: 8pt;
                text-transform: uppercase;
            }
            td { 
                border: 1px solid #e5e7eb; 
                padding: 5px; 
                font-size: 8.5pt;
                vertical-align: middle;
            }
            tr:nth-child(even) { background-color: #f9fafb; }
            .text-right { text-align: right; }
            .text-center { text-align: center; }
            .font-mono { font-family: 'Courier New', Courier, monospace; letter-spacing: -0.5px; }
            .font-bold { font-weight: bold; }
            
            .total-row td { 
                background-color: #312e81; 
                color: white; 
                font-weight: bold; 
                border: 1px solid #312e81;
                font-size: 9pt;
            }
            
            .footer {
                position: fixed; 
                bottom: 0; 
                width: 100%; 
                text-align: center; 
                font-size: 7pt; 
                color: #999;
                border-top: 1px solid #eee;
                padding-top: 5px;
            }
        </style>
    </head>
    <body>
        <div class="header-container">
            <div class="empresa-nombre">{{ empresa.razon_social }}</div>
            <div class="empresa-nit">NIT: {{ empresa.nit }} {% if empresa.dv %}- {{ empresa.dv }}{% endif %}</div>
            <div class="reporte-titulo">{{ titulo_reporte }}</div>
            <div class="reporte-fechas">Del {{ fecha_inicio }} al {{ fecha_fin }}</div>
        </div>

        <table>
            <thead>
                <tr>
                    <th width="10%">Cuenta</th>
                    <th width="20%">Nombre Cuenta</th>
                    <th width="10%">NIT Tercero</th>
                    <th width="20%">Nombre Tercero</th>
                    <th width="10%">Saldo Anterior</th>
                    <th width="10%">Débito</th>
                    <th width="10%">Crédito</th>
                    <th width="10%">Saldo Final</th>
                </tr>
            </thead>
            <tbody>
                {% for row in data %}
                <tr>
                    <td class="text-center font-bold">{{ row.cuenta_codigo }}</td>
                    <td>{{ row.cuenta_nombre }}</td>
                    <td class="text-center">{{ row.tercero_nit }}</td>
                    <td>{{ row.tercero_nombre }}</td>
                    <td class="text-right font-mono">{{ "{:,.2f}".format(row.saldo_anterior) }}</td>
                    <td class="text-right font-mono">{{ "{:,.2f}".format(row.debito) }}</td>
                    <td class="text-right font-mono">{{ "{:,.2f}".format(row.credito) }}</td>
                    <td class="text-right font-mono font-bold">{{ "{:,.2f}".format(row.saldo_final) }}</td>
                </tr>
                {% endfor %}
                <tr class="total-row">
                    <td colspan="4" class="text-right">TOTALES GENERALES</td>
                    <td class="text-right">{{ "{:,.2f}".format(total_anterior) }}</td>
                    <td class="text-right">{{ "{:,.2f}".format(total_debito) }}</td>
                    <td class="text-right">{{ "{:,.2f}".format(total_credito) }}</td>
                    <td class="text-right">{{ "{:,.2f}".format(total_final) }}</td>
                </tr>
            </tbody>
        </table>

        <div class="footer">
            Generado por Sistema Contable | Fecha de Impresión: {{ fecha_fin }}
        </div>
    </body>
    </html>
    """
    
    try:
        template = GLOBAL_JINJA_ENV.from_string(html_template)
        html_string = template.render(context)
        pdf_content = HTML(string=html_string).write_pdf()
        return pdf_content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando PDF Relación Saldos: {e}")


# --- REPORTE: AUXILIAR INVERSO (Cuenta -> Terceros) ---
def generate_auxiliar_inverso_report(db: Session, empresa_id: int, filtros: Dict[str, Any]) -> Dict[str, Any]:
    # Similar al Auxiliar normal, pero agrupado para mostrar detalle
    # Retorna estructura compatible con la página existente, o una nueva si decidimos actualizar frontend.
    # Dado que actualizaremos el frontend para agrupar por tercero cuando sea inverso:
    
    # 1. Recuperar Movimientos
    query = db.query(
        MovimientoContable,
        Documento,
        Tercero.razon_social.label("tercero_nombre"),
        Tercero.id.label("tercero_id_real")
    ).select_from(MovimientoContable)\
     .join(Documento, MovimientoContable.documento_id == Documento.id)\
     .outerjoin(Tercero, Documento.beneficiario_id == Tercero.id)\
     .filter(
        Documento.empresa_id == empresa_id,
        Documento.fecha.between(filtros['fecha_inicio'], filtros['fecha_fin']),
        Documento.anulado == False,
        MovimientoContable.cuenta_id == filtros['cuenta_id']
    )
    
    if filtros.get('tercero_ids'):
        query = query.filter(Documento.beneficiario_id.in_(filtros['tercero_ids']))
        
    query = query.order_by(Tercero.razon_social, Documento.fecha, Documento.numero) # Agrupar visualmente por tercero
    
    raw_movs = query.all()
    
    # 2. Calcular Saldos Iniciales por Tercero
    # Query de saldo inicial filtrado por cuenta y agrupado por tercero
    q_saldos = db.query(
        Documento.beneficiario_id,
        func.sum(MovimientoContable.debito - MovimientoContable.credito).label("saldo")
    ).select_from(MovimientoContable)\
     .join(Documento, MovimientoContable.documento_id == Documento.id)\
     .filter(
        Documento.empresa_id == empresa_id,
        Documento.fecha < filtros['fecha_inicio'],
        Documento.anulado == False,
        MovimientoContable.cuenta_id == filtros['cuenta_id']
    )
    
    if filtros.get('tercero_ids'):
        q_saldos = q_saldos.filter(Documento.beneficiario_id.in_(filtros['tercero_ids']))
        
    q_saldos = q_saldos.group_by(Documento.beneficiario_id).all()
    saldos_iniciales_map = { (r.beneficiario_id or 0): float(r.saldo or 0) for r in q_saldos }
    
    # 3. Construir Respuesta
    # Reusamos la estructura de 'movimientos' plana, pero el frontend agrupará.
    # Para facilitar al frontend, inyectamos "tercero_nombre" y "tercero_id" en el objeto
    
    movimientos_resp = []
    
    # Tracking de saldos parciales por tercero
    running_balances = saldos_iniciales_map.copy()
    
    for mov, doc, t_nombre, t_id in raw_movs:
        tid = t_id or 0
        current_bal = running_balances.get(tid, 0.0)
        new_bal = current_bal + float(mov.debito) - float(mov.credito)
        running_balances[tid] = new_bal
        
        movimientos_resp.append({
            "fecha": doc.fecha.isoformat(),
            "tipo_documento": doc.tipo_documento.codigo if doc.tipo_documento else "DOC",
            "numero_documento": doc.numero,
            "cta_id": mov.cuenta_id, # Redundante
            # Crucial: Frontend usará esto para agrupar
            "tercero_id": tid, 
            "tercero_nombre": t_nombre or "Cuantías Menores",
            
            # Campos estándar
            "cuenta_codigo": mov.cuenta.codigo, # Fijo
            "cuenta_nombre": mov.cuenta.nombre, # Fijo
            "concepto": mov.concepto,
            "debito": float(mov.debito),
            "credito": float(mov.credito),
            "saldo_parcial": new_bal
        })
        
    return {
        "saldoAnterior": sum(saldos_iniciales_map.values()), # Total global (menos util)
        "movimientos": movimientos_resp,
        "saldos_iniciales_por_tercero": {str(k): v for k, v in saldos_iniciales_map.items()}
    }

def generate_auxiliar_inverso_pdf(db: Session, empresa_id: int, filtros: Dict[str, Any]):
    report_data = generate_auxiliar_inverso_report(db, empresa_id, filtros)
    empresa_info = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()
    
    # Obtener info de cuenta principal
    cuenta_principal = db.query(PlanCuenta).filter(PlanCuenta.id == filtros['cuenta_id']).first()
    cuenta_display = f"{cuenta_principal.codigo} - {cuenta_principal.nombre}" if cuenta_principal else "Desconocida"

    # Preparar datos agrupados para la plantilla
    # La plantilla espera una estructura similar a 'movimientos' pero quizás agrupada
    # Vamos a usar la misma plantilla de auxiliar tercero si es posible, O una genérica dinámica.
    # Dado que "tercero_cuenta" (auxiliar normal) ya tiene una plantilla, intentaremos adaptarla o usar una nueva.
    # Para rapidez y calidad, usaremos una estructura de contexto compatible con una plantilla nueva simple.
    
    # Agrupar movimientos por tercero para la vista impresa
    grouped_movs = {}
    
    # Inicializar con saldos
    saldos_init = report_data['saldos_iniciales_por_tercero']
    
    # Agrupar
    for mov in report_data['movimientos']:
        tid = str(mov['tercero_id'])
        if tid not in grouped_movs:
            grouped_movs[tid] = {
                "tercero_nombre": mov['tercero_nombre'],
                "saldo_inicial": saldos_init.get(tid, 0),
                "movimientos": [],
                "total_debito": 0,
                "total_credito": 0,
                "saldo_final": saldos_init.get(tid, 0)
            }
        
        grouped_movs[tid]['movimientos'].append(mov)
        grouped_movs[tid]['total_debito'] += mov['debito']
        grouped_movs[tid]['total_credito'] += mov['credito']
        grouped_movs[tid]['saldo_final'] = mov['saldo_parcial'] # El último será el final

    # Convertir a lista
    lista_terceros = list(grouped_movs.values())
    lista_terceros.sort(key=lambda x: x['tercero_nombre'])

    context = {
        'empresa': empresa_info,
        'fecha_inicio': filtros['fecha_inicio'].strftime('%d/%m/%Y'),
        'fecha_fin': filtros['fecha_fin'].strftime('%d/%m/%Y'),
        'titulo_reporte': f"Auxiliar Contable Inverso (Por Cuenta)",
        'subtitulo': f"Cuenta Principal: {cuenta_display}",
        'data_agrupada': lista_terceros,
        'total_general_saldo_ant': report_data['saldoAnterior']
    }

    # Definir plantilla HTML inline por simplicidad y robustez inmediata
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body { font-family: sans-serif; font-size: 10px; color: #333; }
            .header { text-align: center; margin-bottom: 20px; }
            .empresa-nombre { font-size: 14px; font-weight: bold; }
            .reporte-titulo { font-size: 12px; font-weight: bold; margin-top: 5px; }
            table { width: 100%; border-collapse: collapse; margin-bottom: 15px; }
            th, td { border: 1px solid #ddd; padding: 4px; text-align: left; }
            th { background-color: #f2f2f2; font-weight: bold; }
            .text-right { text-align: right; }
            .group-header { background-color: #e0e7ff; font-weight: bold; padding: 5px; margin-top: 10px; }
            .total-row { font-weight: bold; background-color: #f9fafb; }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="empresa-nombre">{{ empresa.razon_social }}</div>
            <div>NIT: {{ empresa.nit }}</div>
            <div class="reporte-titulo">{{ titulo_reporte }}</div>
            <div>{{ subtitulo }}</div>
            <div>Del {{ fecha_inicio }} al {{ fecha_fin }}</div>
        </div>

        {% for grupo in data_agrupada %}
            <div class="group-header">
                Tercero: {{ grupo.tercero_nombre }} | Saldo Inicial: {{ "{:,.2f}".format(grupo.saldo_inicial) }}
            </div>
            <table>
                <thead>
                    <tr>
                        <th width="15%">Fecha</th>
                        <th width="15%">Documento</th>
                        <th>Concepto</th>
                        <th width="12%" class="text-right">Débito</th>
                        <th width="12%" class="text-right">Crédito</th>
                        <th width="12%" class="text-right">Saldo</th>
                    </tr>
                </thead>
                <tbody>
                    {% for mov in grupo.movimientos %}
                    <tr>
                        <td>{{ mov.fecha }}</td>
                        <td>{{ mov.tipo_documento }} #{{ mov.numero_documento }}</td>
                        <td>{{ mov.concepto }}</td>
                        <td class="text-right">{{ "{:,.2f}".format(mov.debito) }}</td>
                        <td class="text-right">{{ "{:,.2f}".format(mov.credito) }}</td>
                        <td class="text-right">{{ "{:,.2f}".format(mov.saldo_parcial) }}</td>
                    </tr>
                    {% endfor %}
                    <tr class="total-row">
                        <td colspan="3" class="text-right">Total Tercero:</td>
                        <td class="text-right">{{ "{:,.2f}".format(grupo.total_debito) }}</td>
                        <td class="text-right">{{ "{:,.2f}".format(grupo.total_credito) }}</td>
                        <td class="text-right">{{ "{:,.2f}".format(grupo.saldo_final) }}</td>
                    </tr>
                </tbody>
            </table>
        {% endfor %}
    </body>
    </html>
    """
    
    try:
        template = GLOBAL_JINJA_ENV.from_string(html_template)
        html_string = template.render(context)
        pdf_content = HTML(string=html_string).write_pdf()
        return pdf_content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando PDF inverso: {e}")