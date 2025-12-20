
import sys
import os

# Ajustar path
sys.path.append("c:/ContaPY2")

from app.core.database import SessionLocal, get_db
from app.models import Documento, PHUnidad, MovimientoContable

def inspect_units():
    db = SessionLocal()
    try:
        print("--- INSPECCION DE UNIDADES EN DOCUMENTOS ---")
        # Buscamos por numero de documento mencionados en el debug anterior
        # FPH-10 (10), FPH-12 (12), FPH-15 (15)
        # RPH-3 (3), RPH-4 (4)
        # Filtrando por el tercero 817 para no confundir con otras empresas
        
        target_ids = [3323, 3325, 3329, 3331, 3334, 3328]
        
        docs = db.query(Documento).filter(Documento.id.in_(target_ids)).all()
        
        for d in docs:
            unit_code = "N/A"
            if d.unidad_ph_id:
                u = db.query(PHUnidad).filter(PHUnidad.id == d.unidad_ph_id).first()
                unit_code = u.codigo if u else "Broken Link"
            
            print(f"ID: {d.id} | Num: {d.numero} | Fecha: {d.fecha} | Unidad_ID: {d.unidad_ph_id} ({unit_code}) | Beneficiario: {d.beneficiario_id}")

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_units()
