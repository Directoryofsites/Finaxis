import sys
import os
from sqlalchemy import create_engine, text
from datetime import datetime, date

# Add app to path
sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.documento import Documento
from app.models.movimiento_contable import MovimientoContable
from app.models.conciliacion_bancaria import BankMovement

def check_adjustments():
    db = SessionLocal()
    try:
        print("Checking recent documents...")
        # Check documents created today with "Ajuste" in observaciones
        today_docs = db.query(Documento).filter(
            Documento.fecha >= date.today(),
            Documento.observaciones.ilike('%Ajuste%')
        ).all()
        
        print(f"Found {len(today_docs)} adjustment documents created today:")
        for doc in today_docs:
            print(f"- ID: {doc.id}, Numero: {doc.numero}, Concepto: {doc.observaciones}, Credit: {doc.total_credito}")
            
            # Check associated movements
            movs = db.query(MovimientoContable).filter(MovimientoContable.documento_id == doc.id).all()
            print(f"  Movements ({len(movs)}):")
            for m in movs:
                print(f"  - Account: {m.cuenta_id}, Debit: {m.debito}, Credit: {m.credito}, Status: {m.reconciliation_status}")

        print("\nChecking Bank Movements status...")
        # Check bank movements with status ADJUSTED
        adjusted_movements = db.query(BankMovement).filter(
            BankMovement.status == 'ADJUSTED'
        ).limit(5).all()
        
        print(f"Found {len(adjusted_movements)} ADJUSTED bank movements:")
        for bm in adjusted_movements:
            print(f"- ID: {bm.id}, Desc: {bm.description}, Amount: {bm.amount}, Date: {bm.transaction_date}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_adjustments()
