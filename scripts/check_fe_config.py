import sys
import os

sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.configuracion_fe import ConfiguracionFE

def check_config():
    session = SessionLocal()
    try:
        empresa_id = 218
        config = session.query(ConfiguracionFE).filter_by(empresa_id=empresa_id).first()
        if config:
            print(f"Config ID: {config.id}")
            print(f"Ambiente: {config.ambiente}")
            print(f"Rango Desde (usado como ID): {config.rango_desde}")
            print(f"Habilitado: {config.habilitado}")
        else:
            print("No se encontró configuración para la empresa 218")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_config()
