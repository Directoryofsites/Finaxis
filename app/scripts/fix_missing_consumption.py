from app.core.database import SessionLocal
from app.models.documento import Documento
from app.models.consumo_registros import HistorialConsumo
from app.models.movimiento_contable import MovimientoContable
from app.services.consumo_service import registrar_consumo
from sqlalchemy import func
from datetime import datetime

def fix_missing_consumption():
    db = SessionLocal()
    try:
        print("[INFO] Scanning for documents without consumption history in Dec 2025...")
        
        # Define range: Dec 2025
        start_date = datetime(2025, 12, 1)
        end_date = datetime(2025, 12, 31, 23, 59, 59)
        
        # Find candidates
        candidates = db.query(Documento).filter(
            Documento.fecha >= start_date,
            Documento.fecha <= end_date,
            Documento.anulado == False
        ).all()
        
        print(f"Found {len(candidates)} documents to check in Dec 2025.")
        
        fixed_count = 0
        
        for doc in candidates:
            # Check if history exists
            history = db.query(HistorialConsumo).filter(HistorialConsumo.documento_id == doc.id).first()
            
            if not history:
                # Calculate consumption quantity
                qty = db.query(func.count(MovimientoContable.id)).filter(
                    MovimientoContable.documento_id == doc.id
                ).scalar()
                
                if qty > 0:
                    print(f"  > Doc #{doc.numero} (ID: {doc.id}) has NO history. Using {qty} records.")
                    try:
                        # Attempt to register consumption
                        # We use doc.fecha to target the correct plan
                        registrar_consumo(db, doc.empresa_id, qty, doc.id, doc.fecha)
                        fixed_count += 1
                        print(f"    [FIXED] Consumed {qty} from Plan/Bolsa.")
                    except Exception as e:
                        print(f"    [FAILED] Failed to fix Doc #{doc.numero}: {e}")
                else:
                    # print(f"  > Doc #{doc.numero} (ID: {doc.id}) empty. Skipping.")
                    pass
            else:
                # History exists, skipping
                pass

        if fixed_count > 0:
            db.commit()
            print(f"[SUCCESS] Successfully fixed {fixed_count} documents.")
        else:
            print("No missing consumptions found.")
            
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_missing_consumption()
