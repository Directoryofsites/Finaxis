import sys
import os
from datetime import date

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.usuario import Usuario
from app.models.empresa import Empresa
from app.models.producto import Producto
from app.models.tercero import Tercero
from app.models.bodega import Bodega
from app.models.tipo_documento import TipoDocumento
from app.services import facturacion as service_facturacion
from app.schemas import facturacion as schemas_facturacion

def debug_balance_decrement():
    db = SessionLocal()
    try:
        email = "mar1@mar.com"
        user = db.query(Usuario).filter(Usuario.email == email).first()
        if not user:
            print("User not found")
            return

        empresa_id = user.empresa_id
        empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
        
        print(f"Initial Balance: {empresa.saldo_facturas_venta}")
        initial_balance = empresa.saldo_facturas_venta
        
        # Prepare Dummy Invoice Data
        tipo_doc = db.query(TipoDocumento).filter(TipoDocumento.empresa_id == empresa_id, TipoDocumento.codigo == 'FV').first()
        tercero = db.query(Tercero).filter(Tercero.empresa_id == empresa_id).first()
        producto = db.query(Producto).filter(Producto.empresa_id == empresa_id).first()
        
        if not all([tipo_doc, tercero, producto]):
            print("Missing required data (TipoDoc, Tercero, Producto)")
            return

        payload = {
            "tipo_documento_id": tipo_doc.id,
            "beneficiario_id": tercero.id,
            "fecha": date.today(),
            "condicion_pago": "Contado",
            "bodega_id": None, 
            "items": [
                {
                    "producto_id": producto.id,
                    "cantidad": 1,
                    "precio_unitario": 100,
                    "descuento_tasa": 0
                }
            ],
            "fecha_vencimiento": date.today()
        }
        
        factura_dto = schemas_facturacion.FacturaCreate(**payload)
        
        # Run Service
        print("Creating Invoice...")
        service_facturacion.crear_factura_venta(db, factura_dto, user_id=user.id, empresa_id=empresa_id)
        
        # Check Balance AGAIN (Re-query to be sure)
        db.expire_all() # Force reload from DB
        empresa_updated = db.query(Empresa).filter(Empresa.id == empresa_id).first()
        print(f"Final Balance: {empresa_updated.saldo_facturas_venta}")
        
        if empresa_updated.saldo_facturas_venta == initial_balance - 1:
            print("SUCCESS: Balance decremented correctly.")
        else:
            print(f"FAILURE: Balance did not change as expected. (Expected {initial_balance - 1}, Got {empresa_updated.saldo_facturas_venta})")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_balance_decrement()
