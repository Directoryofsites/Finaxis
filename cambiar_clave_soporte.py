# C:\ContaPY2\cambiar_clave_soporte.py
import sys
import os

# Añadir el directorio actual al path para que encuentre el módulo 'app'
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.services import usuario as usuario_service

def cambiar_clave():
    email_soporte = "soporte@soporte.com"
    nueva_clave = input(f"Introduce la nueva contraseña para {email_soporte}: ")
    
    if not nueva_clave or len(nueva_clave) < 4:
        print("❌ Error: La contraseña es demasiado corta.")
        return

    db = SessionLocal()
    try:
        usuario = usuario_service.get_user_by_email(db, email_soporte)
        if not usuario:
            print(f"❌ Error: No se encontró el usuario {email_soporte} en la base de datos.")
            return
        
        usuario_service.update_password(db, usuario, nueva_clave)
        print(f"✅ ¡Éxito! La contraseña de {email_soporte} ha sido actualizada correctamente.")
        print("Recuerda que este cambio solo afecta a tu base de datos LOCAL actual.")
        
    except Exception as e:
        print(f"❌ Ocurrió un error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    cambiar_clave()
