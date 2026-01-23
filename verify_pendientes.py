from app.core.database import SessionLocal
from app.services.propiedad_horizontal import pago_service
from app.models.propiedad_horizontal import PHUnidad
import json

def test_pendientes():
    db = SessionLocal()
    try:
        # Buscar la unidad que estaba dando problemas (o una con historial)
        # El user mencionaba 40k abono, 150k capital.
        unidad = db.query(PHUnidad).filter(PHUnidad.id == 42).first()
        if not unidad:
            print("No se encontró la unidad 42.")
            return

        print(f"Probando con Unidad: {unidad.codigo} (ID: {unidad.id}) Empresa: {unidad.empresa_id}")

        # Llamar al servicio
        pendientes = pago_service.get_cartera_ph_pendientes_detallada(
            db, 
            empresa_id=unidad.empresa_id, 
            unidad_id=unidad.id
        )

        print(f"\n--- Detalle Cartera Pendiente ({len(pendientes)} items) ---")
        for p in pendientes:
            print(f"Concepto: {p['concepto']}")
            print(f"Tipo: {p['tipo']}")
            print(f"Saldo: ${p['saldo']:,.0f}")
            print("-" * 20)

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_pendientes()
