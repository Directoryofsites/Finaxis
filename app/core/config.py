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
    # Pydantic leerá automáticamente las variables que acabamos de cargar en el entorno.
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int
    
    # --- AÑADIDO PARA LA IMPRESIÓN SEGURA ---
    # Se define la variable que la aplicación espera encontrar.
    BASE_URL: str


settings = Settings()