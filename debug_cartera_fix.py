
import sys
import os

# Ajustar path
sys.path.append("c:/ContaPY2")

from app.core.database import SessionLocal
from app.services import cartera
from app.models import Documento, MovimientoContable, AplicacionPago, Tercero
from app.models.propiedad_horizontal import PHUnidad
from sqlalchemy import func

def debug_cartera_ph(unidad_codigo):
    db = SessionLocal()
    try:
        print(f"--- DEBUGGING UNIDAD {unidad_codigo} ---")
        
        # 1. Buscar Unidad
        unidad = db.query(PHUnidad).filter(PHUnidad.codigo == unidad_codigo).first()
        if not unidad:
            print("Unidad no encontrada")
            return

        tercero_id = unidad.propietario_principal_id
        empresa_id = unidad.empresa_id
        print(f"Unidad ID: {unidad.id}, Propietario ID: {tercero_id}, Empresa ID: {empresa_id}")
        
        if not tercero_id:
            print("Sin propietario")
            return

        # 2. Listar Documentos del Propietario
        docs = db.query(Documento).filter(
            Documento.beneficiario_id == tercero_id,
            Documento.empresa_id == empresa_id,
            Documento.anulado == False
        ).order_by(Documento.fecha).all()
        
        print("\n--- DOCUMENTOS ENCONTRADOS ---")
        cuentas_cxc = cartera.get_cuentas_especiales_ids(db, empresa_id, 'cxc')
        print(f"Cuentas CXC IDs: {cuentas_cxc}")

        for d in docs:
            impacto = 0
            for m in d.movimientos:
                if m.cuenta_id in cuentas_cxc:
                    impacto += (m.debito - m.credito)
            
            print(f"ID: {d.id} | Fecha: {d.fecha} | Numero: {d.numero} | Tipo: {d.tipo_documento.nombre} | Impacto CXC: {impacto}")

        # 3. Ejecutar Recalculo
        print("\n--- EJECUTANDO RECALCULO ---")
        cartera.recalcular_aplicaciones_tercero(db, tercero_id, empresa_id)
        
        # 4. Verificar Aplicaciones
        print("\n--- APLICACIONES RESULTANTES ---")
        aplicaciones = db.query(AplicacionPago).join(Documento, AplicacionPago.documento_factura_id == Documento.id).filter(
            Documento.beneficiario_id == tercero_id
        ).all()
        
        for app in aplicaciones:
            print(f"Factura {app.documento_factura_id} <--- Pago {app.documento_pago_id} : Monto {app.valor_aplicado}")

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Extraemos el codigo de la imagen: b 5 / 503
    debug_cartera_ph("b 5 / 503") 
