import os
import google.generativeai as genai
from dotenv import load_dotenv
import json

import sys

def test_diagnostics(cmd_key=None):
    print("--- INICIANDO DIAGNÓSTICO DE GEMINI API ---")
    load_dotenv()
    
    api_key = cmd_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] No se encontró GEMINI_API_KEY en el entorno ni en argumentos.")
        return

    print(f"[OK] Probando API Key (termina en ...{api_key[-4:]})")
    genai.configure(api_key=api_key)

    print("\n1. Listando modelos disponibles para esta Key:")
    available_full_names = []
    try:
        models = genai.list_models()
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                available_full_names.append(m.name)
        print(f"   Modelos encontrados ({len(available_full_names)}):")
        for name in sorted(available_full_names):
            print(f"   - {name}")
    except Exception as e:
        print(f"[ERROR] al listar modelos: {e}")
        return

    print("\n2. Probando modelos encontrados:")
    # Probamos los 3 primeros de la lista real para ver si alguno funciona
    for target_name in sorted(available_full_names)[:5]:
        print(f"\n--- Probando: {target_name} ---")
        try:
            model = genai.GenerativeModel(target_name)
            response = model.generate_content("Hola, di 'OK'.")
            print(f"   [OK] EXITO: {response.text.strip()}")
        except Exception as e:
            print(f"   [ERROR] FALLO: {str(e)}")

    print("\n--- FIN DEL DIAGNÓSTICO ---")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_diagnostics(sys.argv[1])
    else:
        test_diagnostics()
