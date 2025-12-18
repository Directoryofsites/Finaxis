
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services import usuario as usuario_service
from app.models.usuario import Usuario

def reset_password():
    db = SessionLocal()
    try:
        email = "admin@empresa.com"
        new_password = "admin123"
        
        user = usuario_service.get_user_by_email(db, email)
        if user:
            print(f"Usuario encontrado: {user.email}")
            # Hashear y actualizar
            hashed_password = usuario_service.get_password_hash(new_password)
            user.password_hash = hashed_password
            db.commit()
            print(f"--> CONTRASEÑA RESTABLECIDA EXITOSAMENTE A: {new_password}")
        else:
            print("ERROR: Usuario admin@empresa.com no encontrado.")
    except Exception as e:
        print(f"Error resetting password: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_password()
