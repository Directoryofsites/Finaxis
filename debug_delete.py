import sys
import os

sys.path.insert(0, r"C:\ContaPY2")

from app.core.database import SessionLocal
from app.models.plan_cuenta import PlanCuenta
from app.services.plan_cuenta import _identificar_cuentas_borrables
from app.models.movimiento_contable import MovimientoContable
from app.models.documento import Documento
from app.models.impuesto import TasaImpuesto
from app.models.tipo_documento import TipoDocumento

def debug_deletion():
    db = SessionLocal()
    try:
        from app.models.empresa import Empresa
        
        # Buscar la cuenta 53
        cuenta = db.query(PlanCuenta).filter(
            PlanCuenta.codigo.like("53%")
        ).first()
        
        if not cuenta:
            print("No hay cuentas")
            return
            
        empresa_id = cuenta.empresa_id
        print(f"\nAnalizando cuenta: {cuenta.id} - Cdigo: '{cuenta.codigo}' - Nombre: {cuenta.nombre} - Empresa: {empresa_id}")
        
        # Copiamos logica
        todas_las_cuentas_empresa = db.query(PlanCuenta).filter(PlanCuenta.empresa_id == empresa_id).all()
        codigo_raiz = str(cuenta.codigo)
        descendientes_ids = set()
        for c in todas_las_cuentas_empresa:
            if str(c.codigo).startswith(codigo_raiz):
                descendientes_ids.add(c.id)
                
        print(f"Descendientes directos ({len(descendientes_ids)}): {descendientes_ids}")
        
        ids_protegidos = set()
        
        # Movimientos
        cuentas_con_movimiento_q = db.query(MovimientoContable.cuenta_id).join(
            Documento, MovimientoContable.documento_id == Documento.id
        ).filter(
            Documento.empresa_id == empresa_id,
            MovimientoContable.cuenta_id.in_(list(descendientes_ids))
        ).distinct().all()
        ids_mov = {item[0] for item in cuentas_con_movimiento_q}
        print(f"Protegidos por movimiento: {ids_mov}")
        ids_protegidos.update(ids_mov)
        
        # Impuestos
        impuestos_q = db.query(TasaImpuesto.cuenta_id, TasaImpuesto.cuenta_iva_descontable_id).filter(
            TasaImpuesto.empresa_id == empresa_id
        ).all()
        ids_imp_v = {t.cuenta_id for t in impuestos_q if t.cuenta_id in descendientes_ids}
        ids_imp_c = {t.cuenta_iva_descontable_id for t in impuestos_q if t.cuenta_iva_descontable_id in descendientes_ids}
        print(f"Protegidos por impuestos V: {ids_imp_v}, C: {ids_imp_c}")
        ids_protegidos.update(ids_imp_v)
        ids_protegidos.update(ids_imp_c)
        
        # Tipos doc
        tipos_doc_q = db.query(
            TipoDocumento.cuenta_debito_cxc_id, TipoDocumento.cuenta_credito_cxc_id,
            TipoDocumento.cuenta_debito_cxp_id, TipoDocumento.cuenta_credito_cxp_id
        ).filter(TipoDocumento.empresa_id == empresa_id).all()
        ids_td1 = {t.cuenta_debito_cxc_id for t in tipos_doc_q if t.cuenta_debito_cxc_id in descendientes_ids}
        ids_td2 = {t.cuenta_credito_cxc_id for t in tipos_doc_q if t.cuenta_credito_cxc_id in descendientes_ids}
        ids_td3 = {t.cuenta_debito_cxp_id for t in tipos_doc_q if t.cuenta_debito_cxp_id in descendientes_ids}
        ids_td4 = {t.cuenta_credito_cxp_id for t in tipos_doc_q if t.cuenta_credito_cxp_id in descendientes_ids}
        
        print(f"Protegidos por tipo doc: {ids_td1 | ids_td2 | ids_td3 | ids_td4}")
        ids_protegidos.update(ids_td1 | ids_td2 | ids_td3 | ids_td4)
        
        print(f"Total IDs Protegidos iniciales: {ids_protegidos}")
        
    finally:
        db.close()

if __name__ == "__main__":
    debug_deletion()
