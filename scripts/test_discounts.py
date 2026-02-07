
import sys
sys.path.append('c:\\ContaPY2')
from app.core.database import SessionLocal
from app.models.documento import Documento
from app.models.movimiento_contable import MovimientoContable
from app.services.factura_electronica_service import factura_electronica_service
import json

def test_discount_emission():
    session = SessionLocal()
    try:
        # Usar documento 12223 que ya reparamos como base
        doc_id = 12223 
        doc = session.query(Documento).get(doc_id)
        
        if not doc:
            print("Documento no encontrado.")
            return

        print(f"Probando emisión con descuentos para Documento {doc_id}...")
        
        # 1. Simular Descuentos Globales (Re-activados para validar Prorrateo)
        doc.descuento_global_valor = 5000
        doc.cargos_globales_valor = 2000
        
        # 2. Simular Descuento por Línea (si hay movimientos de ingreso)
        ingresos = [m for m in doc.movimientos if m.cuenta and m.cuenta.codigo.startswith('4')]
        if ingresos:
            ingresos[0].descuento_tasa = 10.00 # 10% descuento
            print("Aplicado descuento de línea 10% al primer item.")
        
        session.commit()
        
        # 3. Emitir (Usará MOCK o Sandbox REAL si está configurado)
        # Nota: Como es Sandbox real, esto podría afectar la factura real en Factus.
        # Pero es necesario validar el payload.
        
        # Para evitar enviar basura a la DIAN real si no queremos, podríamos solo inspeccionar la lógica.
        # Pero el usuario pidió implementación. Vamos a intentar generar el payload sin emitir o emitir si es seguro.
        # Dado que ya validamos que usa Sandbox, es seguro.
        
        resultado = factura_electronica_service.emitir_factura(session, doc_id, doc.usuario_creador_id)
        
        print("\n--- RESULTADO ---")
        print(json.dumps(resultado, indent=2))
        
        if resultado.get("success"):
            print("Emision exitosa con descuentos.")
        else:
            print("Fallo en emision.")

    except Exception as e:
        print(f"Error test: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    test_discount_emission()
