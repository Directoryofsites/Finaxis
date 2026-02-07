import sys
import os
from sqlalchemy import func

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.core.database import SessionLocal
from app.models.consumo_registros import HistorialConsumo, BolsaExcedente, TipoOperacionConsumo, TipoFuenteConsumo
from app.models.empresa import Empresa
import app.models.nomina # Fix mapper

def force_delete_all_bags():
    db = SessionLocal()
    try:
        # 1. Find Mejia
        mejia = db.query(Empresa).filter(Empresa.razon_social.ilike("%Mejia%")).first()
        if not mejia:
            print("Mejia not found")
            return

        print(f"Cleaning Bags for: {mejia.razon_social} (ID: {mejia.id})")

        # 2. Find ALL Bags
        bags = db.query(BolsaExcedente).filter(
            BolsaExcedente.empresa_id == mejia.id
        ).all()

        if not bags:
            print("No bags found for Mejia.")
            return

        print(f"Found {len(bags)} bags. Deleting ALL...")
        
        for b in bags:
            print(f" -> Deleting Bag ID {b.id} (Initial: {b.cantidad_inicial}, Available: {b.cantidad_disponible}, State: {b.estado})")
            
            # Delete History linked to this bag (Creation/Usage)
            # 1. Creation (CIERRE)
            deleted_hist = db.query(HistorialConsumo).filter(
                HistorialConsumo.fuente_id == b.id,
                HistorialConsumo.fuente_tipo == TipoFuenteConsumo.BOLSA
            ).delete()
            print(f"    - Deleted {deleted_hist} history records linked to this bag.")
            
            # 2. Delete Bag
            db.delete(b)
            
        db.commit()
        print("All bags deleted successfully.")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    force_delete_all_bags()
