# app/services/cartera.py (VERSIÓN CORREGIDA: FIX JOIN EN PROVEEDORES)

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, select, or_
from ..models import Documento as models_doc
from ..models import AplicacionPago as models_aplica
from ..models import MovimientoContable as models_mov
from ..models import TipoDocumento as models_tipo
from app.services import documento as documento_service
from typing import List, Dict, Any
from app.core.constants import FuncionEspecial

def _get_cuentas_especiales_ids(db: Session, empresa_id: int, tipo: str) -> List[int]:
    cuentas_ids = set()
    query = db.query(
        models_tipo.cuenta_debito_cxc_id,
        models_tipo.cuenta_credito_cxc_id,
        models_tipo.cuenta_debito_cxp_id,
        models_tipo.cuenta_credito_cxp_id
    ).filter(models_tipo.empresa_id == empresa_id).distinct()

    if tipo == 'cxc':
        for row in query.all():
            if row.cuenta_debito_cxc_id: cuentas_ids.add(row.cuenta_debito_cxc_id)
            if row.cuenta_credito_cxc_id: cuentas_ids.add(row.cuenta_credito_cxc_id)
    elif tipo == 'cxp':
        for row in query.all():
            if row.cuenta_debito_cxp_id: cuentas_ids.add(row.cuenta_debito_cxp_id)
            if row.cuenta_credito_cxp_id: cuentas_ids.add(row.cuenta_credito_cxp_id)

    return list(cuentas_ids)

def _documento_afecta_cuentas(db: Session, documento_id: int, cuentas_ids: List[int]) -> bool:
    if not cuentas_ids:
        return False

    movimiento_existente = db.query(models_mov.id).filter(
        models_mov.documento_id == documento_id,
        models_mov.cuenta_id.in_(cuentas_ids)
    ).first()
    return movimiento_existente is not None

