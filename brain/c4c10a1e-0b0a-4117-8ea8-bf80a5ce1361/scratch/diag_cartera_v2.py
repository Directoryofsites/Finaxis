import os
import sys

sys.path.append(os.path.abspath('c:/ContaPY2'))
from app.core.database import SessionLocal
from app.services.cartera import get_facturas_pendientes_por_tercero, get_cuentas_especiales_ids
from app.models.documento import Documento
from app.models.tipo_documento import TipoDocumento
from app.models.movimiento_contable import MovimientoContable
from app.models.plan_cuenta import PlanCuenta
from sqlalchemy import func

db = SessionLocal()

# Tercero 2326 (uno de los mas activos en 134)
tercero_id = 2326
empresa_id = 134

print(f"--- DIAGNÓSTICO CARTERA TERCERO {tercero_id} (Empresa {empresa_id}) ---")

# 1. Cuentas detectadas
cuentas_ids = get_cuentas_especiales_ids(db, empresa_id, 'cxc')
cuentas_codigos = [db.query(PlanCuenta.codigo).filter(PlanCuenta.id == cid).scalar() for cid in cuentas_ids]
print(f"Cuentas CXC detectadas: {cuentas_codigos}")

# 2. Facturas pendientes reportadas
pendientes = get_facturas_pendientes_por_tercero(db, tercero_id, empresa_id)
pendientes_ids = [p['id'] for p in pendientes]

# 3. Documentos que TOCAN las cuentas CXC pero NO ESTÁN en el reporte
otros = db.query(Documento).join(MovimientoContable).filter(
    Documento.empresa_id == empresa_id,
    Documento.beneficiario_id == tercero_id,
    Documento.anulado == False,
    MovimientoContable.cuenta_id.in_(cuentas_ids),
    ~Documento.id.in_(pendientes_ids)
).distinct().all()

print(f"\nDocumentos que TOCAN CXC pero NO aparecen en el reporte ({len(otros)}):")
for o in otros:
    tipo = db.query(TipoDocumento).get(o.tipo_documento_id)
    # Sumar debitos
    val_debito = db.query(func.sum(MovimientoContable.debito)).filter(
        MovimientoContable.documento_id == o.id,
        MovimientoContable.cuenta_id.in_(cuentas_ids)
    ).scalar() or 0
    
    val_credito = db.query(func.sum(MovimientoContable.credito)).filter(
        MovimientoContable.documento_id == o.id,
        MovimientoContable.cuenta_id.in_(cuentas_ids)
    ).scalar() or 0
    
    print(f"  - ID: {o.id} | {tipo.nombre} #{o.numero} | D: {val_debito} | C: {val_credito}")

db.close()
