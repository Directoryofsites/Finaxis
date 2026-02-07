import sys
import os
import json
import requests

sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.configuracion_fe import ConfiguracionFE

def find_range_id():
    session = SessionLocal()
    try:
        empresa_id = 218
        config = session.query(ConfiguracionFE).filter_by(empresa_id=empresa_id).first()
        if not config or not config.api_token:
            print("No hay configuración o token")
            return
            
        creds = json.loads(config.api_token)
        
        # Login
        auth_url = "https://api-sandbox.factus.com.co/oauth/token"
        payload = {
            "grant_type": "password",
            "client_id": creds.get("client_id"),
            "client_secret": creds.get("client_secret"),
            "username": creds.get("username"),
            "password": creds.get("password")
        }
        
        print("Logging in...")
        resp = requests.post(auth_url, data=payload)
        token = resp.json().get('access_token')
        if not token:
            print(f"Error login: {resp.text}")
            return
        
        print(f"Searching ranges for Token: {token[:10]}...")
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

        # Intentar consultar la lista completa primero sin ID específico pero con paginación
        query_url = "https://api-sandbox.factus.com.co/v1/numbering-ranges"
        resp = requests.get(query_url, headers=headers)
        if resp.status_code == 200:
            data_items = resp.json().get('data', {}).get('items', [])
            print(f"LISTA COMPLETA - Rangos encontrados: {len(data_items)}")
            for item in data_items:
                print(f"ID: {item.get('id')} | Prefix: {item.get('prefix')} | Current: {item.get('current')}")

        # Probar IDs individuales si la lista falló
        print("\nProbando IDs individuales del 1 al 20...")
        for rid in range(1, 21):
            query_url = f"https://api-sandbox.factus.com.co/v1/numbering-ranges?id={rid}"
            resp = requests.get(query_url, headers=headers)
            if resp.status_code == 200:
                data_items = resp.json().get('data', {}).get('items', [])
                for item in data_items:
                    if item.get('prefix') == 'SETP':
                        print(f"¡ID {rid} es para SETP! | Prefix: {item.get('prefix')} | Current: {item.get('current')}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    find_range_id()
