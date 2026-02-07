import sys
import os
from sqlalchemy import desc

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.core.database import SessionLocal
from app.models.consumo_registros import HistorialConsumo, TipoOperacionConsumo, TipoFuenteConsumo
from app.models.documento import Documento
from app.models.empresa import Empresa
import app.models.nomina # Fix import error

def audit_consumption_source():
    db = SessionLocal()
    try:
        # 1. Find Mejia
        empresa = db.query(Empresa).filter(Empresa.razon_social.ilike("%Mejia%")).first()
        if not empresa:
            print("Company 'Mejia' not found.")
            return

        print(f"Auditing consumption for Company: {empresa.razon_social} (ID: {empresa.id})")

        # 2. Get Recent Consumption Records (Limit 10)
        history = db.query(HistorialConsumo).filter(
            HistorialConsumo.empresa_id == empresa.id,
            HistorialConsumo.tipo_operacion == TipoOperacionConsumo.CONSUMO
        ).order_by(desc(HistorialConsumo.fecha)).limit(10).all()

        print("\n--- RECENT CONSUMPTION RECORDS ---")
        for h in history:
            doc_info = "No Doc"
            if h.documento_id:
                doc = db.query(Documento).get(h.documento_id)
                if doc:
                    doc_empresa = db.query(Empresa).get(doc.empresa_id)
                    doc_owner = doc_empresa.razon_social if doc_empresa else "Unknown"
                    doc_info = f"Doc {doc.id} ({doc.fecha}) by {doc_owner}"
            
            print(f"Time: {h.fecha} | Qty: {h.cantidad} | Source: {h.fuente_tipo} | {doc_info}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    audit_consumption_source()
