
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services import usuario as usuario_service
from app.core.hashing import verify_password

def test_login():
    db = SessionLocal()
    try:
        email = "admin@empresa.com"
        password = "admin123"
        
        user = usuario_service.get_user_by_email(db, email=email)
        
        if not user:
            print("FALLO: Usuario no encontrado")
            return

        print(f"Usuario encontrado: {user.email}")
        print(f"Hash en BD: {user.password_hash}")
        
        if verify_password(password, user.password_hash):
            print("EXITO: Contraseña verificada correctamente.")
        else:
            print("FALLO: La contraseña 'admin123' no coincide con el hash.")

    except Exception as e:
        print(f"Error testing login: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_login()
