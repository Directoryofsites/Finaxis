import sys
import os
import json
from datetime import datetime
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.documento import Documento
from app.models.empresa import Empresa
from app.models.tercero import Tercero
from app.models.tipo_documento import TipoDocumento
from app.models.configuracion_fe import ConfiguracionFE
from app.services.factura_electronica_service import factura_electronica_service

def test_emit_credit_note():
    db = SessionLocal()
    try:
        # 1. Buscar una empresa habilitada
        # Usamos ID 134 (Verduras la 21) que parece ser la que el usuario usa para pruebas
        empresa_id = 134 
        empresa = db.query(Empresa).get(empresa_id)
        if not empresa:
            print("Empresa 134 no encontrada, buscando cualquiera...")
            empresa = db.query(Empresa).first()
            empresa_id = empresa.id

        print(f"Usando Empresa: {empresa.razon_social}")

        # 2. Buscar Configuración FE
        config = db.query(ConfiguracionFE).filter_by(empresa_id=empresa_id).first()
        if not config:
            print("Empresa no tiene configuración FE.")
            return

        # TEMPORAL: Asegurar rango para la prueba
        if not config.nc_rango_id:
            config.nc_rango_id = 999 # ID Dummy
            db.commit()
            print("Configurado nc_rango_id temporal = 999")

        # 3. Buscar/Crear Factura Referencia (Debe tener CUFE)
        # Buscamos una aceptada
        factura = db.query(Documento).filter(
            Documento.empresa_id == empresa_id,
            Documento.dian_estado == 'ACEPTADO',
            Documento.dian_cufe.isnot(None)
        ).order_by(Documento.id.desc()).first()

        if not factura:
            print("No se encontró una factura aceptada para usar de referencia. Creando MOCK...")
            # Aquí podríamos crear una, pero para el test rápido asumimos que el usuario ya emitió alguna.
            # Si no, fallará la validación lógica del servicio.
            return

        print(f"Factura Referencia: {factura.numero} (CUFE: {factura.dian_cufe})")

        # 4. Crear Nota Crédito en BD
        # Buscar Tipo NC
        tipo_nc = db.query(TipoDocumento).filter_by(empresa_id=empresa_id, codigo='91').first()
        if not tipo_nc:
            print("No existe Tipo Documento 91 (Nota Crédito)")
            return

        # Copiar datos básicos
        nueva_nc = Documento(
            empresa_id=empresa_id,
            tipo_documento_id=tipo_nc.id,
            numero=999999, # Dummy number
            fecha=datetime.now().date(),
            beneficiario_id=factura.beneficiario_id,
            centro_costo_id=factura.centro_costo_id,
            observaciones="PRUEBA AUTO GNERADA NOTA CREDITO",
            usuario_creador_id=factura.usuario_creador_id,
            # REFERENCIA
            documento_referencia_id=factura.id,
            estado='ACTIVO'
        )
        db.add(nueva_nc)
        db.commit()
        db.refresh(nueva_nc)
        print(f"Nota Crédito creada en BD: ID {nueva_nc.id}")

        # NOTA: No le agregamos movimientos todavía.
        # El servicio fallará si no tiene movimientos validos.
        # Agreguemos un movimiento dummy clonado de la factura pero invertido?
        # En la factura venta: Credito Ingreso. En NC: Debito Ingreso.
        
        # Clonamos un movimiento de la factura
        mov_ref = factura.movimientos[0] if factura.movimientos else None
        if mov_ref:
            from app.models.movimiento_contable import MovimientoContable
            
            # Asumimos que mov_ref es el ingreso (Credito)
            # Para la NC, hacemos un Debito
            valor = float(mov_ref.credito) if mov_ref.credito else 0
            if valor == 0 and mov_ref.debito: valor = float(mov_ref.debito) # Fallback
            
            nuevo_mov = MovimientoContable(
                documento_id=nueva_nc.id,
                cuenta_id=mov_ref.cuenta_id,
                tercero_id=mov_ref.tercero_id,
                concepto="Reversión Prueba", # FIXED: detalle -> concepto
                debito=valor,
                credito=0,
                producto_id=mov_ref.producto_id,
                cantidad=mov_ref.cantidad
            )
            db.add(nuevo_mov)
            db.commit()
            print("Movimiento contable agregado a la NC.")
        else:
            print("La factura referencia no tiene movimientos.")

        # 5. Emitir
        print("Emitiendo Nota Crédito...")
        resultado = factura_electronica_service.emitir_factura(db, nueva_nc.id, 1)
        print("Resultado Emisión:")
        print(json.dumps(resultado, indent=2))

    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_emit_credit_note()
