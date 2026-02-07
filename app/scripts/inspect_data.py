import sys
import os
from sqlalchemy import or_

# Add project root to path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.tercero import Tercero
from app.models.plan_cuenta import PlanCuenta

def inspect_data():
    db = SessionLocal()
    try:
        print("=== INSPECCIÓN DE DATOS ===")
        
        # 1. Buscar Empresa
        empresa = db.query(Empresa).filter(Empresa.razon_social.ilike("%Pruebas de registros%")).first()
        if not empresa:
            print("[ERROR] No se encontró la empresa 'Pruebas de registros'")
            return
        
        print(f"Empresa: {empresa.razon_social} (ID: {empresa.id})")
        empresa_id = empresa.id

        # 2. Tipos de Documento
        print("\n--- Tipos de Documento ---")
        tipos = db.query(TipoDocumento).filter(TipoDocumento.empresa_id == empresa_id).all()
        for t in tipos:
            print(f"ID: {t.id} - Nombre: {t.nombre} - Es Manual: {t.es_manual}")

        # 3. Terceros
        print("\n--- Terceros (Primeros 5 + Busqueda 'pru') ---")
        terceros = db.query(Tercero).filter(Tercero.empresa_id == empresa_id).limit(5).all()
        for t in terceros:
            print(f"ID: {t.id} - Razón Social: {t.razon_social} - NIT: {t.nit}")
        
        # Buscar usuario especifico
        tercero_pru = db.query(Tercero).filter(
            Tercero.empresa_id == empresa_id,
            or_(Tercero.razon_social.ilike("%pru%"), Tercero.email.ilike("%pru%"))
        ).all()
        if tercero_pru:
            print("  [MATCH 'pru']:")
            for t in tercero_pru:
                print(f"  -> ID: {t.id} - {t.razon_social} ({t.email})")

        # 4. Cuentas
        print("\n--- Cuentas (Auxiliares Movibles) ---")
        cuentas = db.query(PlanCuenta).filter(
            PlanCuenta.empresa_id == empresa_id,
            PlanCuenta.permite_movimiento == True
        ).limit(10).all()
        
        for c in cuentas:
            print(f"ID: {c.id} - Código: {c.codigo} - Nombre: {c.nombre}")

    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_data()
