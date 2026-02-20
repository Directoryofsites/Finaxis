
import sys
import os
sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.configuracion_fe import ConfiguracionFE

def fix_nd_range():
    session = SessionLocal()
    try:
        config = session.query(ConfiguracionFE).filter_by(empresa_id=134).first()
        if config:
            print(f"Current ND Range: {config.nd_rango_id}")
            config.nd_rango_id = 9
            session.commit()
            print(f"Updated ND Range to: {config.nd_rango_id}")
        else:
            print("Config not found")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    fix_nd_range()
