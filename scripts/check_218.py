
import sys
sys.path.append('c:\\ContaPY2')
from app.core.database import SessionLocal
from app.models.configuracion_fe import ConfiguracionFE

def check_218():
    session = SessionLocal()
    try:
        config = session.query(ConfiguracionFE).filter_by(empresa_id=218).first()
        if config:
            print("OK: Configuracion encontrada para empresa 218.")
        else:
            print("FAIL: No configuracion para empresa 218.")
    finally:
        session.close()

if __name__ == "__main__":
    check_218()
