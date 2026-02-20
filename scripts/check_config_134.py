
import sys
import os
import json

sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.configuracion_fe import ConfiguracionFE

def check_config():
    session = SessionLocal()
    try:
        empresa_id = 134
        config = session.query(ConfiguracionFE).filter_by(empresa_id=empresa_id).first()
        if not config:
            print(f"No hay configuración para la empresa {empresa_id}")
            return
            
        print(f"Configuración para Empresa 134:")
        print(f"  Ambiente: {config.ambiente}")
        print(f"  Habilitado: {config.habilitado}")
        print(f"  Factura Rango ID: {config.factura_rango_id}")
        print(f"  DS Rango ID: {config.ds_rango_id}")
        print(f"  NC Rango ID: {config.nc_rango_id}")
        print(f"  ND Rango ID: {config.nd_rango_id}")
        print(f"  Prefijo: {config.prefijo}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_config()