def recalcular_aplicaciones_tercero(db: Session, tercero_id: int, empresa_id: int):
    filter_condition = models_doc.beneficiario_id == tercero_id
    
    try:
        documento_ids_del_tercero_subquery = select(models_doc.id).where(
            filter_condition,
            models_doc.empresa_id == empresa_id
        ).scalar_subquery()

        db.query(models_aplica).where(
            or_(
                models_aplica.documento_factura_id.in_(documento_ids_del_tercero_subquery),
                models_aplica.documento_pago_id.in_(documento_ids_del_tercero_subquery)
            )
        ).delete(synchronize_session=False)

        cuentas_cxc_ids = _get_cuentas_especiales_ids(db, empresa_id, 'cxc')
        cuentas_cxp_ids = _get_cuentas_especiales_ids(db, empresa_id, 'cxp')

        documentos_potenciales = db.query(models_doc).options(joinedload(models_doc.tipo_documento)).filter(
            filter_condition,
            models_doc.empresa_id == empresa_id,
            models_doc.anulado == False
        ).order_by(models_doc.fecha, models_doc.id).all()

        facturas_venta = []
        for d in documentos_potenciales:
            if d.tipo_documento.funcion_especial == FuncionEspecial.CARTERA_CLIENTE:
                if _documento_afecta_cuentas(db, d.id, cuentas_cxc_ids):
                    facturas_venta.append(d)
        
        pagos_cartera = []
        for d in documentos_potenciales:
            if d.tipo_documento.funcion_especial == FuncionEspecial.RC_CLIENTE:
                if _documento_afecta_cuentas(db, d.id, cuentas_cxc_ids):
                    pagos_cartera.append(d)

        facturas_compra = []
        for d in documentos_potenciales:
            if d.tipo_documento.funcion_especial == FuncionEspecial.CXP_PROVEEDOR:
                if _documento_afecta_cuentas(db, d.id, cuentas_cxp_ids):
                    facturas_compra.append(d)

        pagos_proveedores = []
        for d in documentos_potenciales:
            if d.tipo_documento.funcion_especial == FuncionEspecial.PAGO_PROVEEDOR:
                if _documento_afecta_cuentas(db, d.id, cuentas_cxp_ids):
                    pagos_proveedores.append(d)
        
        if facturas_venta or pagos_cartera:
            docs_cxc_ordenados = sorted(facturas_venta + pagos_cartera, key=lambda doc: (doc.fecha, doc.id))
            facturas_pendientes = {}

            for doc in docs_cxc_ordenados:
                if doc.tipo_documento.funcion_especial == FuncionEspecial.CARTERA_CLIENTE:
                    valor_factura = db.query(func.sum(models_mov.debito)).filter(
                        models_mov.documento_id == doc.id,
                        models_mov.cuenta_id.in_(cuentas_cxc_ids)
                    ).scalar() or 0
                    facturas_pendientes[doc.id] = {'doc': doc, 'saldo': valor_factura}
                elif doc.tipo_documento.funcion_especial == FuncionEspecial.RC_CLIENTE:
                    valor_pago = db.query(func.sum(models_mov.credito)).filter(
                        models_mov.documento_id == doc.id,
                        models_mov.cuenta_id.in_(cuentas_cxc_ids)
                    ).scalar() or 0
                    for factura_id, data_factura in sorted(facturas_pendientes.items(), key=lambda item: (item[1]['doc'].fecha, item[1]['doc'].id)):
                        if valor_pago <= 0: break
                        if data_factura['saldo'] > 0:
                            valor_a_aplicar = min(valor_pago, data_factura['saldo'])
                            nueva_aplicacion = models_aplica(documento_factura_id=factura_id, documento_pago_id=doc.id, valor_aplicado=valor_a_aplicar)
                            db.add(nueva_aplicacion)
                            data_factura['saldo'] -= valor_a_aplicar
                            valor_pago -= valor_a_aplicar
        
        if facturas_compra or pagos_proveedores:
            docs_cxp_ordenados = sorted(facturas_compra + pagos_proveedores, key=lambda doc: (doc.fecha, doc.id))
            facturas_compra_pendientes = {}

            for doc in docs_cxp_ordenados:
                if doc.tipo_documento.funcion_especial == FuncionEspecial.CXP_PROVEEDOR:
                    valor_factura = db.query(func.sum(models_mov.credito)).filter(
                        models_mov.documento_id == doc.id,
                        models_mov.cuenta_id.in_(cuentas_cxp_ids)
                    ).scalar() or 0
                    facturas_compra_pendientes[doc.id] = {'doc': doc, 'saldo': valor_factura}
                elif doc.tipo_documento.funcion_especial == FuncionEspecial.PAGO_PROVEEDOR:
                    valor_pago = db.query(func.sum(models_mov.debito)).filter(
                        models_mov.documento_id == doc.id,
                        models_mov.cuenta_id.in_(cuentas_cxp_ids)
                    ).scalar() or 0
                    for factura_id, data_factura in sorted(facturas_compra_pendientes.items(), key=lambda item: (item[1]['doc'].fecha, item[1]['doc'].id)):
                        if valor_pago <= 0: break
                        if data_factura['saldo'] > 0:
                            valor_a_aplicar = min(valor_pago, data_factura['saldo'])
                            nueva_aplicacion = models_aplica(documento_factura_id=factura_id, documento_pago_id=doc.id, valor_aplicado=valor_a_aplicar)
                            db.add(nueva_aplicacion)
                            data_factura['saldo'] -= valor_a_aplicar
                            valor_pago -= valor_a_aplicar
        
        return {"status": "ok", "message": "Recálculo de cartera y proveedores completado."}

    except Exception as e:
        db.rollback()
        raise e
            
