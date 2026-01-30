from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.consumo_registros import ControlPlanMensual, EstadoPlan
from app.services.consumo_service import _get_or_create_plan_mensual, calcular_deficit
from datetime import datetime
from app.core.config import settings

db = SessionLocal()

def debug_quota():
    print("-" * 50)
    print("DEBUGGING QUOTA STATUS")
    print(f"DATABASE URL: {settings.DATABASE_URL}")
    print("-" * 50)

    # 1. Find Mejia
    mejias = db.query(Empresa).filter(Empresa.razon_social.ilike("%Mejia%")).all()
    print(f"Found {len(mejias)} companies matching 'Mejia':")
    
    for m in mejias:
        print(f"ID: {m.id} | Name: {m.razon_social} | NIT: {m.nit} | Parent: {m.padre_id}")
    
    # Use the one matching the user's screenshot NIT if possible, or just the first.
    target_nit = "800300500-1"
    mejia = next((m for m in mejias if m.nit == target_nit), None)
    
    if not mejia:
        mejia = mejias[0] if mejias else None
        
    if not mejia:
        print("ERROR: Could not find company")
        return

    print(f"Company: {mejia.razon_social} (ID: {mejia.id})")
    print(f"Parent ID: {mejia.padre_id}")
    print(f"Master Limit (Global): {mejia.limite_registros}")
    print(f"Master Limit (Monthly): {mejia.limite_registros_mensual}")
    
    # --- FIX MASTER LIMIT ---
    if mejia.limite_registros != 1800:
        print("\n[FIX] Updating Master Limit to 1800...")
        mejia.limite_registros = 1800
        # mejia.limite_registros_mensual = 1800 # Optional, depending on logic
        db.add(mejia)
        db.commit()
        print("-> Master Limit Updated.")
    # ------------------------

    # 2. Check Mejia's Plan
    now = datetime.now()
    plan_mejia = _get_or_create_plan_mensual(db, mejia.id, now)
    print(f"\n[MEJIA LOCAL PLAN] {now.strftime('%Y-%m')}")
    print(f"  - Limit Assigned: {plan_mejia.limite_asignado}")
    print(f"  - Available (Local): {plan_mejia.cantidad_disponible}")
    print(f"  - Used (Implied): {plan_mejia.limite_asignado - plan_mejia.cantidad_disponible}")

    # 3. Check Parent's Plan
    if mejia.padre_id:
        plan_parent = _get_or_create_plan_mensual(db, mejia.padre_id, now)
        print(f"\n[PARENT GLOBAL PLAN] {now.strftime('%Y-%m')}")
        print(f"  - Limit Assigned: {plan_parent.limite_asignado}")
        print(f"  - Available (Global Wallet): {plan_parent.cantidad_disponible}")
        print(f"  - Used: {plan_parent.limite_asignado - plan_parent.cantidad_disponible}")
    
    # 4. Simulate Deficit Check for 84 records
    needed = 84
    print(f"\n[SIMULATION] Check for {needed} records")
    deficit = calcular_deficit(db, mejia.id, needed)
    print(f"  - Calculated Deficit: {deficit}")
    
    # --- MANUAL REPAIR ATTEMPT ---
    if deficit > 0 or plan_mejia.limite_asignado == 1800:
        print("\n[REPAIR] Attempting to recalculate balance based on new limit...")
        # Recalculate real consumption
        from app.models.documento import Documento
        from app.models.movimiento_contable import MovimientoContable
        from sqlalchemy import func, extract
        
        query_consumo = db.query(func.count(MovimientoContable.id))\
            .join(Documento, MovimientoContable.documento_id == Documento.id)\
            .filter(
                Documento.empresa_id == mejia.id,
                extract('year', Documento.fecha) == now.year,
                extract('month', Documento.fecha) == now.month,
                Documento.anulado == False
            )
        # DEBUG: Check HistorialConsumo (Financial)
        from app.models.consumo_registros import HistorialConsumo, TipoOperacionConsumo
        total_consumo_fin = db.query(func.sum(HistorialConsumo.cantidad)).filter(
            HistorialConsumo.empresa_id == mejia.id,
            extract('year', HistorialConsumo.fecha) == now.year,
            extract('month', HistorialConsumo.fecha) == now.month,
            HistorialConsumo.tipo_operacion == TipoOperacionConsumo.CONSUMO
        ).scalar() or 0
        print(f"  - Financial Consumption (Historial): {total_consumo_fin}")
        
        consumo_real = query_consumo.scalar() or 0
        print(f"  - Real Consumption (Physical Docs): {consumo_real}")
        
        # DEBUG: List documents
        docs = db.query(Documento).filter(
            Documento.empresa_id == mejia.id,
            extract('year', Documento.fecha) == now.year,
            extract('month', Documento.fecha) == now.month,
            # Documento.anulado == False  # Let's see ALL first
        ).all()
        print(f"  - Total Docs found in DB: {len(docs)}")
        for d in docs:
             count_movs = len(d.movimientos)
             print(f"    -> Doc {d.numero} ({d.fecha}): {count_movs} movs. Anulado={d.anulado}")

        expected_available = max(0, plan_mejia.limite_asignado - consumo_real)
        print(f"  - Expected Available: {expected_available}")
        print(f"  - Current Available: {plan_mejia.cantidad_disponible}")
        
        if plan_mejia.cantidad_disponible != expected_available:
            print("  -> FIXING BALANCE...")
            plan_mejia.cantidad_disponible = expected_available
            db.add(plan_mejia)
            db.commit()
            print("  -> FIXED.")
        else:
            print("  -> Balance appears correct.")
    # -----------------------------

    # --- NUCLEAR OPTION: DELETE PLAN ---
    if plan_mejia:
        print("\n[NUCLEAR] Deleting ControlPlanMensual to force reset...")
        db.delete(plan_mejia)
        db.commit()
        print("-> Plan Deleted. Next request will recreate it.")
    # -----------------------------
    
    # Verify deletion
    plan_check = db.query(ControlPlanMensual).filter(
        ControlPlanMensual.empresa_id == mejia.id,
        ControlPlanMensual.anio == now.year,
        ControlPlanMensual.mes == now.month
    ).first()
    
    if not plan_check:
        print("-> Verification: Plan is GONE.")
    else:
        print("-> ERROR: Plan still exists!")

debug_quota()
