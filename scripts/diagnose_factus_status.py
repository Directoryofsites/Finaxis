import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# Configuración
CLIENT_ID = os.getenv("FACTUS_CLIENT_ID")
CLIENT_SECRET = os.getenv("FACTUS_CLIENT_SECRET")
USERNAME = os.getenv("FACTUS_EMAIL")
PASSWORD = os.getenv("FACTUS_PASSWORD")
ENV = os.getenv("FACTUS_ENV", "PRUEBAS")

BASE_URL = "https://api-sandbox.factus.com.co"
if ENV == "PRODUCCION":
    BASE_URL = "https://api.factus.com.co"

print(f"--- DIAGNOSTICO FACTUS ({ENV}) ---")
print(f"URL: {BASE_URL}")
print(f"Usuario: {USERNAME}")

def get_token():
    url = f"{BASE_URL}/oauth/token"
    payload = {
        "grant_type": "password",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "username": USERNAME,
        "password": PASSWORD
    }
    try:
        resp = requests.post(url, data=payload)
        resp.raise_for_status()
        return resp.json()['access_token']
    except Exception as e:
        print(f"❌ Error obteniendo token: {e}")
        if 'resp' in locals():
            print(resp.text)
        return None

token = get_token()

if token:
    print("✅ Token obtenido exitosamente.")
    
    # Consultar últimas facturas
    url_bills = f"{BASE_URL}/v1/bills?page=1"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    try:
        print("\n--- CONSULTANDO ÚLTIMAS FACTURAS ---")
        resp = requests.get(url_bills, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            bills = data.get('data', {}).get('bills', [])
            if not bills:
                bills = data.get('data', {}).get('data', []) # A veces cambia la estructura
            
            print(f"Encontradas {len(bills)} facturas recientes.")
            for bill in bills[:5]:
                print(f"📄 [{bill.get('number')}] Estado: {bill.get('status')} | DIAN: {bill.get('dian_status')}")
                # Si hay error message
                if bill.get('api_client_name'):
                     print(f"   Cliente: {bill.get('api_client_name')}")
        else:
            print(f"❌ Error consultando facturas: {resp.status_code}")
            print(resp.text)
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

else:
    print("❌ No se pudo autenticar. Verifique credenciales en .env")
