import sys
import os
from sqlalchemy import func, extract, or_

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.core.database import SessionLocal
from app.models.consumo_registros import HistorialConsumo, TipoOperacionConsumo
from app.models.documento import Documento
from app.models.empresa import Empresa
import app.models.nomina

def audit_jan_2026_breakdown():
    db = SessionLocal()
    try:
        # 1. Find Mejia
        mejia = db.query(Empresa).filter(Empresa.razon_social.ilike("%Mejia y Mejia Tributos%")).first()
        if not mejia:
            print("Mejia not found")
            return
        
        print(f"Mejia ID: {mejia.id} (NIT: {mejia.nit})")

        # 2. Query Consumption Logic (Jan 2026)
        # Note: Using the exact logic from dashboard_service
        year = 2026
        month = 1
        
        # Financial Count (The main driver now)
        q = db.query(
            HistorialConsumo.cantidad, 
            HistorialConsumo.empresa_id, 
            Documento.empresa_id.label('doc_owner_id'),
            Empresa.razon_social.label('doc_owner_name')
        )\
        .outerjoin(Documento, HistorialConsumo.documento_id == Documento.id)\
        .outerjoin(Empresa, Documento.empresa_id == Empresa.id)\
        .filter(
            or_(
                HistorialConsumo.empresa_id == mejia.id,
                Documento.empresa_id == mejia.id
            ),
            extract('year', HistorialConsumo.fecha) == year,
            extract('month', HistorialConsumo.fecha) == month,
            HistorialConsumo.tipo_operacion == TipoOperacionConsumo.CONSUMO
        )
        
        results = q.all()
        
        total_qty = 0
        breakdown = {}
        
        for qty, hist_owner, doc_owner_id, doc_owner_name in results:
            total_qty += qty
            owner_name = doc_owner_name if doc_owner_name else f"Unknown/Self (ID {doc_owner_id})"
            if not doc_owner_id: owner_name = "Self (No Doc)"
            
            breakdown[owner_name] = breakdown.get(owner_name, 0) + qty
            
        print(f"\nTotal Calculated Consumption Jan 2026: {total_qty}")
        print("Breakdown by Document Owner:")
        for owner, qty in breakdown.items():
            print(f" - {owner}: {qty}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    audit_jan_2026_breakdown()
