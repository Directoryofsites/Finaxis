import os
import sys
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

def resource_path(relative_path):
    """ Obtiene la ruta absoluta al recurso, funciona para desarrollo y para PyInstaller """
    try:
        # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # En modo desarrollo, _MEIPASS no existe
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Usamos nuestra función de confianza para encontrar la ruta correcta del .env
dotenv_path = resource_path('.env')

# Forzamos la carga de las variables desde esa ruta al entorno del sistema.
load_dotenv(dotenv_path=dotenv_path)


class Settings(BaseSettings):
    # --- SEGURIDAD: REVERTIDO A CLAVE DE DESARROLLO (Kiro/Backup) ---
    # Si no existe archivo .env, se usará esta conexión por defecto.
    DATABASE_URL: str = "postgresql://postgres:mysecretpassword@localhost:5432/contapy_db"
    
    # DEBUG: Print loaded URL
    print(f"--- DEBUG CONFIG LOADED: {DATABASE_URL} ---")
    
    SECRET_KEY: str = "secret_key_por_defecto_para_produccion_segura"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # 24 horas para evitar desconexiones
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    
    # --- AÑADIDO PARA LA IMPRESIÓN SEGURA ---
    # Se define la variable que la aplicación espera encontrar.
    BASE_URL: str = "http://localhost:3000"


settings = Settings()