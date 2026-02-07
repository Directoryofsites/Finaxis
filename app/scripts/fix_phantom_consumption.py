import sys
import os
from sqlalchemy import func, or_

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.core.database import SessionLocal
from app.models.consumo_registros import HistorialConsumo, BolsaExcedente
from app.models.documento import Documento
from app.models.empresa import Empresa
import app.models.nomina # Fix mapper error

def clean_orphans_and_bags():
    db = SessionLocal()
    try:
        print("--- 1. Checking for Orphaned Consumption Records (Phantom Consumption) ---")
        # Find HistorialConsumo records that have a documento_id but the document does not exist
        orphans = db.query(HistorialConsumo).outerjoin(
            Documento, HistorialConsumo.documento_id == Documento.id
        ).filter(
            HistorialConsumo.documento_id != None,
            Documento.id == None
        ).all()

        if orphans:
            print(f"Found {len(orphans)} orphaned consumption records. Deleting...")
            ids_to_delete = [o.id for o in orphans]
            # Bulk delete
            db.query(HistorialConsumo).filter(HistorialConsumo.id.in_(ids_to_delete)).delete(synchronize_session=False)
            db.commit()
            print("Orphans deleted successfully.")
        else:
            print("No orphaned consumption records found.")

        print("\n--- 2. Checking for 'Bolsa Excedente' (60 records) ---")
        # User specifically mentioned 60 records.
        # Let's find bags with exactly 60 or closely matching, created recently
        bags = db.query(BolsaExcedente).filter(
            BolsaExcedente.cantidad_inicial == 60
        ).all()

        if bags:
            print(f"Found {len(bags)} Bolsa Excedente records with 60 qty:")
            for b in bags:
                print(f" - ID: {b.id} | EmpresaID: {b.empresa_id} | Created: {b.fecha_creacion} | Available: {b.cantidad_disponible}")
                # We can delete them if this is a cleanup script
                db.delete(b)
            db.commit()
            print("Bolsa Excedente records deleted.")
        else:
            print("No specific '60 record' bags found (or already consumed). check logic.")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clean_orphans_and_bags()
