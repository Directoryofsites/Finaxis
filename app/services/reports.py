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

from ..models import PlanCuenta, MovimientoContable, Documento, Empresa as models_empresa
from ..schemas import reporte_balance_prueba as schemas_bce

from ..models import CentroCosto
from ..schemas import reporte_balance_prueba_cc as schemas_bce_cc


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