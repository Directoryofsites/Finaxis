import os
import sys

sys.path.append(os.path.abspath('c:/ContaPY2'))
from app.core.database import SessionLocal
from app.services.cartera import get_cuentas_especiales_ids
from app.models.plan_cuenta import PlanCuenta

db = SessionLocal()
empresa_id = 134

print(f"--- CUENTAS CXC DETECTADAS PARA EMPRESA {empresa_id} ---")
ids = get_cuentas_especiales_ids(db, empresa_id, 'cxc')
print(f"IDs detectados: {ids}")

cuentas = db.query(PlanCuenta).filter(PlanCuenta.id.in_(ids)).all()
for c in cuentas:
    print(f"ID: {c.id} | Codigo: {c.codigo} | Nombre: {c.nombre}")

db.close()
