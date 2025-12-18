
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.usuario import Usuario

def inspect_user():
    db = SessionLocal()
    try:
        email = "admin@empresa.com"
        user = db.query(Usuario).filter(Usuario.email == email).first()
        if user:
            print(f"ID: {user.id}")
            print(f"Email: {user.email}")
            print(f"Nombre: {user.nombre_completo}")
            print(f"Activo: {user.is_active}")
            print(f"Empresa ID: {user.empresa_id}")
            print(f"Hashed Password: {user.hashed_password}")
        else:
            print("Usuario no encontrado.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_user()
