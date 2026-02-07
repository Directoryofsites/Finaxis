import sys
import os
from sqlalchemy import func

# Add project root to path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.consumo_registros import ControlPlanMensual
from app.models.documento import Documento
import app.models.nomina # Fix circular dependency/missing mapper

def diagnose_family(company_name_part):
    db = SessionLocal()
    try:
        # 1. Find Potential Parents
        candidates = db.query(Empresa).filter(Empresa.razon_social.ilike(f"%{company_name_part}%")).all()
        
        if not candidates:
            print(f"No companies found matching '{company_name_part}'")
            return
            
        print(f"Found {len(candidates)} candidates for '{company_name_part}':")
        for c in candidates:
             print(f" - {c.razon_social} (ID: {c.id}) | ParentID: {c.padre_id}")
             
        # Pick the one that looks like a parent (No ParentID) or just the first one?
        # Let's inspect ALL of them briefly
        
        for parent in candidates:
             print(f"\n==================================================")
             print(f"INSPECTING: {parent.razon_social} (ID: {parent.id})")
             print(f"==================================================")
        
        # 2. Find Children
        children = db.query(Empresa).filter(Empresa.padre_id == parent.id).all()
        print(f"Children Found: {len(children)}")
        for child in children:
            print(f"  - Child: {child.razon_social} (ID: {child.id})")

        # 3. Count Active Records (Parent)
        parent_docs = db.query(Documento).filter(
            Documento.empresa_id == parent.id,
            Documento.anulado == False
        ).count()
        print(f"\n[PARENT CONSUMPTION]")
        print(f"  Own Active Docs: {parent_docs}")

        # 4. Count Active Records (Children)
        total_child_docs = 0
        print(f"\n[CHILDREN CONSUMPTION]")
        for child in children:
            child_docs = db.query(Documento).filter(
                Documento.empresa_id == child.id,
                Documento.anulado == False
            ).count()
            print(f"  - {child.razon_social}: {child_docs}")
            total_child_docs += child_docs
        
        total_family_consumption = parent_docs + total_child_docs
        print(f"\n[TOTAL FAMILY CONSUMPTION]: {total_family_consumption}")

        # 5. Check Quota Status
        # Check current month (Feb 2026?)
        # Let's check all plans for simplicity or just recent ones
        print(f"\n[QUOTA STATUS (ControlPlanMensual)]")
        plans = db.query(ControlPlanMensual).filter(
            ControlPlanMensual.empresa_id == parent.id
        ).order_by(ControlPlanMensual.anio.desc(), ControlPlanMensual.mes.desc()).limit(3).all()

        forplan = None
        for p in plans:
            print(f"  - {p.mes}/{p.anio} | State: {p.estado}")
            print(f"    Limit: {p.limite_asignado}")
            print(f"    Available: {p.cantidad_disponible}")
            calc_consumed = p.limite_asignado - p.cantidad_disponible
            print(f"    Calculated Usage (Limit - Avail): {calc_consumed}")
            
            discrepancy = calc_consumed - total_family_consumption
            print(f"    DISCREPANCY (CalcUsage - RealFamily): {discrepancy}")
            if discrepancy != 0:
                print(f"    >>> DRIFT DETECTED <<<")

    finally:
        db.close()

def diagnose_by_id(company_id):
    db = SessionLocal()
    try:
        parent = db.query(Empresa).get(company_id)
        if not parent:
            print(f"Company ID {company_id} not found.")
            return

        print(f"\n--- DIAGNOSIS FOR ID: {parent.id} ({parent.razon_social}) ---")
        
        # 2. Find Children
        children = db.query(Empresa).filter(Empresa.padre_id == parent.id).all()
        print(f"Children Found: {len(children)}")
        for child in children:
            print(f"  - Child: {child.razon_social} (ID: {child.id})")

        # 3. Count Active Records (Parent)
        parent_docs = db.query(Documento).filter(
            Documento.empresa_id == parent.id,
            Documento.anulado == False
        ).count()
        print(f"\n[PARENT CONSUMPTION]")
        print(f"  Own Active Docs: {parent_docs}")

        # 4. Count Active Records (Children)
        total_child_docs = 0
        print(f"\n[CHILDREN CONSUMPTION]")
        for child in children:
            child_docs = db.query(Documento).filter(
                Documento.empresa_id == child.id,
                Documento.anulado == False
            ).count()
            print(f"  - {child.razon_social}: {child_docs}")
            total_child_docs += child_docs
        
        total_family_consumption = parent_docs + total_child_docs
        print(f"\n[TOTAL FAMILY CONSUMPTION]: {total_family_consumption}")

        # 5. Check Quota Status
        print(f"\n[QUOTA STATUS (ControlPlanMensual)]")
        plans = db.query(ControlPlanMensual).filter(
            ControlPlanMensual.empresa_id == parent.id
        ).order_by(ControlPlanMensual.anio.desc(), ControlPlanMensual.mes.desc()).limit(5).all()

        for p in plans:
            print(f"  - {p.mes}/{p.anio} | State: {p.estado}")
            print(f"    Limit: {p.limite_asignado}")
            print(f"    Available: {p.cantidad_disponible}")
            calc_consumed = p.limite_asignado - p.cantidad_disponible
            print(f"    Calculated Usage (Limit - Avail): {calc_consumed}")
            
            discrepancy = calc_consumed - total_family_consumption
            print(f"    DISCREPANCY (CalcUsage - RealFamily): {discrepancy}")
            
    finally:
        db.close()

if __name__ == "__main__":
    # diagnose_family("Gonzale")
    diagnose_by_id(177) # Gonzalito
