import sys
import os
from sqlalchemy import func, extract, or_
from datetime import date

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.core.database import SessionLocal
from app.models.consumo_registros import HistorialConsumo, TipoOperacionConsumo
from app.models.documento import Documento
from app.models.empresa import Empresa
import app.models.nomina # Fix import error

def investigate_accumulation():
    db = SessionLocal()
    try:
        # 1. Find Mejia
        empresa = db.query(Empresa).filter(Empresa.razon_social.ilike("%Mejia%")).first()
        if not empresa:
            print("Company 'Mejia' not found.")
            return

        print(f"Investigating Company: {empresa.razon_social} (ID: {empresa.id})")

        # 2. Check Consumption for Jan and Feb Separately
        for month in [1, 2]:
            year = 2025 # User context
            
            # Query exactly as Dashboard Service does now
            total_consumo = db.query(func.sum(HistorialConsumo.cantidad))\
                .outerjoin(Documento, HistorialConsumo.documento_id == Documento.id)\
                .filter(
                    or_(
                        HistorialConsumo.empresa_id == empresa.id,
                        Documento.empresa_id == empresa.id
                    ),
                    extract('year', HistorialConsumo.fecha) == year,
                    extract('month', HistorialConsumo.fecha) == month,
                    HistorialConsumo.tipo_operacion == TipoOperacionConsumo.CONSUMO
                ).scalar() or 0
            
            print(f"Consumption for Month {month}/{year}: {total_consumo}")

        # 3. List top consumers in Feb to see who is driving the 372
        print("\n--- Top Consumers in Feb 2026 ---")
        history_feb = db.query(HistorialConsumo).filter(
            extract('year', HistorialConsumo.fecha) == 2026,
            extract('month', HistorialConsumo.fecha) == 2,
            HistorialConsumo.tipo_operacion == TipoOperacionConsumo.CONSUMO,
             or_(
                HistorialConsumo.empresa_id == empresa.id,
                # Note: We can't easily filter by Documento.empresa_id in this simple list query without join,
                # but let's stick to what Mejia 'sees' as payer first.
                 HistorialConsumo.empresa_id == empresa.id
            )
        ).all()
        
        # Manually filter/group to mimic the OR logic correctly and see details
        total_feb_check = 0
        for h in history_feb:
            total_feb_check += h.cantidad
            # print(f" - ID {h.id}: Qty {h.cantidad} | Date {h.fecha}")

        print(f"Total explicitly on Mejia History for Feb: {total_feb_check}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    investigate_accumulation()
