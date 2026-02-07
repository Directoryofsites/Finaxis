import sys
import os
# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.services.facturacion import crear_factura_venta
from app.schemas.facturacion import FacturaCreate, FacturaItemCreate
from app.models.usuario import Usuario
from app.models.empresa import Empresa
from app.models.producto import Producto
from app.models.tercero import Tercero
from app.models.tipo_documento import TipoDocumento
from datetime import date

def test_descuentos():
    db = SessionLocal()
    try:
        # 1. Setup Data - Find existing or create dummy
        user = db.query(Usuario).first()
        empresa = db.query(Empresa).first()
        if not empresa: 
            print("No empresa found, skipping test")
            return
        
        producto = db.query(Producto).filter(Producto.empresa_id == empresa.id).first()
        tercero = db.query(Tercero).filter(Tercero.empresa_id == empresa.id).first()
        tipo_doc = db.query(TipoDocumento).filter(TipoDocumento.empresa_id == empresa.id, TipoDocumento.codigo == 'FV').first()
        
        if not (producto and tercero and tipo_doc):
            print("Missing master data. Attempting to CREATE dummy data...")
            from app.models.plan_cuenta import PlanCuenta
            
            # 1. Accounts
            cuenta = db.query(PlanCuenta).filter(PlanCuenta.empresa_id == empresa.id).first()
            if not cuenta:
                cuenta = PlanCuenta(empresa_id=empresa.id, codigo="110505", nombre="Caja General", nivel=4)
                db.add(cuenta); db.flush()
            
            # 2. Tipo Doc
            if not tipo_doc:
                tipo_doc = TipoDocumento(
                    empresa_id=empresa.id, codigo="FVT", nombre="Factura Test",
                    cuenta_caja_id=cuenta.id, cuenta_debito_cxc_id=cuenta.id,
                    cuenta_credito_cxc_id=cuenta.id, cuenta_debito_cxp_id=cuenta.id,
                    cuenta_credito_cxp_id=cuenta.id,
                    funcion_especial='FACTURA_VENTA',
                    afecta_inventario=True
                )
                db.add(tipo_doc); db.flush()

            # 3. Proveedor / Tercero
            if not tercero:
                tercero = Tercero(
                    empresa_id=empresa.id, nit="999999999", razon_social="Cliente Test",
                    direccion="Calle Falsa 123", telefono="1234567", email="test@test.com",
                    responsabilidad_fiscal='R-99-PN'
                )
                db.add(tercero); db.flush()

            # 4. Product
            from app.models.grupo_inventario import GrupoInventario
            from app.models.impuesto import TasaImpuesto
            
            if not producto:
                # Need Group
                grupo = db.query(GrupoInventario).filter(GrupoInventario.empresa_id == empresa.id).first()
                if not grupo:
                    grupo = GrupoInventario(
                        empresa_id=empresa.id, nombre="Grupo Test",
                        cuenta_ingreso_id=cuenta.id, cuenta_costo_venta_id=cuenta.id,
                        cuenta_inventario_id=cuenta.id
                    )
                    db.add(grupo); db.flush()
                
                producto = Producto(
                    empresa_id=empresa.id, codigo="PROD-TEST", nombre="Producto Test",
                    grupo_id=grupo.id, costo_promedio=500, precio_base_manual=1000,
                    es_servicio=False
                )
                db.add(producto); db.flush()
            
            # 5. Bodega
            from app.models.bodega import Bodega
            bodega = db.query(Bodega).filter(Bodega.empresa_id == empresa.id).first()
            if not bodega:
                bodega = Bodega(empresa_id=empresa.id, nombre="Bodega Test")
                db.add(bodega); db.flush()
            
            # 6. Stock
            from app.models.producto import StockBodega
            stock = db.query(StockBodega).filter(StockBodega.producto_id == producto.id, StockBodega.bodega_id == bodega.id).first()
            if not stock:
                stock = StockBodega(producto_id=producto.id, bodega_id=bodega.id, stock_actual=100)
                db.add(stock); db.flush()
            else:
                stock.stock_actual = 100
                db.flush()
                
            print("Dummy data created.")

        print(f"Testing with Emp: {empresa.id}, Prod: {producto.nombre}, Terc: {tercero.razon_social}")

        # 2. Payload
        # Scenario: 
        # Price: 1000
        # Qty: 2
        # Line Disc: 10%
        # Subtotal Line Net: 2 * 1000 * 0.9 = 1800
        # Global Disc: 180
        # Global Charge: 0
        # Net Base: 1800 - 180 = 1620.
        
        item = FacturaItemCreate(
            producto_id=producto.id,
            cantidad=2,
            precio_unitario=1000,
            descuento_tasa=10.0, # 10%
        )
        
        factura = FacturaCreate(
            tipo_documento_id=tipo_doc.id,
            beneficiario_id=tercero.id,
            fecha=date.today(),
            fecha_vencimiento=date.today(),
            centro_costo_id=None,
            bodega_id=bodega.id, 
            condicion_pago="Contado", 
            items=[item],
            descuento_global_valor=180.0,
            cargos_globales_valor=0.0
        )
        
        # Force TipoDoc to have Caja Account if needed
        if not tipo_doc.cuenta_caja_id and not tipo_doc.cuenta_debito_cxc_id:
             print("WARNING: Tipo Doc missing accounts. Selecting first available account for test.")
             from app.models.plan_cuenta import PlanCuenta
             acc = db.query(PlanCuenta).first()
             tipo_doc.cuenta_caja_id = acc.id
             tipo_doc.cuenta_debito_cxc_id = acc.id

        # 3. Execution
        print("Calling crear_factura_venta...")
        doc = crear_factura_venta(db, factura, user.id, empresa.id)
        
        print(f"Document Created: {doc.numero}")
        print(f"Global Disc Saved: {doc.descuento_global_valor}")
        
        # 4. Verification
        if doc.descuento_global_valor != 180.0:
             print(f"FAIL: Global Discount not saved correctly. Got {doc.descuento_global_valor}")
        else:
             print("PASS: Global Discount Persistence.")
        
        found_income = False
        for mov in doc.movimientos:
            # Look for income movement (Credit > 0 and Product Linked)
            if mov.credito > 0 and mov.producto_id == producto.id:
                print(f"Credit Move: {mov.credito} (Expected ~1620)")
                # Check stored discount metadata
                print(f"  Metadata Desc Tasa: {mov.descuento_tasa}")
                print(f"  Metadata Desc Val: {mov.descuento_valor}")
                
                # Verify Line Disc (200) + Prorated Global (180) = 380 total discount val?
                # Formula: total_descuento_acumulado = valor_desc_linea + dist_desc_global
                # valor_desc_linea = 2000 * 0.1 = 200.
                # dist_desc_global = 1 * 180 = 180.
                # Total = 380.
                
                if abs(float(mov.descuento_valor) - 380.0) < 1.0:
                     print("PASS: Discount Metadata Value (380).")
                else:
                     print(f"FAIL: Discount Metadata Value {mov.descuento_valor} != 380.")

                if abs(float(mov.credito) - 1620.0) < 1.0:
                    found_income = True
        
        if found_income:
            print("SUCCESS: Accounting matches expected Net Base (1620).")
        else:
            print("FAILURE: Accounting mismatch.")
            
        db.rollback() 
        print("Rolled back changes.")
        
    except Exception as e:
        print(f"Test Failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_descuentos()
