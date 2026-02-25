import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "")

async def test_whatsapp_connection():
    print(f"--- DIAGNÓSTICO WHATSAPP ---")
    print(f"Phone ID: {WHATSAPP_PHONE_ID}")
    print(f"Token (primeros 10): {WHATSAPP_TOKEN[:10]}...")
    
    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": "573234259925", # Número de prueba detectado en BD
        "type": "text",
        "text": {"body": "Test de diagnóstico Finaxis"}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_whatsapp_connection())
