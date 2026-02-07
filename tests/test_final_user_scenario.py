
import sys
import os
import json
from datetime import date

# Add root to python path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.models.tercero import Tercero
from app.models.producto import Producto, StockBodega
from app.models.bodega import Bodega
from app.models.tipo_documento import TipoDocumento
from app.models.configuracion_fe import ConfiguracionFE
from app.models.impuesto import TasaImpuesto
from app.services.facturacion import crear_factura_venta
from app.schemas.facturacion import FacturaCreate, FacturaItemCreate
from app.services.factura_electronica_service import factura_electronica_service

def test_final_scenario():
    db = SessionLocal()
    
    # Setup Log
    log_file = open("final_validation.txt", "w", encoding="utf-8")
    def log(msg):
        print(msg, flush=True)
        log_file.write(str(msg) + "\n")
        log_file.flush()

    try:
        # 1. Setup Data
        user = db.query(Usuario).first()
        empresa = db.query(Empresa).first() 
        if not empresa: return

        # Ensure Accounting Plan and Defaults
        from app.models.plan_cuenta import PlanCuenta
        
        def get_or_create_account(code, name, type_account):
            acc = db.query(PlanCuenta).filter_by(empresa_id=empresa.id, codigo=code).first()
            if not acc:
                acc = PlanCuenta(empresa_id=empresa.id, codigo=code, nombre=name, nivel=4)
                db.add(acc); db.flush()
            return acc

        cta_ingreso = get_or_create_account("413501", "Ingresos Test", "CREDITO")
        cta_cxc = get_or_create_account("130505", "Clientes Nacionales", "DEBITO")
        cta_iva = get_or_create_account("240801", "IVA Generado", "CREDITO")
        cta_inv = get_or_create_account("143501", "Mercancia", "DEBITO")
        cta_costo = get_or_create_account("613501", "Costo Ventas", "DEBITO")

        empresa.cuenta_por_cobrar_id = cta_cxc.id
        db.flush()

        tipo_doc = db.query(TipoDocumento).filter(TipoDocumento.empresa_id==empresa.id).first()
        tercero = db.query(Tercero).filter(Tercero.empresa_id==empresa.id).first()
        bodega = db.query(Bodega).filter(Bodega.empresa_id==empresa.id).first()
        
        # 2. Setup Products (Papa, Pollo, Frijol)
        # Papa: 990, IVA 19%
        # Pollo: 2850, Exempt (0%)
        # Frijol: 768, IVA 5%
        
        # Taxes
        iva_19 = db.query(TasaImpuesto).filter_by(empresa_id=empresa.id, tasa=0.19).first()
        if not iva_19: 
            iva_19 = TasaImpuesto(empresa_id=empresa.id, nombre="IVA 19%", tasa=0.19, cuenta_id=cta_iva.id)
            db.add(iva_19); db.flush()
        else:
            iva_19.cuenta_id = cta_iva.id

        iva_5 = db.query(TasaImpuesto).filter_by(empresa_id=empresa.id, tasa=0.05).first()
        if not iva_5: 
            iva_5 = TasaImpuesto(empresa_id=empresa.id, nombre="IVA 5%", tasa=0.05, cuenta_id=cta_iva.id)
            db.add(iva_5); db.flush()
        else:
             iva_5.cuenta_id = cta_iva.id
        
        iva_0 = db.query(TasaImpuesto).filter_by(empresa_id=empresa.id, tasa=0.0).first()
        if not iva_0: 
            iva_0 = TasaImpuesto(empresa_id=empresa.id, nombre="Exento", tasa=0.0, cuenta_id=cta_iva.id)
            db.add(iva_0); db.flush()
        
        def create_prod_mock(code, name, tax_id):
            p = db.query(Producto).filter_by(empresa_id=empresa.id, codigo=code).first()
            if not p:
                p = Producto(
                    empresa_id=empresa.id, codigo=code, nombre=name, 
                    impuesto_iva_id=tax_id, precio_base_manual=1000, 
                    es_servicio=False
                )
                db.add(p); db.flush()
            else:
                p.impuesto_iva_id = tax_id
            
            # Ensure Group
            from app.models.grupo_inventario import GrupoInventario
            if not p.grupo_id:
                g = db.query(GrupoInventario).filter_by(empresa_id=empresa.id).first()
                if not g:
                    g = GrupoInventario(empresa_id=empresa.id, nombre="Grupo Test", cuenta_ingreso_id=cta_ingreso.id, cuenta_inventario_id=cta_inv.id, cuenta_costo_id=cta_costo.id)
                    db.add(g); db.flush()
                p.grupo_id = g.id
            else:
                p.grupo_inventario.cuenta_ingreso_id = cta_ingreso.id

            # Stock
            s = db.query(StockBodega).filter_by(producto_id=p.id, bodega_id=bodega.id).first()
            if not s:
                s = StockBodega(producto_id=p.id, bodega_id=bodega.id, stock_actual=1000)
                db.add(s)
            else:
                s.stock_actual = 1000
            
            db.flush()
            return p

        prod_papa = create_prod_mock("P APA", "Papa", iva_19.id)
        prod_pollo = create_prod_mock("POLLO", "Pollo", iva_0.id)
        prod_frijol = create_prod_mock("FRIJOL", "Frijol", iva_5.id)


        # 3. Create Invoice
        # Papa: 20 un, 990, 50% Disc
        # Pollo: 20 un, 2850, 0%
        # Frijol: 20 un, 768, 0%
        
        items = [
            FacturaItemCreate(producto_id=prod_papa.id, cantidad=20, precio_unitario=990, descuento_tasa=50.0),
            FacturaItemCreate(producto_id=prod_pollo.id, cantidad=20, precio_unitario=2850, descuento_tasa=0.0),
            FacturaItemCreate(producto_id=prod_frijol.id, cantidad=20, precio_unitario=768, descuento_tasa=0.0)
        ]
        
        factura_in = FacturaCreate(
            tipo_documento_id=tipo_doc.id,
            beneficiario_id=tercero.id,
            fecha=date.today(),
            fecha_vencimiento=date.today(),
            bodega_id=bodega.id, 
            condicion_pago="Contado", 
            items=items,
            descuento_global_valor=0.0,
            cargos_globales_valor=0.0
        )

        log("Creating Invoice (User Scenario)...")
        doc = crear_factura_venta(db, factura_in, user.id if user else 1, empresa.id)
        log(f"Invoice Created: {doc.id}")
        
        # Check Totals in DB
        # Calculate total from CXC movements (Debits)
        total_factura = sum(m.debito for m in doc.movimientos if m.debito)
        
        log(f"DB Total Calculated: {total_factura}")
        
        if abs(total_factura - 84909.0) < 1.0:
            log("SUCCESS: DB Total matches 84909.")
        else:
            log(f"FAIL: DB Total {total_factura} != 84909.")

        # 4. Emit FE
        log("-" * 50)
        log("Emitting FE...")
        
        import io
        from contextlib import redirect_stdout
        
        f = io.StringIO()
        with redirect_stdout(f):
             factura_electronica_service.emitir_factura(db, doc.id, user.id if user else 1)
        
        output = f.getvalue()
        log("CAPTURED JSON PARTIAL:")
        import re
        match = re.search(r'DEBUG PAYLOAD A FACTUS:\s*({.*})', output, re.DOTALL)
        if match:
             # Just verify totals in JSON if possible, or visually check
             log(match.group(1)[:2000] + "...") # Log intro
        
        db.rollback()
        log("Rollback performed.")

    except Exception as e:
        log(f"Error: {e}")
        import traceback
        traceback.print_exc(file=log_file)
        db.rollback()
    finally:
        db.close()
        log_file.close()

if __name__ == "__main__":
    test_final_scenario()
