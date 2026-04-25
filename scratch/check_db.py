import os
import sys

# Add the project root to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.models.documento import Documento
from app.models.movimiento_contable import MovimientoContable
from app.models.plan_cuenta import PlanCuenta
from app.models.propiedad_horizontal.concepto import PHConcepto
from app.models.tercero import Tercero
from sqlalchemy.orm import joinedload
from sqlalchemy import select

def check_db():
    db = SessionLocal()
    try:
        # Step 1: Verify the actual text in the DB for CXC debit movements
        # We need to find a third-party related to unit b2/101. Let's just grab the latest CXC debits for any PH unit.
        print("--- PASO 1: Textos de movimientos de débito CXC (últimos 20) ---")
        
        movs = db.query(MovimientoContable).join(
            Documento, MovimientoContable.documento_id == Documento.id
        ).join(
            PlanCuenta, MovimientoContable.cuenta_id == PlanCuenta.id
        ).filter(
            PlanCuenta.codigo.like('1305%'),
            MovimientoContable.debito > 0,
            Documento.unidad_ph_id.isnot(None) # Only PH documents
        ).order_by(
            Documento.fecha.desc()
        ).limit(20).all()
        
        for mov in movs:
            print(f"Doc: {mov.documento_id} | Cuenta: {mov.cuenta.codigo} - {mov.cuenta.nombre} | Concepto: '{mov.concepto}' | Débito: {mov.debito}")
        
        # Step 2: Verify the 'orden' field in ph_conceptos
        print("\n--- PASO 2: Campo orden en ph_conceptos ---")
        conceptos = db.query(PHConcepto).order_by(PHConcepto.orden).all()
        for c in conceptos:
            print(f"ID: {c.id} | Empresa: {c.empresa_id} | Nombre: '{c.nombre}' | Orden: {c.orden}")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_db()
