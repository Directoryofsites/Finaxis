from app.services.dian_email_service import DianEmailService
import sys

# Credenciales proporcionadas por el usuario
EMAIL = "iglesiaibgv5@gmail.com"
PASS = "dscqziesjsrhoxiy" # Confirmado por imagen

def test_connection():
    service = DianEmailService(
        imap_server="imap.gmail.com",
        email_user=EMAIL,
        email_password=PASS
    )
    
    print(f"--- Intentando conectar a {EMAIL} ---")
    if service.connect():
        print("CONEXION EXITOSA! El servicio pudo loguearse en el servidor IMAP.")
        # ... resta del código sin cambios ...
    else:
        print("[-] FALLO LA CONEXION.")
        print("\nRAZON PROBABLE (GMAIL):")
        print("1. Tienes 2FA activado (Verificacion en dos pasos).")
        print("2. Google bloquea 'aplicaciones menos seguras'.")
        print("\nSOLUCION: Debes crear una 'Contraseña de Aplicación' en:")
        print("https://myaccount.google.com/apppasswords")

if __name__ == "__main__":
    test_connection()
