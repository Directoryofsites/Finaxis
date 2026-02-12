import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("FATAL: GEMINI_API_KEY no encontrada en .env")
    exit(1)

genai.configure(api_key=api_key)

print(f"Consultando modelos disponibles para la Key: {api_key[:5]}...")

try:
    models = genai.list_models()
    print("\n--- MODELOS DISPONIBLES ---")
    found_any = False
    for m in models:
        # Filtrar solo modelos que generan contenido (no embedding)
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name} (Versión: {m.version}) -> {m.display_name}")
            found_any = True
    
    if not found_any:
        print("No se encontraron modelos con capability 'generateContent'.")

except Exception as e:
    print(f"\nERROR AL LISTAR MODELOS: {e}")
