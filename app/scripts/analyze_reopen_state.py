import sys
import os
from sqlalchemy import func

# Add project root to path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.consumo_registros import BolsaExcedente, HistorialConsumo, TipoFuenteConsumo, RecargaAdicional
from app.models.empresa import Empresa
import app.models.nomina

def inspect_post_reopen_state(company_id):
    db = SessionLocal()
    try:
        print(f"--- INSPECTION FOR COMPANY ID: {company_id} ---")
        
        # 1. Check Surplus Bags (Should be New and Full)
        print("\n[ACTIVE SURPLUS BAGS]")
        bolsas = db.query(BolsaExcedente).filter(
            BolsaExcedente.empresa_id == company_id
        ).order_by(BolsaExcedente.anio_origen, BolsaExcedente.mes_origen).all()
        
        if not bolsas:
            print("No surplus bags found.")
        
        for b in bolsas:
            print(f"  - Bag {b.mes_origen}/{b.anio_origen}: Initial={b.cantidad_inicial}, Available={b.cantidad_disponible}, Status={b.estado}")

        # 2. Check Consumption History for Jan 2026 (Where the mystery is)
        print("\n[CONSUMPTION HISTORY JAN 2026]")
        history = db.query(HistorialConsumo).filter(
            HistorialConsumo.empresa_id == company_id,
            func.extract('year', HistorialConsumo.fecha) == 2026,
            func.extract('month', HistorialConsumo.fecha) == 1,
            HistorialConsumo.tipo_operacion == 'CONSUMO'
        ).order_by(HistorialConsumo.fecha).all()
        
        counts = {}
        for h in history:
            key = f"{h.fuente_tipo} (ID: {h.fuente_id})"
            counts[key] = counts.get(key, 0) + h.cantidad
            
        for k, v in counts.items():
            print(f"  - {k}: {v}")

        # 3. Check Recharges
        print("\n[RECHARGES]")
        recargas = db.query(RecargaAdicional).filter(
            RecargaAdicional.empresa_id == company_id
        ).all()
        for r in recargas:
             print(f"  - Recharge ID {r.id}: Bought={r.cantidad_comprada}, Available={r.cantidad_disponible}, Status={r.estado}")

    finally:
        db.close()

if __name__ == "__main__":
    # Inspect the whole family
    for cid in [176, 177, 205]:
        inspect_post_reopen_state(cid)
