import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv("c:\\ContaPY2\\.env")

def list_available_models():
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        print("No se encontró GEMINI_API_KEY")
        return

    print(f"Probando llave: {key[:10]}...")
    genai.configure(api_key=key)
    
    print("--- Modelos Disponibles ---")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"ID: {m.name} | Display: {m.display_name}")
    except Exception as e:
        print(f"ERROR listando modelos: {e}")

if __name__ == "__main__":
    list_available_models()