def get_facturas_pendientes_por_tercero(db: Session, tercero_id: int, empresa_id: int):
    cuentas_cxc_ids = _get_cuentas_especiales_ids(db, empresa_id, 'cxc')
    if not cuentas_cxc_ids:
        return []

    subquery_valor_total = db.query(
        models_mov.documento_id.label("documento_id"),
        func.sum(models_mov.debito).label("valor_total")
    ).join(models_doc, models_mov.documento_id == models_doc.id).filter(
        models_doc.empresa_id == empresa_id,
        models_doc.anulado == False,
        models_mov.cuenta_id.in_(cuentas_cxc_ids) 
    ).group_by(models_mov.documento_id).subquery()

    subquery_valor_aplicado = db.query(
        models_aplica.documento_factura_id.label("documento_id"),
        func.sum(models_aplica.valor_aplicado).label("total_aplicado")
    ).join(models_doc, models_aplica.documento_pago_id == models_doc.id).filter(
        models_doc.anulado == False
    ).group_by(models_aplica.documento_factura_id).subquery()

    facturas_pendientes = db.query(
        models_doc.id, models_doc.numero, models_doc.fecha,
        subquery_valor_total.c.valor_total,
        func.coalesce(subquery_valor_aplicado.c.total_aplicado, 0).label("total_aplicado")
    ).join(
        subquery_valor_total, subquery_valor_total.c.documento_id == models_doc.id
    ).join(
        models_tipo, models_doc.tipo_documento_id == models_tipo.id
    ).outerjoin(
        subquery_valor_aplicado, subquery_valor_aplicado.c.documento_id == models_doc.id
    ).filter(
        models_doc.beneficiario_id == tercero_id,
        models_doc.empresa_id == empresa_id,
        models_doc.anulado == False,
        models_tipo.funcion_especial == FuncionEspecial.CARTERA_CLIENTE,
        subquery_valor_total.c.valor_total > func.coalesce(subquery_valor_aplicado.c.total_aplicado, 0)
    ).order_by(models_doc.fecha).all()

    resultado_formateado = []
    for factura in facturas_pendientes:
        saldo_pendiente = factura.valor_total - factura.total_aplicado
        resultado_formateado.append({
            "id": factura.id, "numero": factura.numero,
            "fecha": factura.fecha.isoformat(),
            "valor_total": float(factura.valor_total),
            "saldo_pendiente": float(saldo_pendiente)
        })
    return resultado_formateado

def get_facturas_compra_pendientes_por_tercero(db: Session, tercero_id: int, empresa_id: int):
    cuentas_cxp_ids = _get_cuentas_especiales_ids(db, empresa_id, 'cxp')
    if not cuentas_cxp_ids:
        return []

    # --- CORRECCIÓN CRÍTICA EN JOIN ---
    # Antes: .join(models_mov, ...) -> Incorrecto, intentaba unir movimiento consigo mismo o flotaba
    # Ahora: .join(models_doc, ...) -> Correcto, une con documento para filtrar por empresa/anulado
    subquery_valor_total = db.query(
        models_mov.documento_id.label("documento_id"),
        func.sum(models_mov.credito).label("valor_total")
    ).join(models_doc, models_mov.documento_id == models_doc.id).filter(
        models_doc.empresa_id == empresa_id,
        models_doc.anulado == False,
        models_mov.cuenta_id.in_(cuentas_cxp_ids)
    ).group_by(models_mov.documento_id).subquery()

    subquery_valor_aplicado = db.query(
        models_aplica.documento_factura_id.label("documento_id"),
        func.sum(models_aplica.valor_aplicado).label("total_aplicado")
    ).join(models_doc, models_aplica.documento_pago_id == models_doc.id).filter(
        models_doc.anulado == False
    ).group_by(models_aplica.documento_factura_id).subquery()

    facturas_pendientes = db.query(
        models_doc.id, models_doc.numero, models_doc.fecha,
        subquery_valor_total.c.valor_total,
        func.coalesce(subquery_valor_aplicado.c.total_aplicado, 0).label("total_aplicado")
    ).join(
        subquery_valor_total, subquery_valor_total.c.documento_id == models_doc.id
    ).join(
        models_tipo, models_doc.tipo_documento_id == models_tipo.id
    ).outerjoin(
        subquery_valor_aplicado, subquery_valor_aplicado.c.documento_id == models_doc.id
    ).filter(
        models_doc.beneficiario_id == tercero_id,
        models_doc.empresa_id == empresa_id,
        models_doc.anulado == False,
        models_tipo.funcion_especial == FuncionEspecial.CXP_PROVEEDOR,
        subquery_valor_total.c.valor_total > func.coalesce(subquery_valor_aplicado.c.total_aplicado, 0)
    ).order_by(models_doc.fecha).all()

    resultado_formateado = []
    for factura in facturas_pendientes:
        saldo_pendiente = factura.valor_total - factura.total_aplicado
        resultado_formateado.append({
            "id": factura.id, "numero": factura.numero,
            "fecha": factura.fecha.isoformat(),
            "valor_total": float(factura.valor_total),
            "saldo_pendiente": float(saldo_pendiente)
        })
    return resultado_formateado