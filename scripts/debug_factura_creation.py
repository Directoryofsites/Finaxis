# scripts/debug_factura_creation.py
import sys
import os
from datetime import date

sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.services import facturacion as service_facturacion
from app.schemas import facturacion as schemas_facturacion
from app.models.usuario import Usuario
from app.models.empresa import Empresa
from app.models.tipo_documento import TipoDocumento
from app.models.tercero import Tercero
from app.models.bodega import Bodega
from app.models.producto import Producto
from fastapi import HTTPException

def debug_creation():
    db = SessionLocal()
    try:
        email = "mar1@mar.com"
        user = db.query(Usuario).filter(Usuario.email == email).first()
        if not user:
            print("User not found")
            return

        empresa_id = user.empresa_id
        print(f"User: {user.email}, Empresa ID: {empresa_id}")
        
        # Fetch Dependencies
        tipo_doc = db.query(TipoDocumento).filter(
            TipoDocumento.empresa_id == empresa_id,
            TipoDocumento.afecta_inventario == True
        ).first()
        
        if not tipo_doc:
            print("No valid TipoDocumento found!")
            return
            
        bodega = db.query(Bodega).filter(Bodega.empresa_id == empresa_id).first()
        if not bodega:
            print("No valid Bodega found!")
            # Proceeding with None to test validation if needed, but standard flow needs one.
            
        tercero = db.query(Tercero).filter(Tercero.empresa_id == empresa_id).first()
        producto = db.query(Producto).filter(Producto.empresa_id == empresa_id).first()
        
        print(f"Data: TipoDoc={tipo_doc.id}, Bodega={bodega.id if bodega else 'None'}, Tercero={tercero.id}, Producto={producto.id}")
        
        print(f"--- TIPO DOC CONFIG CHECK ---")
        print(f"Cuenta CXC Debito: {tipo_doc.cuenta_debito_cxc_id}")
        print(f"Cuenta Caja: {tipo_doc.cuenta_caja_id}")
        if not tipo_doc.cuenta_debito_cxc_id:
             print("WARNING: TipoDoc has NO CXC Account configured!")

        # Construct Payload FORCE NULL for robustness test
        payload_dict = {
            "tipo_documento_id": tipo_doc.id,
            "beneficiario_id": tercero.id,
            "fecha": date.today(),
            "condicion_pago": "Crédito",
            "bodega_id": None, # FORCE NULL to test auto-select
            "descuento_global_valor": 0,
            "cargos_globales_valor": 0,
            "items": [
                {
                    "producto_id": producto.id,
                    "cantidad": 1,
                    "precio_unitario": 1000,
                    "descuento_tasa": 0
                }
            ],
            # "fecha_vencimiento": date.today() # Intentionally COMMENTED to test auto-fill
        }
        
        # Test Case 1: Missing Fecha Vencimiento & Bodega (Should now SUCCESS or fail at stock)
        print("\n--- TEST ROBUSTNESS: Missing Fecha Vencimiento & Bodega ---")
        try:
            factura_dto = schemas_facturacion.FacturaCreate(**payload_dict)
            
            # Run the service!
            new_inv = service_facturacion.crear_factura_venta(db, factura_dto, user_id=user.id, empresa_id=empresa_id)
            print(f"SUCCESS: Invoice Created with Auto-Filled Data! ID: {new_inv.id}")
            print(f"   -> Bodega ID Used: {new_inv.movimientos[0].bodega_id if new_inv.movimientos else 'Unknown'}") 
            # Note: movimientos don't store bodega directly in this model usually, but stock move does.
            # We check if it passed.
            
            db.rollback()
            print("Rolled back successfully")

        except Exception as e:
            print(f"FAILED: {e}")
            if isinstance(e, HTTPException):
                print(f"DETAIL: {e.detail}")
            import traceback
            traceback.print_exc()
        except Exception as e:
             print(e)
             
    except Exception as e:
        print(f"SETUP ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_creation()
