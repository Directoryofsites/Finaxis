import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI

async def test_openai():
    # Cargar .env desde la raíz
    root_dir = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(root_dir, ".env"))
    
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"Buscando llave en: {os.path.join(root_dir, '.env')}")
    
    if not api_key or "tu_llave" in api_key:
        print("[ERROR] No se encontro OPENAI_API_KEY o sigue siendo el placeholder.")
        print("Por favor, edita el archivo .env y pon tu llave real.")
        return

    print(f"[OK] Llave encontrada (primeros 5 caracteres): {api_key[:5]}...")
    
    client = AsyncOpenAI(api_key=api_key)
    print("[INFO] Probando conexion con OpenAI (gpt-4o-mini)...")
    
    try:
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Responde 'HOLA' si me escuchas."},
                {"role": "user", "content": "Test"}
            ],
            max_tokens=5
        )
        print(f"[AI] Respuesta de la IA: {completion.choices[0].message.content}")
        print("[SUCCESS] TODO LISTO! La IA funcionara localmente.")
    except Exception as e:
        print(f"[ERROR] Al conectar con OpenAI: {e}")

if __name__ == "__main__":
    asyncio.run(test_openai())
