from app.core.database import SessionLocal
from app.services.propiedad_horizontal import pago_service
from app.models.propiedad_horizontal import PHUnidad
from datetime import date, timedelta
import json

def verify_history_breakdown():
    db = SessionLocal()
    try:
        unidad = db.query(PHUnidad).first()
        if not unidad:
            print("No hay unidades.")
            return

        print(f"Probando con Unidad: {unidad.codigo} (ID: {unidad.id}) Empresa: {unidad.empresa_id}")
        
        # Fecha Inicio febrero 2025 para forzar un saldo inicial no nulo
        # Asumiendo que hay datos en enero
        f_inicio = date(2025, 2, 1)

        result = pago_service.get_historial_cuenta_ph_detailed(
            db, 
            empresa_id=unidad.empresa_id, 
            unidad_id=unidad.id,
            fecha_inicio=f_inicio
        )
        
        print(f"Keys returned: {list(result.keys())}")
        if 'saldo_anterior_detalle' in result:
             print(f"Saldo Anterior Detalle Items: {len(result['saldo_anterior_detalle'])}")
             for sub in result['saldo_anterior_detalle']:
                 print(f"  [HEADER] {sub['concepto']}: ${sub['valor']}")
        
        # Ver si el primer item es SALDO INICIAL y tiene desglose
        if result['transacciones']:
            primer_mov = result['transacciones'][0]
            print(f"Primer Movimiento: {primer_mov['tipo_documento']}")
            print(f"Concepto: {primer_mov['detalle']}")
            print(f"Saldo Acumulado (Item): {primer_mov['saldo_acumulado']}")
            
            if primer_mov['sub_items']:
                print("\n>>> DESGLOSE SALDO INICIAL ENCONTRADO <<<")
                for sub in primer_mov['sub_items']:
                    print(f" - {sub['concepto']}: ${sub['valor']:,.0f}")
            else:
                 print("\nXXX NO HAY DESGLOSE EN SALDO INICIAL XXX")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_history_breakdown()
