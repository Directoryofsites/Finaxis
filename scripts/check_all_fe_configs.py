import sys
import os

sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.configuracion_fe import ConfiguracionFE

def check_all_configs():
    session = SessionLocal()
    try:
        configs = session.query(ConfiguracionFE).all()
        print(f"Total configuraciones: {len(configs)}")
        for c in configs:
            print(f"ID: {c.id} | Empresa: {c.empresa_id} | RangoID: {c.rango_desde} | Habilitado: {c.habilitado}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_all_configs()
