
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

class EncryptionManager:
    _key = None
    _cipher = None

    @classmethod
    def get_cipher(cls):
        if cls._cipher is None:
            key = os.getenv("ENCRYPTION_KEY")
            if not key:
                # Generar una clave temporal si no existe (Advertencia: esto invalida datos previos al reiniciar)
                # En producción, esto DEBE estar en .env
                print("⚠️ WARNING: ENCRYPTION_KEY not found in .env. Generating temporary key.")
                key = Fernet.generate_key().decode()
                # Opcional: Escribirlo en .env automáticamente
            
            cls._key = key
            cls._cipher = Fernet(key.encode())
        return cls._cipher

    @staticmethod
    def encrypt(data: str) -> str:
        if not data:
            return None
        cipher = EncryptionManager.get_cipher()
        return cipher.encrypt(data.encode()).decode()

    @staticmethod
    def decrypt(token: str) -> str:
        if not token:
            return None
        try:
            cipher = EncryptionManager.get_cipher()
            return cipher.decrypt(token.encode()).decode()
        except Exception as e:
            print(f"❌ Decryption failed: {e}")
            return None

    @staticmethod
    def generate_new_key():
        return Fernet.generate_key().decode()
