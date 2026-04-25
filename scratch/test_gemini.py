import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv("c:\\ContaPY2\\.env")

# Probar con las llaves que están en el archivo (aunque estén comentadas, las leeremos manualmente)
def test_gemini_key():
    # Intentamos leer la llave manualmente si no está en os.environ
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        # Buscamos en el archivo .env
        with open("c:\\ContaPY2\\.env", "r") as f:
            for line in f:
                if "GEMINI_API_KEY=" in line and not line.strip().startswith("#"):
                     key = line.split("=")[1].strip()
                elif "# GEMINI_API_KEY=" in line:
                     # Intentamos con la comentada para ver si sirve
                     key = line.split("=")[1].strip()
    
    if not key:
        print("No se encontró GEMINI_API_KEY")
        return

    print(f"Probando llave: {key[:10]}...")
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    try:
        response = model.generate_content("Hola, ¿estás activado?")
        print("RESPUESTA:", response.text)
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_gemini_key()
