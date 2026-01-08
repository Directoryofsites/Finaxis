import sys
import os
sys.path.append("c:/ContaPY2")
from app.core.database import SessionLocal
from app.models import usuario as models_usuario, empresa as models_empresa

def check_users():
    db = SessionLocal()
    try:
        users = db.query(models_usuario.Usuario).all()
        print(f"Total Usuarios encontrados: {len(users)}")
        print("-" * 60)
        print(f"{'Email':<30} | {'Rol':<15} | {'Empresa ID':<10} | {'Nombre Empresa'}")
        print("-" * 60)
        
        for u in users:
            rol_nombre = u.roles[0].nombre if u.roles else "SIN ROL"
            emp_nombre = u.empresa.razon_social if u.empresa else "---"
            print(f"{u.email:<30} | {rol_nombre:<15} | {str(u.empresa_id):<10} | {emp_nombre}")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_users()
