import sys
import os
from sqlalchemy import create_engine, text

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.core.database import SessionLocal
import app.models # imports base models
import app.models.nomina # explicit import for nomina
from app.models.consumo_registros import ControlPlanMensual, HistorialConsumo, BolsaExcedente
from app.models.empresa import Empresa

def fix_frozen_record():
    db = SessionLocal()
    try:
        print("Starting Frozen Record Fix...")
        empresa = db.query(Empresa).filter(Empresa.razon_social.ilike("%Mejia y Mejia%")).first()
        if not empresa:
            print("Company not found.")
            return

        print(f"Target Company: {empresa.razon_social}")

        # 1. Delete the frozen 'CIERRE' record (ID 1690)
        # Record details: ID 1690, Date: 2026-01-30, Qty: 100, Type: CIERRE, Source: BOLSA
        frozen_cierre = db.query(HistorialConsumo).filter_by(id=1690).first()
        if frozen_cierre:
            print(f"Deleting Frozen Cierre Record ID {frozen_cierre.id} (Type: {frozen_cierre.tipo_operacion}, Qty: {frozen_cierre.cantidad})")
            db.delete(frozen_cierre)
        else:
            print("Record ID 1690 already deleted or not found.")

        # 2. Check for and Delete related BolsaExcedente
        # The Cierre usually creates a BolsaExcedente for the NEXT month? Or current?
        # Logic: If Cierre was Jan->Feb, Bolsa might be for Feb.
        # Let's check for any BolsaExcedente created recently for this company.
        bolsas = db.query(BolsaExcedente).filter_by(empresa_id=empresa.id).all()
        print(f"\nChecking BolsaExcedente records: {len(bolsas)}")
        for b in bolsas:
            print(f"  ID: {b.id}, Origin: {b.anio_origen}-{b.mes_origen}, Qty: {b.cantidad_inicial}, Created: {b.fecha_creacion}")
            # If we find one that looks like the result of that Cierre (100 records), delete it.
            if b.cantidad_inicial == 100 and b.anio_origen == 2026 and b.mes_origen == 1:
                print(f"  -> Deleting matching BolsaExcedente ID {b.id}")
                db.delete(b)

        db.commit()
        print("Fix committed successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error executing fix: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_frozen_record()
