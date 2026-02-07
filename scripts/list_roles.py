
import sys
sys.path.append('c:\\ContaPY2')
from app.core.database import SessionLocal
from app.models.permiso import Rol
from app.models.usuario import usuario_roles  # Tabla intermedia
from sqlalchemy import func

def list_roles():
    session = SessionLocal()
    try:
        roles = session.query(Rol).all()
        print(f"{'ID':<5} | {'Nombre':<20} | {'Usuarios Asignados'}")
        print("-" * 50)
        
        for rol in roles:
            # Contar usuarios
            count = session.query(usuario_roles).filter_by(rol_id=rol.id).count()
            print(f"{rol.id:<5} | {rol.nombre:<20} | {count}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    list_roles()
