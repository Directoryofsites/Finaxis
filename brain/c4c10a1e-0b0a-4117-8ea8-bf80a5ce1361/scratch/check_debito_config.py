import os
import sys

sys.path.append(os.path.abspath('c:/ContaPY2'))
from app.core.database import SessionLocal
from app.models.tipo_documento import TipoDocumento
from app.models.plan_cuenta import PlanCuenta

db = SessionLocal()

# Empresa del usuario (en el ultimo log era 134 o similar, reviso segun el query anterior)
# NOTA DEBITO ID 2584 (Empresa 132) o NOTA DEBITO ID 2532 (Empresa 140)
# Vamos a ver las de la empresa 134 que es la que mas se usa en logs
tipos_134 = db.query(TipoDocumento).filter(TipoDocumento.empresa_id == 134).all()

print(f"Tipos de Documento Empresa 134:")
for t in tipos_134:
    if "NOTA" in t.nombre.upper() or "DEB" in t.nombre.upper():
         cuenta_cxc = db.query(PlanCuenta).get(t.cuenta_debito_cxc_id) if t.cuenta_debito_cxc_id else None
         print(f"ID: {t.id} | Nombre: {t.nombre} | Funcion: {t.funcion_especial} | Cuenta CxC ID: {t.cuenta_debito_cxc_id} ({cuenta_cxc.codigo if cuenta_cxc else 'N/A'})")

db.close()
