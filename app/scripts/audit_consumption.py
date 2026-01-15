import sys
import os
from datetime import datetime
from sqlalchemy import func

# Add project root to path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.documento import Documento
from app.models.consumo_registros import HistorialConsumo
from app.models.movimiento_contable import MovimientoContable

def audit_missing_consumption():
    db = SessionLocal()
    try:
        # Scan entire Dec 2025 and Jan 2026
        start_date = datetime(2025, 12, 1)
        end_date = datetime(2026, 2, 1)

        print("[INFO] Auditing documents vs execution history...")

        # 1. Find all documents
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
                
                # Only care if it SHOULD have consumed something
                if mov_count > 0:
                    missing_docs.append({
                        "id": doc.id,
                        "numero": doc.numero,
                        "fecha": doc.fecha,
                        "registros": mov_count,
                        "tipo_id": doc.tipo_documento_id
                    })

        print(f"Found {len(missing_docs)} documents MISSING from history:")
        for d in missing_docs:
            print(f"  - Doc #{d['numero']} (ID: {d['id']}) Date: {d['fecha']} Rows: {d['registros']} TypeID: {d['tipo_id']}")

    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        db.close()

if __name__ == "__main__":
    audit_missing_consumption()
