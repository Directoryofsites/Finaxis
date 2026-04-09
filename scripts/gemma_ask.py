import requests
import argparse
import sys
import os
import json
from datetime import datetime

# Configuración
API_URL = "http://127.0.0.1:1234/v1/chat/completions"
MODELS_URL = "http://127.0.0.1:1234/v1/models"

def get_active_model():
    """Detecta automáticamente qué modelo hay cargado en LM Studio"""
    try:
        response = requests.get(MODELS_URL, timeout=5)
        response.raise_for_status()
        models = response.json().get("data", [])
        if models:
            return models[0]["id"]
    except:
        pass
    return "google/gemma-3-4b" # Backup por defecto

DEFAULT_MODEL = get_active_model()

# Rutas absolutas para que funcione desde cualquier carpeta
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) # c:\ContaPY2\scripts
BASE_DIR = os.path.dirname(SCRIPT_DIR) # c:\ContaPY2
LOG_DIR = os.path.join(BASE_DIR, "logs", "gemma")
LOG_FILE = os.path.join(LOG_DIR, "history.jsonl")

def log_interaction(prompt, response, file_used=None):
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "file_context": file_used,
        "prompt": prompt,
        "response": response
    }
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def read_docx(file_path):
    """Extrae texto de un archivo Word (.docx)"""
    try:
        import docx
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        return f"Error al leer Word: {str(e)}"

def read_pdf(file_path):
    """Extrae texto de un archivo PDF"""
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error al leer PDF: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description="Consulta a Gemma con contexto local")
    parser.add_argument("prompt", help="La pregunta para el modelo")
    parser.add_argument("--file", help="Ruta de un archivo local para incluir como contexto")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Nombre del modelo a usar")
    args = parser.parse_args()

    file_content = ""
    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: El archivo {args.file} no existe.")
            return

        ext = os.path.splitext(args.file)[1].lower()
        print(f"Leyendo archivo ({ext})...")

        try:
            if ext == ".docx":
                file_content = read_docx(args.file)
            elif ext == ".pdf":
                file_content = read_pdf(args.file)
            else:
                # Intento de lectura de texto plano (UTF-8)
                with open(args.file, "r", encoding="utf-8") as f:
                    file_content = f.read()
        except Exception as e:
            print(f"Error al leer el archivo: {str(e)}")
            return

    # Construir el mensaje con el contexto
    full_prompt = args.prompt
    if file_content:
        full_prompt = f"Contexto del archivo '{args.file}':\n\n{file_content}\n\n--- PREGUNTA DEL USUARIO ---\n{args.prompt}"

    print(f"Consultando a {args.model}... (esto puede tardar un momento)")
    
    try:
        response = requests.post(
            API_URL,
            json={
                "model": args.model,
                "messages": [
                    {"role": "system", "content": "Eres una consultora experta. Analiza el contexto proporcionado y responde de forma técnica y útil."},
                    {"role": "user", "content": full_prompt}
                ]
            },
            timeout=600
        )
        response.raise_for_status()
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        print("\n--- RESPUESTA DE GEMMA ---")
        print(content)
        
        log_interaction(args.prompt, content, args.file)
        
    except requests.exceptions.RequestException as e:
        print(f"Error de la API: {str(e)}")
    except Exception as e:
        print(f"Error inesperado: {str(e)}")

if __name__ == "__main__":
    main()
