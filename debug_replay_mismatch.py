from app.core.database import SessionLocal
from app.services.propiedad_horizontal import pago_service
from app.models.propiedad_horizontal import PHUnidad
from app.models.documento import Documento, MovimientoContable
from sqlalchemy.orm import joinedload, selectinload
from datetime import date

def debug_mismatch():
    db = SessionLocal()
    try:
        # 1. Buscar unidad b 5 / 501
        # Intentamos buscar por codigo o similar
        unidad = db.query(PHUnidad).filter(PHUnidad.codigo.ilike("%5 / 501%")).first()
        if not unidad:
            # Fallback a buscar cualquiera si no encuentra esa especifica
            print("No se encontro unidad especifica, buscando la primera...")
            unidad = db.query(PHUnidad).first()

        print(f"Debugueando Unidad: {unidad.codigo} ID: {unidad.id}")

        # 2. Obtener Docs (Copiado de pago_service logic)
        docs = db.query(Documento).options(
            selectinload(Documento.movimientos).joinedload(MovimientoContable.cuenta),
            joinedload(Documento.tipo_documento),
            joinedload(Documento.unidad_ph)
        ).filter(
            Documento.empresa_id == unidad.empresa_id,
            Documento.unidad_ph_id == unidad.id,
            Documento.estado.in_(['ACTIVO', 'PROCESADO'])
        ).order_by(Documento.fecha.asc(), Documento.id.asc()).all()

        # 3. Correr Simulacion con Snapshot en Marzo 1
        fecha_snapshot = date(2025, 3, 1)
        pending_debts, transacciones, snapshot = pago_service._simular_cronologia_pagos(db, docs, unidad.empresa_id, fecha_snapshot)

        # 4. Imprimir Snapshot names
        print("\n--- SNAPSHOT (MARZO 1) ---")
        for debt in snapshot:
            print(f"Debt: '{debt['concepto']}' | Val: {debt['saldo']}")

        # 5. Imprimir Pagos
        print("\n--- TRANSACCIONES ---")
        for t in transacciones:
            if t['credito'] > 0: # Es un pago
                print(f"Pago fecha: {t['fecha']} | Doc: {t['documento']}")
                print("  Detalle Pago Items:")
                for item in t['detalle_pago']:
                    print(f"    -> '{item}'")
                
                # Check raw pago summary if possible? 
                # No, detailed in transacciones is a list of strings.
                
                # Check sub items check
                # (My previous fix added sub_items to payment transaction? No, only to Saldo Inicial?
                # Actually _simular_cronologia_pagos adds sub_items for invoices, 
                # but for payments it uses detalle_pago strings)
                pass

    finally:
        db.close()

if __name__ == "__main__":
    debug_mismatch()
