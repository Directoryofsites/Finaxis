
import requests
import json
import sys

# DATAYCO SANDBOX / PRODUCTION URLs
# Necesitamos confirmar si existe URL específica para pruebas o si es la misma con un flag.
# Según doc, suele ser https://api.dataico.com/dataico_api/v2 con un token de pruebas.

BASE_URL = "https://api.dataico.com/dataico_api/v2"

def test_connection(account_id, auth_token):
    print(f"Probando conexión a Datayco API...")
    print(f"URL: {BASE_URL}")
    print(f"Account ID: {account_id}")
    
    headers = {
        "Auth-token": auth_token,
        "Dataico-account-id": account_id, # Verificar si el header es así o Dataico_account_id
        "Content-Type": "application/json"
    }
    
    # Endpoint de prueba: Consultar numeraciones o estado general
    # Endpoint: /biller_numberings
    try:
        url = f"{BASE_URL}/biller_numberings" 
        resp = requests.get(url, headers=headers)
        
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {resp.text}")
        
        if resp.status_code == 200:
            print("✅ Conexión Exitosa!")
            return True
        else:
            print("❌ Falló la conexión.")
            return False
            
    except Exception as e:
        print(f"❌ Error de excepción: {str(e)}")
        return False

if __name__ == "__main__":
    print("--- TEST DE CONEXIÓN DATAYCO ---")
    account_id = input("Ingrese Dataico Account ID: ").strip()
    auth_token = input("Ingrese Auth Token: ").strip()
    
    if account_id and auth_token:
        test_connection(account_id, auth_token)
    else:
        print("Credenciales vacías.")
