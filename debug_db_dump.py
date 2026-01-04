import sys
import os
from sqlalchemy import text

# Add project root to sys.path
sys.path.append(os.getcwd())

# Force env loading
from dotenv import load_dotenv
load_dotenv()

from app.core.database import SessionLocal
from app.models.usuario import Usuario
from app.models.plan_cuenta import PlanCuenta
from app.models.documento import Documento
from app.models.empresa import Empresa

def debug_db_contents():
    db = SessionLocal()
    print("="*60)
    print("DIAGNOSTICO DE EMPRESA_ID Y DATOS")
    print("="*60)

    # 1. EMPRESAS (Simplified)
    empresas_count = db.query(Empresa).count()
    print(f"\n1. EMPRESAS EN BD: {empresas_count} registros encontrados.")

    # 2. USUARIOS
    usuarios = db.query(Usuario).all()
    print(f"\n2. USUARIOS EN BD ({len(usuarios)}):")
    for u in usuarios:
        print(f"   - ID: {u.id} | Email: {u.email} | Empresa_ID: {u.empresa_id}")

    # 3. PLAN DE CUENTAS (Muestra)
    cuentas = db.query(PlanCuenta).limit(5).all()
    print(f"\n3. PLAN CUENTAS (Primeros 5):")
    for c in cuentas:
        print(f"   - ID: {c.id} | Codigo: {c.codigo} | Empresa_ID: {c.empresa_id}")

    # 4. DOCUMENTOS (Muestra)
    docs = db.query(Documento).limit(5).all()
    print(f"\n4. DOCUMENTOS (Primeros 5):")
    for d in docs:
        print(f"   - ID: {d.id} | Num: {d.numero} | Empresa_ID: {d.empresa_id} | Anulado: {d.anulado}")

    # 5. MOVIMIENTOS CONTABLES (Muestra)
    movs = db.query(MovimientoContable).limit(5).all()
    print(f"\n5. MOVIMIENTOS CONTABLES (Primeros 5):")
    for m in movs:
        print(f"   - ID: {m.id} | Doc_ID: {m.documento_id} | Cuenta_ID: {m.cuenta_id} | Empresa_ID: {getattr(m, 'empresa_id', 'N/A')}")


if __name__ == "__main__":
    debug_db_contents()
