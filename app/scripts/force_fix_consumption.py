import sys
import os
from datetime import datetime
from sqlalchemy import func

# Add project root to path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.documento import Documento
from app.models.consumo_registros import HistorialConsumo, ControlPlanMensual, TipoFuenteConsumo, TipoOperacionConsumo
from app.models.movimiento_contable import MovimientoContable

def force_fix_missing_consumption():
    db = SessionLocal()
    try:
        # Target Date: Dec 2025
        start_date = datetime(2025, 12, 1)
        end_date = datetime(2026, 1, 1)

        print("[INFO] Scanning for documents without consumption history in Dec 2025...")

        # 1. Find Documents in range
        docs = db.query(Documento).filter(
            Documento.fecha >= start_date,
            Documento.fecha < end_date
        ).all()

        missing_docs = []
        for doc in docs:
            # Check if history exists
            history_count = db.query(HistorialConsumo).filter(
                HistorialConsumo.documento_id == doc.id
            ).count()

            if history_count == 0:
                # Calculate expected consumption
                mov_count = db.query(func.count(MovimientoContable.id)).filter(
                    MovimientoContable.documento_id == doc.id
                ).scalar() or 0
                
                if mov_count > 0:
                    missing_docs.append((doc, mov_count))

        print(f"Found {len(missing_docs)} documents to fix.")

        for doc, quantity in missing_docs:
            print(f"  > Fixing Doc #{doc.numero} (ID: {doc.id}, Date: {doc.fecha}) -> Quantity: {quantity}")

            # Create HistorialConsumo record manually
            # Assuming Plan Mensual is the source.
            
            # Dummy values for snapshot as we are retroactively fixing
            saldo_antes = 0
            saldo_despues = 0

            new_history = HistorialConsumo(
                empresa_id=doc.empresa_id,
                fecha=doc.fecha, # Use document date
                cantidad=quantity,
                tipo_operacion=TipoOperacionConsumo.CONSUMO,
                fuente_tipo=TipoFuenteConsumo.PLAN,
                fuente_id=None, # Null for Plan
                saldo_fuente_antes=saldo_antes,
                saldo_fuente_despues=saldo_despues,
                documento_id=doc.id
            )

            db.add(new_history)
        
        if missing_docs:
            db.commit()
            print("[SUCCESS] All missing history records created successfully.")
        else:
            print("[INFO] No missing records found.")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
    finally:
        db.close()

if __name__ == "__main__":
    force_fix_missing_consumption()
