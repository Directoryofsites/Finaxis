from app.core.database import SessionLocal
from app.models.consumo_registros import HistorialConsumo, BolsaExcedente, TipoOperacionConsumo, TipoFuenteConsumo
from sqlalchemy import func, text
from datetime import timedelta

def fix_orphan_cierres():
    db = SessionLocal()
    try:
        print("[INFO] Scanning for orphan CIERRE records...")
        
        # 1. Find orphans
        orphans = db.query(HistorialConsumo).filter(
            HistorialConsumo.tipo_operacion == TipoOperacionConsumo.CIERRE,
            HistorialConsumo.fuente_tipo == TipoFuenteConsumo.BOLSA,
            HistorialConsumo.fuente_id == None
        ).all()
        
        print(f"found {len(orphans)} orphans.")
        
        fixed_count = 0
        
        for orphan in orphans:
            print(f"  > Processing Orphan ID {orphan.id} | Date: {orphan.fecha} | Qty: {orphan.cantidad}")
            
            # 2. Find matching Bolsa
            # Logic: Same Company, Same Creation Time (+- 60 seconds), Same Quantity (Initial)
            # BolsaExcedente.fecha_creacion vs HistorialConsumo.fecha
            
            margin = timedelta(seconds=60) # Relaxed to 60s
            min_time = orphan.fecha - margin
            max_time = orphan.fecha + margin
            
            # Debug: Print candidates search range
            # print(f"    Searching for Bolsa with Qty={orphan.cantidad} between {min_time} and {max_time}")

            candidate = db.query(BolsaExcedente).filter(
                BolsaExcedente.empresa_id == orphan.empresa_id,
                BolsaExcedente.cantidad_inicial == orphan.cantidad,
                BolsaExcedente.fecha_creacion >= min_time,
                BolsaExcedente.fecha_creacion <= max_time
            ).order_by(BolsaExcedente.id.desc()).first() # Take newest if multiple
            
            if candidate:
                print(f"    [MATCH] MATCH FOUND: Bolsa ID {candidate.id} (Orig: {candidate.mes_origen}/{candidate.anio_origen})")
                orphan.fuente_id = candidate.id
                fixed_count += 1
            else:
                print("    [NO MATCH] NO MATCH FOUND. Skipping.")
                
        if fixed_count > 0:
            db.commit()
            print(f"[SUCCESS] Successfully fixed {fixed_count} records.")
        else:
            print("No records were fixed.")
            
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_orphan_cierres()
