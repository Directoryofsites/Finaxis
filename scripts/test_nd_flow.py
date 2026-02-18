
import sys
import os
import json
import time
from datetime import datetime

# Setup path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.documento import Documento
from app.models.movimiento_contable import MovimientoContable
from app.models.tercero import Tercero
from app.models.configuracion_fe import ConfiguracionFE
from app.models.empresa import Empresa
from app.services.factura_electronica_service import factura_electronica_service

def run_verification():
    db = SessionLocal()
    try:
        print("--- INICIO DE VERIFICACION FLUJO NOTA DEBITO (ND) ---")
        
        # 1. Buscar Empresa y Config
        empresa = db.query(Empresa).filter(Empresa.razon_social == "Verduras la 21").first()
        if not empresa:
            print("Empresa 'Verduras la 21' no encontrada por razon_social. Intentando ID...")
            empresa = db.query(Empresa).get(134)

        if not empresa:
            print("❌ No se encontró empresa")
            return
            
        config = db.query(ConfiguracionFE).filter_by(empresa_id=empresa.id).first()
        if not config or not config.habilitado:
            print("❌ Empresa no habilitada para FE")
            if config:
                config.habilitado = True
                db.commit()
                print("   -> Habilitada temporalmente para prueba")
            else:
                return

        # 2. Buscar Cliente y Usuario
        cliente = db.query(Tercero).filter(Tercero.nit == "41411660").first() # Jaime Muñoz
        if not cliente:
            print("❌ No se encontró cliente Jaime Muñoz")
            return
        
        # Dynamic User Fetch
        from app.models.usuario import Usuario
        usuario = db.query(Usuario).first()
        usuario_id = usuario.id if usuario else 1
        print(f"   Usuario ID: {usuario_id}")

        # Dynamic PlanCuenta Fetch
        from app.models.plan_cuenta import PlanCuenta
        cuenta_ingreso = db.query(PlanCuenta).filter(PlanCuenta.codigo.like('4%')).first()
        if not cuenta_ingreso:
             print("❌ No se encontró una cuenta de ingreso (4xxx)")
             return
        print(f"   Cuenta Ingreso: {cuenta_ingreso.codigo}")

        # Dynamic TipoDocumento Fetch
        from app.models.documento import TipoDocumento
        
        # Factura Venta Search
        td_fe = db.query(TipoDocumento).filter(
            (TipoDocumento.codigo == '01') | 
            (TipoDocumento.nombre.ilike('%Factura de Venta%'))
        ).first()
        
        # Nota Debito Search 
        td_nd = db.query(TipoDocumento).filter(
            (TipoDocumento.codigo == '92') | 
            (TipoDocumento.nombre.ilike('%Nota Debito%')) |
            (TipoDocumento.nombre.ilike('%Nota Débito%'))
        ).first()

        if not td_fe:
             print("❌ No se encontró TipoDocumento 'Factura de Venta'")
             return
        if not td_nd:
             print("❌ No se encontró TipoDocumento 'Nota Débito'. Intentando crear uno...")
             # Create generic ND Type if missing
             td_nd = TipoDocumento(
                 codigo='92', 
                 nombre='Nota Débito de Prueba', 
                 empresa_id=empresa.id,
                 funcion_especial='nota_debito' 
             )
             db.add(td_nd)
             db.commit()
             print(f"   -> Creado TipoDocumento ND: {td_nd.id}")

        print(f"   Tipos Doc: FE={td_fe.id}, ND={td_nd.id}")


        # 3. Crear FACTURA PADRE
        print("\n1. Creando FACTURA DE VENTA (Padre)...")
        
        # Calcular numero
        last_doc = db.query(Documento).filter(
            Documento.empresa_id == empresa.id, 
            Documento.tipo_documento_id == td_fe.id
        ).order_by(Documento.numero.desc()).first()
        next_num_fe = (last_doc.numero + 1) if last_doc else 1000

        nueva_fe = Documento(
            empresa_id=empresa.id,
            beneficiario_id=cliente.id,
            tipo_documento_id=td_fe.id,
            numero=next_num_fe,
            fecha=datetime.now().date(),
            # fecha_vencimiento omitted as in test_full_flow.py
            observaciones="Factura Base para ND Automatica",
            usuario_creador_id=usuario_id,
            estado="ACTIVO",
            fecha_operacion=datetime.now()
        )
        db.add(nueva_fe)
        db.commit()
        
        # Item de Factura
        mov_fe = MovimientoContable(
            documento_id=nueva_fe.id,
            tercero_id=cliente.id,
            concepto="Servicio Base",
            cuenta_id=cuenta_ingreso.id, 
            debito=0,
            credito=20000, # Venta = Credito
            producto_id=1634, # Arracacha
            cantidad=2
        )
        db.add(mov_fe)
        db.commit()
        
        print(f"   Emitiendo Factura #{nueva_fe.numero}...")
        resp_fe = factura_electronica_service.emitir_factura(db, nueva_fe.id, usuario_id)
        
        if not resp_fe.get("success"):
            print(f"❌ Error emitiendo Factura Padre: {resp_fe.get('error')}")
            print(f"   Detalles: {resp_fe.get('details')}")
            return 
            
        print(f"   Factura Emitida ÉXITO. CUFE: {resp_fe.get('cufe')}")
        print(f"   Provider ID: {resp_fe.get('provider_id')}")
        
        # Ensure provider_id is saved
        if not nueva_fe.provider_id:
             db.refresh(nueva_fe)
             
        
        # Wait a bit
        time.sleep(2)
        
        # 4. Crear NOTA DEBITO
        print("\n2. Creando NOTA DEBITO asociada...")
        
        # Calcular numero ND
        last_nd_doc = db.query(Documento).filter(
            Documento.empresa_id == empresa.id, 
            Documento.tipo_documento_id == td_nd.id
        ).order_by(Documento.numero.desc()).first()
        next_num_nd = (last_nd_doc.numero + 1) if last_nd_doc else 2000

        # Nota Debito aumenta el valor de la deuda (Debito al cliente, Credito al Ingreso)
        nueva_nd = Documento(
            empresa_id=empresa.id,
            beneficiario_id=cliente.id,
            tipo_documento_id=td_nd.id, # TIPO ND
            documento_referencia_id=nueva_fe.id, # LINK PADRE
            numero=next_num_nd,
            fecha=datetime.now().date(),
            observaciones="NOTA DEBITO PRUEBA AUTOMATICA",
            usuario_creador_id=usuario_id,
            estado="ACTIVO",
            fecha_operacion=datetime.now()
        )
        db.add(nueva_nd)
        db.commit()
        
        # Item de Nota Debito (Similiar a Venta, Credito a Ingreso)
        mov_nd = MovimientoContable(
            documento_id=nueva_nd.id,
            tercero_id=cliente.id,
            concepto="Ajuste Mayor Valor",
            cuenta_id=cuenta_ingreso.id,
            debito=0,
            credito=5000, # Nota Debito aumenta ventas/ingreso
            producto_id=1634,
            cantidad=1
        )
        db.add(mov_nd)
        db.commit()
        
        print(f"   Emitiendo Nota Débito #{nueva_nd.numero}...")
        resp_nd = factura_electronica_service.emitir_factura(db, nueva_nd.id, usuario_id)
        
        if resp_nd.get("success"):
            print("\n✅ PRUEBA EXITOSA: Nota Débito emitida correctamente.")
            print(f"   CUDE: {resp_nd.get('cufe')}")
            print(f"   XML: {resp_nd.get('xml_url')}")
        else:
            print("\n❌ PRUEBA FALLIDA: Error al emitir Nota Débito.")
            print(f"   Error: {resp_nd.get('error')}")
            print(f"   Detalles: {resp_nd.get('details')}")

    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    run_verification()
