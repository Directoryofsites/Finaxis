from typing import List, Dict, Any
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, func, select, or_

from ..models import PlanCuenta as models_plan
from ..models import Documento as models_doc
from ..models import AplicacionPago as models_aplica
from ..models import MovimientoContable as models_mov
from ..models import TipoDocumento as models_tipo
from ..models import Empresa as models_empresa
from app.services import documento as documento_service
from app.core.constants import FuncionEspecial
from ..models.propiedad_horizontal import PHConfiguracion

def get_cuentas_especiales_ids(db: Session, empresa_id: int, tipo: str) -> List[int]:
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
    
    if not cuentas_ids:
        return []

    # Obtener configuración de prefijos de la empresa
    empresa = db.query(models_empresa).filter(models_empresa.id == empresa_id).first()

    # --- INTEGRACION PH: Verificar si hay cuenta centralizada de Carter ---
    # Esto asegura que la cuenta 16 (o cualquiera) configurada en PH sea reconocida como CXC
    ph_config = db.query(PHConfiguracion).filter(PHConfiguracion.empresa_id == empresa_id).first()
    ph_cuenta_cartera_id = ph_config.cuenta_cartera_id if ph_config else None
    
    # Lógica flexible para CXC:
    # En PH y otros negocios, la cartera puede ser 13, 14, 16, etc.
    # El problema original era que incluía la 11 (Caja) y los recibos sumaban deuda.
    # SOLUCIÓN: Si es CXC, aceptamos cualquier ACTIVO (1%) excepto DISPONIBLE (11%).
    
    if tipo == 'cxc':
        print(f"DEBUG: Checking CXC IDs: {cuentas_ids}")
        valid_ids = db.query(models_plan.id, models_plan.codigo).filter(
            models_plan.id.in_(list(cuentas_ids)),
            models_plan.codigo.like("1%"),
            ~models_plan.codigo.like("11%") # Excluir Caja/Bancos
        ).all()
        
        result_ids = [row.id for row in valid_ids]
        
        # AGREGAR CUENTA PH EXPLICITA SI EXISTE (Y SI ES VALIDA/ACTIVA)
        # Esto soluciona el caso donde por algun motivo el filtro de arriba no la cogiera,
        # O simplemente para dar prioridad total.
        if ph_cuenta_cartera_id and ph_cuenta_cartera_id in cuentas_ids:
            if ph_cuenta_cartera_id not in result_ids:
                print(f"DEBUG: Adding PH Specific Account {ph_cuenta_cartera_id} to valid list.")
                result_ids.append(ph_cuenta_cartera_id)

        print(f"DEBUG: Valid CXC Codes found: {[r.codigo for r in valid_ids]}")
        return result_ids
    else:
        # Para CXP (Proveedores), mantenemos Pasivos (2%)
        # Podríamos usar la configuración de empresa si se requiere algo exótico
        prefix = empresa.prefijo_cxp if empresa and empresa.prefijo_cxp else default_cxp
        valid_ids = db.query(models_plan.id).filter(
            models_plan.id.in_(list(cuentas_ids)),
            models_plan.codigo.like(f"{prefix}%")
        ).all()

    return [row.id for row in valid_ids]

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

        cuentas_cxc_ids = get_cuentas_especiales_ids(db, empresa_id, 'cxc')
        cuentas_cxp_ids = get_cuentas_especiales_ids(db, empresa_id, 'cxp')

        documentos_potenciales = db.query(models_doc).options(
            joinedload(models_doc.tipo_documento),
            selectinload(models_doc.movimientos)
        ).filter(
            filter_condition,
            models_doc.empresa_id == empresa_id,
            models_doc.anulado == False
        ).order_by(models_doc.fecha, models_doc.id).all()


        # --- NUEVA LÓGICA ROBUSTA ---
        # Clasificar documentos por su impacto contable real, ignorando etiquetas mal configuradas.
        # Si (Debito - Credito) > 0 -> Es FACTURA (Aumenta deuda)
        # Si (Debito - Credito) < 0 -> Es PAGO (Disminuye deuda)
        
        docs_cxc_ordenados = []
        pagos_cxc_ordenados = []

        # Para proveedores (CXP), la lógica es inversa:
        # Credito - Debito > 0 -> FACTURA COMPRA (Aumenta deuda)
        # Credito - Debito < 0 -> PAGO (Disminuye deuda)
        docs_cxp_ordenados = []
        pagos_cxp_ordenados = []

        for d in documentos_potenciales:
            # --- ANÁLISIS CXC ---
            impacto_cxc = 0
            has_cxc_mov = False
            for mov in d.movimientos:
                if mov.cuenta_id in cuentas_cxc_ids:
                    impacto_cxc += (mov.debito - mov.credito)
                    has_cxc_mov = True
            
            if has_cxc_mov:
                if impacto_cxc > 0:
                    docs_cxc_ordenados.append({'doc': d, 'saldo': impacto_cxc})
                elif impacto_cxc < 0:
                    pagos_cxc_ordenados.append({'doc': d, 'monto': abs(impacto_cxc)})

            # --- ANÁLISIS CXP ---
            impacto_cxp = 0
            has_cxp_mov = False
            for mov in d.movimientos:
                if mov.cuenta_id in cuentas_cxp_ids:
                    impacto_cxp += (mov.credito - mov.debito) # CXP aumenta por Haber
                    has_cxp_mov = True
            
            if has_cxp_mov:
                if impacto_cxp > 0:
                    docs_cxp_ordenados.append({'doc': d, 'saldo': impacto_cxp})
                elif impacto_cxp < 0:
                    pagos_cxp_ordenados.append({'doc': d, 'monto': abs(impacto_cxp)})

        # Procesar Cruces CXC
        if docs_cxc_ordenados and pagos_cxc_ordenados:
            facturas_pendientes = {item['doc'].id: item for item in docs_cxc_ordenados}
            
            # Ordenar pagos por fecha para aplicar
            pagos_cxc_ordenados.sort(key=lambda x: (x['doc'].fecha, x['doc'].id))
            
            for pago in pagos_cxc_ordenados:
                valor_pago = pago['monto']
                # Aplicar a facturas ordenadas por fecha (FIFO)
                # Iterar sobre la lista original para mantener orden
                for factura_data in docs_cxc_ordenados:
                    if valor_pago <= 0: break
                    if factura_data['saldo'] > 0:
                        valor_a_aplicar = min(valor_pago, factura_data['saldo'])
                        if valor_a_aplicar > 0:
                            nueva_aplicacion = models_aplica(
                                documento_factura_id=factura_data['doc'].id, 
                                documento_pago_id=pago['doc'].id, 
                                valor_aplicado=valor_a_aplicar
                            )
                            db.add(nueva_aplicacion)
                            factura_data['saldo'] -= valor_a_aplicar
                            valor_pago -= valor_a_aplicar

        # Procesar Cruces CXP
        if docs_cxp_ordenados and pagos_cxp_ordenados:
            facturas_compra_pendientes = {item['doc'].id: item for item in docs_cxp_ordenados}
            pagos_cxp_ordenados.sort(key=lambda x: (x['doc'].fecha, x['doc'].id))

            for pago in pagos_cxp_ordenados:
                valor_pago = pago['monto']
                for factura_data in docs_cxp_ordenados:
                    if valor_pago <= 0: break
                    if factura_data['saldo'] > 0:
                        valor_a_aplicar = min(valor_pago, factura_data['saldo'])
                        if valor_a_aplicar > 0:
                            nueva_aplicacion = models_aplica(
                                documento_factura_id=factura_data['doc'].id, 
                                documento_pago_id=pago['doc'].id, 
                                valor_aplicado=valor_a_aplicar
                            )
                            db.add(nueva_aplicacion)
                            factura_data['saldo'] -= valor_a_aplicar
                            valor_pago -= valor_a_aplicar
        
        db.commit() # IMPORTANTE: Persistir los cambios
        return {"status": "ok", "message": "Recálculo de cartera y proveedores completado."}

    except Exception as e:
        db.rollback()
        raise e
            
def get_facturas_pendientes_por_tercero(db: Session, tercero_id: int, empresa_id: int):
    cuentas_cxc_ids = get_cuentas_especiales_ids(db, empresa_id, 'cxc')
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
    cuentas_cxp_ids = get_cuentas_especiales_ids(db, empresa_id, 'cxp')
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