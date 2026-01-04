import sys
import os
from datetime import date
from decimal import Decimal

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.movimiento_contable import MovimientoContable
from app.models.plan_cuenta import PlanCuenta
from app.models.documento import Documento
from sqlalchemy import func

def debug_cash_flow():
    db = SessionLocal()
    empresa_id = 1
    fecha_inicio = date(2025, 11, 10) # Matching user screenshot roughly
    fecha_fin = date(2025, 12, 31)

    print(f"--- DEBUGGING CASH FLOW ---")
    print(f"Empresa: {empresa_id}, Rango: {fecha_inicio} - {fecha_fin}")

    # 1. Check if '11' accounts exist
    cuentas_caja = db.query(PlanCuenta).filter(
        PlanCuenta.empresa_id == empresa_id,
        PlanCuenta.codigo.like("11%")
    ).all()
    print(f"1. Cuentas Grupo 11 encontradas: {len(cuentas_caja)}")
    for c in cuentas_caja:
        print(f"   - {c.codigo} {c.nombre}")

    if not cuentas_caja:
        print("   (!) ERROR: No existen cuentas del grupo 11. El reporte siempre dará cero.")
        return

    # 2. Check ANY movements in date range for these accounts
    movimientos = db.query(
        MovimientoContable, Documento.fecha, Documento.estado, Documento.numero
    ).join(PlanCuenta).join(Documento).filter(
        PlanCuenta.empresa_id == empresa_id,
        PlanCuenta.codigo.like("11%"),
        Documento.fecha >= fecha_inicio,
        Documento.fecha <= fecha_fin
    ).all()

    print(f"2. Movimientos Grupo 11 en el rango (TOTAL): {len(movimientos)}")
    
    aprobados = [m for m in movimientos if m.estado == 'APROBADO']
    print(f"   - Movimientos en documentos APROBADOS: {len(aprobados)}")
    
    if not aprobados and movimientos:
        print("   (!) AVISO: Hay movimientos pero nunguno está APROBADO. El reporte filtra por estado APROBADO.")
        for m in movimientos[:5]:
            print(f"      Doc: {m.numero}, Estado: {m.estado}, Fecha: {m.fecha}")

    # 3. Analyze specific 'Approved' movements to check contra-account logic
    print("3. Analizando movimientos aprobados (Muestra primeros 5)...")
    for mov_tuple in aprobados[:5]:
        mov = mov_tuple[0]
        doc_fecha = mov_tuple[1]
        doc_numero = mov_tuple[2]
        
        print(f"   [Mov ID: {mov.id}] Doc: {doc_numero} {doc_fecha} | Valor: {mov.debito - mov.credito}")
        
        # Check contra-accounts in same document
        contrapartidas = db.query(
            PlanCuenta.codigo,
            PlanCuenta.nombre,
            (MovimientoContable.debito - MovimientoContable.credito).label("neto")
        ).join(MovimientoContable).filter(
            MovimientoContable.documento_id == mov.documento_id,
            ~PlanCuenta.codigo.like("11%")
        ).all()
        
        if not contrapartidas:
             print("      (x) Sin contrapartida válida (posible transferencia interna 11 vs 11)")
        else:
             print(f"      OK. Contrapartidas encontradas: {len(contrapartidas)}")
             for cp in contrapartidas:
                 print(f"         - {cp.codigo} {cp.nombre} (Neto: {cp.neto})")

if __name__ == "__main__":
    debug_cash_flow()
