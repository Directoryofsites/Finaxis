import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.core.config import settings
from app.models.empresa import Empresa
from app.schemas.empresa import EmpresaUpdate

def verify_balance_update():
    engine = create_engine(settings.DATABASE_URL)
    session = Session(engine)
    
    try:
        # Find a test company (e.g. "Pruebas")
        empresa = session.query(Empresa).filter(Empresa.nit == "115588").first()
        if not empresa:
            print("Empresa de prueba (NIT 115588) no encontrada.")
            return

        print(f"Estado Inicial: Lite={empresa.is_lite_mode}, FC={empresa.saldo_facturas_venta}, DS={empresa.saldo_documentos_soporte}, NC={empresa.saldo_notas_credito}")

        # Simulate Update Payload
        update_data = EmpresaUpdate(
            is_lite_mode=True,
            saldo_facturas_venta=50,
            saldo_documentos_soporte=20,
            saldo_notas_credito=10
        )
        
        # Apply changes manually (mimicking service)
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(empresa, field, value)
            
        session.commit()
        session.refresh(empresa)
        
        print(f"Estado Final: Lite={empresa.is_lite_mode}, FC={empresa.saldo_facturas_venta}, DS={empresa.saldo_documentos_soporte}, NC={empresa.saldo_notas_credito}")
        
        if empresa.saldo_notas_credito == 10:
            print("SUCCESS: Saldo de Notas Crédito actualizado correctamente.")
        else:
            print("FAILURE: Saldo de Notas Crédito no se actualizó.")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    verify_balance_update()
