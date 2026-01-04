import sys
import os
from datetime import date
from sqlalchemy import func, text

# Add project root to sys.path
sys.path.append(os.getcwd())

# Force env loading explicitly just to be sure
from dotenv import load_dotenv
load_dotenv()

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.movimiento_contable import MovimientoContable
from app.models.plan_cuenta import PlanCuenta
from app.models.documento import Documento

def debug_comparison():
    print("="*60)
    print(f"DIAGNOSTICO V3 - Comparativa de Queries")
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
    print("="*60)

    db = SessionLocal()
    empresa_id = 1
    fecha_inicio = date(2025, 1, 1)
    fecha_fin = date(2025, 12, 31)

    # 1. QUERY TIPO BALANCE (SOLO join Documento)
    print("\n1. Ejecutando Query estilo 'Balance de Prueba' (Sin filtro 11%, todas):")
    try:
        results_bal = db.query(
            MovimientoContable.cuenta_id,
            func.sum(MovimientoContable.debito).label("debito"),
            func.sum(MovimientoContable.credito).label("credito")
        ).join(Documento).filter(
            Documento.empresa_id == empresa_id,
            Documento.fecha >= fecha_inicio,
            Documento.fecha <= fecha_fin,
            Documento.anulado == False
        ).group_by(MovimientoContable.cuenta_id).all()
        
        print(f"   -> Filas encontradas: {len(results_bal)}")
        
        # Check if any account matches 11
        found_11 = False
        sample_id = None
        for row in results_bal:
            # We need to manually check the account code
            acc = db.query(PlanCuenta).get(row.cuenta_id)
            if acc and acc.codigo.startswith("11"):
                print(f"      * ENCONTRADO G11: {acc.codigo} - Deb: {row.debito} Cred: {row.credito}")
                found_11 = True
                sample_id = row.cuenta_id
                
        if not found_11:
            print("      (!) ATENCION: El Balance encuentra datos pero NINGUNO es Grupo 11.")
        else:
            print("      (OK) El Balance encuentra datos del Grupo 11.")

    except Exception as e:
        print(f"   (!) ERROR QUERY BALANCE: {e}")

    # 2. QUERY TIPO FLUJO (Con join PlanCuenta y Filtro)
    print("\n2. Ejecutando Query estilo 'Flujo de Efectivo' (Join PlanCuenta + Filtro 11%):")
    try:
        movimientos_efectivo = db.query(
            MovimientoContable
        ).join(PlanCuenta).join(Documento).filter(
            PlanCuenta.empresa_id == empresa_id,
            PlanCuenta.codigo.like("11%"),
            Documento.fecha >= fecha_inicio,
            Documento.fecha <= fecha_fin,
            Documento.anulado == False
        ).all()
        
        print(f"   -> Movimientos encontrados: {len(movimientos_efectivo)}")
        
        if len(movimientos_efectivo) == 0 and found_11:
            print("   (!) PARADOJA CONFIRMADA: Balance ve el Grupo 11, pero Flujo no.")
            print("       Posible causa: Join PlanCuenta fallido o codigo.like('11%') no match.")
            
            # Deep dive on the sample account found in Balance
            if sample_id:
                acc = db.query(PlanCuenta).get(sample_id)
                print(f"       Analizando cuenta ID {sample_id}:")
                print(f"       - Codigo '{acc.codigo}' (len={len(acc.codigo)})")
                print(f"       - Matches 11%? {'SI' if acc.codigo.startswith('11') else 'NO'}")
                
    except Exception as e:
        print(f"   (!) ERROR QUERY FLUJO: {e}")

if __name__ == "__main__":
    debug_comparison()
