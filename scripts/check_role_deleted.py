
import sys
sys.path.append('c:\\ContaPY2')
from app.core.database import SessionLocal
from app.models.permiso import Rol

def check_role_deleted():
    session = SessionLocal()
    try:
        rol_24 = session.query(Rol).filter_by(id=24).first()
        if not rol_24:
            print("CONFIRMADO: El rol ID 24 NO existe.")
        else:
            print("ADVERTENCIA: El rol ID 24 AÚN existe.")
    finally:
        session.close()

if __name__ == "__main__":
    check_role_deleted()
