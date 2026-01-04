import sys
import os
from datetime import date
from sqlalchemy import text

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.movimiento_contable import MovimientoContable
from app.models.plan_cuenta import PlanCuenta
from app.models.documento import Documento

def debug_multi_scan():
    db = SessionLocal()
    # IDs sospechosos encontrados en el dump anterior + el del usuario (1)
    target_ids = [1, 128, 129]
    
    fecha_inicio = date(2025, 1, 1) 
    fecha_fin = date(2025, 12, 31)

    print("="*60)
    print(f"ESCANEO MULTI-EMPRESA: {target_ids}")
    print("="*60)

    for empresa_id in target_ids:
        print(f"\n--- ANALIZANDO EMPRESA {empresa_id} ---")
        
        # 1. Cuentas Grupo 11
        count_cuentas = db.query(PlanCuenta).filter(
            PlanCuenta.empresa_id == empresa_id,
            PlanCuenta.codigo.like("11%")
        ).count()
        print(f"   > Cuentas Grupo 11: {count_cuentas}")

        # 2. Documentos Activos en 2025
        count_docs = db.query(Documento).filter(
            Documento.empresa_id == empresa_id,
            Documento.fecha >= fecha_inicio,
            Documento.fecha <= fecha_fin,
            Documento.anulado == False
        ).count()
        print(f"   > Documentos Activos (2025): {count_docs}")

        # 3. Movimientos (buscando por Documento.empresa_id)
        count_movs = db.query(MovimientoContable).join(Documento).filter(
            Documento.empresa_id == empresa_id,
            Documento.fecha >= fecha_inicio,
            Documento.fecha <= fecha_fin
        ).count()
        print(f"   > Movimientos Contables: {count_movs}")

if __name__ == "__main__":
    debug_multi_scan()
