import sys
import os
import json
import time
from datetime import datetime
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.documento import Documento
from app.models.empresa import Empresa
from app.models.tercero import Tercero
from app.models.configuracion_fe import ConfiguracionFE
from app.models.movimiento_contable import MovimientoContable
from app.models.tipo_documento import TipoDocumento
from app.models.usuario import Usuario
from app.models.plan_cuenta import PlanCuenta
from app.services.factura_electronica_service import factura_electronica_service

def run_verification():
    db = SessionLocal()
    try:
        print("--- INICIANDO VERIFICACIÓN COMPLETA (Factura -> Nota) ---")
        
        # 1. Configurar Empresa
        # Ajuste: Usar el campo correcto. Si nombre no existe, probar razon_social o identificacion.
        # Asumiendo razon_social por convención Colombia, o listamos todas.
        empresa = db.query(Empresa).filter(Empresa.razon_social == "Verduras la 21").first()
        if not empresa:
             print("Empresa 'Verduras la 21' no encontrada por razon_social. Intentando ID...")
             empresa = db.query(Empresa).get(134) # ID conocido de pruebas anteriores

        config = db.query(ConfiguracionFE).filter_by(empresa_id=empresa.id).first()
        if not config or not config.api_token:
            print("Configuración FE incompleta.")
            return

        # 2. EMITIR FACTURA DE VENTA NUEVA
        print("\n1. Creando Factura de Venta...")
        cliente = db.query(Tercero).filter(Tercero.es_cliente == True, Tercero.email != None).first()
        usuario = db.query(Usuario).first()
        usuario_id = usuario.id if usuario else 1
        cuenta = db.query(PlanCuenta).first()
        cuenta_id = cuenta.id if cuenta else 1
        
        # Obtener IDs de Tipos de Documento
        # Busqueda mas laxa para evitar problemas de tildes
        tipo_factura = db.query(TipoDocumento).filter(TipoDocumento.codigo == 'FV').first()
        if not tipo_factura:
             tipo_factura = db.query(TipoDocumento).filter(TipoDocumento.nombre.ilike("%Factura%Venta%")).first()
             
        tipo_nc = db.query(TipoDocumento).filter(TipoDocumento.codigo == '91').first()
        if not tipo_nc:
             tipo_nc = db.query(TipoDocumento).filter(TipoDocumento.nombre.ilike("%Nota%Cre%")).first()
        
        if not tipo_factura or not tipo_nc:
             print("Tipos de documento no encontrados.")
             # Fallback IDs si no coinciden nombres (ajustar según DB real)
             id_factura = tipo_factura.id if tipo_factura else 1 
             id_nc = tipo_nc.id if tipo_nc else 2
        else:
             id_factura = tipo_factura.id
             id_nc = tipo_nc.id

        # Calcular siguiente numero
        last_doc = db.query(Documento).filter(
            Documento.empresa_id == empresa.id, 
            Documento.tipo_documento_id == id_factura
        ).order_by(Documento.numero.desc()).first()
        
        next_num = (last_doc.numero + 1) if last_doc else (config.rango_desde or 1)
        
        nueva_factura = Documento(
            empresa_id=empresa.id,
            tipo_documento_id=id_factura, # Factura Venta
            numero=next_num,
            fecha=datetime.now().date(),
            beneficiario_id=cliente.id if cliente else None,
            observaciones="PRUEBA AUTOMATICA PROVIDER_ID",
            usuario_creador_id=usuario_id,
            fecha_operacion=datetime.now(),
            estado="ACTIVO",
            # provider_id=None # Default
        )
        db.add(nueva_factura)
        db.commit()
        db.refresh(nueva_factura)
        
        # Movimiento dummy
        mov = MovimientoContable(
            documento_id=nueva_factura.id,
            cuenta_id=cuenta_id, # Dummy
            tercero_id=cliente.id,
            concepto="Venta Prueba",
            debito=0,
            credito=10000,
            producto_id=1634, # Arracacha
            cantidad=1
        )
        db.add(mov)
        db.commit()
        
        print(f"   Factura creada en BD: #{nueva_factura.numero} (ID: {nueva_factura.id})")
        print("   Emitiendo Factura a Factus...")
        
        resp_factura = factura_electronica_service.emitir_factura(db, nueva_factura.id, usuario_id)
        
        if not resp_factura.get("success"):
            print(f"   ERROR Emisión Factura: {resp_factura.get('error')}")
            print(f"   Detalles: {resp_factura.get('details')}")
            return
            
        print(f"   Factura Emitida ÉXITO. CUFE: {resp_factura.get('cufe')}")
        print(f"   Provider ID: {resp_factura.get('provider_id')}")
        
        if not resp_factura.get('provider_id'):
            print("   CRITICO: No se recibió provider_id de Factus.")
            # Intentar leer de BD por si se guardó
            db.refresh(nueva_factura)
            print(f"   Provider ID en BD: {nueva_factura.provider_id}")
            if not nueva_factura.provider_id:
                return

        # No actualizamos config, se calcula dinamicamente

        # Esperar un poco
        time.sleep(2)

        # 3. EMITIR NOTA CREDITO
        print("\n2. Creando Nota Crédito asociada...")
        
        nueva_nc = Documento(
            empresa_id=empresa.id,
            tipo_documento_id=id_nc, # Nota Credito
            numero=99999, # Dummy
            fecha=datetime.now().date(),
            beneficiario_id=cliente.id,
            observaciones="NOTA CREDITO PRUEBA AUTOMATICA",
            usuario_creador_id=usuario_id,
            documento_referencia_id=nueva_factura.id, # Link al padre
            fecha_operacion=datetime.now(),
            estado="ACTIVO"
        )
        db.add(nueva_nc)
        db.commit()
        
        # Movimiento de la nota
        mov_nc = MovimientoContable(
            documento_id=nueva_nc.id,
            cuenta_id=cuenta_id,
            tercero_id=cliente.id,
            concepto="Reversión Prueba",
            debito=10000,
            credito=0,
            producto_id=1634,
            cantidad=1
        )
        db.add(mov_nc)
        db.commit()
        
        print("   Emitiendo Nota Crédito...")
        resp_nc = factura_electronica_service.emitir_factura(db, nueva_nc.id, usuario_id)
        
        if resp_nc.get("success"):
            print("\n✅ PRUEBA EXITOSA: Nota Crédito emitida correctamente.")
            print(f"   CUDE: {resp_nc.get('cufe')}")
            print(f"   XML: {resp_nc.get('xml_url')}")
        else:
            print("\n❌ PRUEBA FALLIDA: Error al emitir Nota Crédito.")
            print(f"   Error: {resp_nc.get('error')}")
            print(f"   Detalles: {resp_nc.get('details')}")

    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    run_verification()
