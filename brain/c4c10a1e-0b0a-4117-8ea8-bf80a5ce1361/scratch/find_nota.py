import os
import sys

sys.path.append(os.path.abspath('c:/ContaPY2'))
from app.core.database import SessionLocal
from app.models.documento import Documento
from app.models.tipo_documento import TipoDocumento
from app.models.movimiento_contable import MovimientoContable
from app.models.plan_cuenta import PlanCuenta

db = SessionLocal()

# Buscamos documentos creados HOY con referencia a otro documento
# (Como son ensayos del usuario, es probable que se crearan hoy)
docs = db.query(Documento).filter(
    Documento.documento_referencia_id.isnot(None)
).order_by(Documento.id.desc()).limit(10).all()

print(f"--- DOCUMENTOS RECIENTES CON REFERENCIA ---")
for d in docs:
    tipo = db.query(TipoDocumento).get(d.tipo_documento_id)
    print(f"\nID: {d.id} | Emp: {d.empresa_id} | Num: {d.numero} | Tipo: {tipo.nombre} | Fecha: {d.fecha} | Benef: {d.beneficiario_id} | Ref: {d.documento_referencia_id}")
    
    # Movimientos en cuenta 13
    movs = db.query(MovimientoContable).join(PlanCuenta).filter(
        MovimientoContable.documento_id == d.id,
        PlanCuenta.codigo.like('13%')
    ).all()
    for m in movs:
        c = db.query(PlanCuenta).get(m.cuenta_id)
        print(f"  - Cuenta: {c.codigo} | D: {m.debito} | C: {m.credito} | Tero: {m.tercero_id}")

db.close()
