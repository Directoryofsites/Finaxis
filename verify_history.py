from app.core.database import SessionLocal
from app.services.propiedad_horizontal import pago_service
from app.models.propiedad_horizontal import PHUnidad
import json

def verify_history():
    db = SessionLocal()
    try:
        unidad = db.query(PHUnidad).first()
        if not unidad:
            print("No hay unidades.")
            return

        print(f"Probando con Unidad: {unidad.codigo} (ID: {unidad.id}) Empresa: {unidad.empresa_id}")

        result = pago_service.get_historial_cuenta_ph_detailed(
            db, 
            empresa_id=unidad.empresa_id, 
            unidad_id=unidad.id
        )
        
        print(f"Total Movimientos: {len(result['transacciones'])}")
        print(f"Saldo Actual Calculado: {result['saldo_actual']}")
        
        pagos_con_detalle = 0
        facturas_con_detalle = 0
        
        print("\n--- Pagos con Detalle Encontrados ---")
        for m in result['transacciones']:
            # Verificar si hay detalle de pago rico
            if m['detalle_pago']:
                pagos_con_detalle += 1
                if pagos_con_detalle <= 5: # Mostrar solo primeros 5 para no saturar
                    print(f"\nFecha: {m['fecha']} | Doc: {m['id']}")
                    print(f"Monto Pago: {m['credito']}")
                    print(f"Detalle Aplicación: {m['detalle_pago']}")
                    
            if m['detalle_conceptos']:
                facturas_con_detalle += 1

        print(f"\n--- Resumen ---")
        print(f"Pagos con detalle: {pagos_con_detalle}")
        print(f"Facturas con detalle: {facturas_con_detalle}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_history()
