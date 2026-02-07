import sys
import os
import json
import requests

sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.configuracion_fe import ConfiguracionFE

def query_ranges():
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
        
        resp = requests.post(auth_url, data=payload)
        token = resp.json()['access_token']
        
        # Query Ranges
        query_url = "https://api-sandbox.factus.com.co/v1/numbering-ranges"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        resp = requests.get(query_url, headers=headers)
        data = resp.json().get('data', {}).get('items', [])
        print(f"Rangos encontrados: {len(data)}")
        for item in data:
            print(f"ID: {item.get('id')} | Name: {item.get('document_type')} {item.get('prefix')} | From: {item.get('from')} To: {item.get('to')} | Current: {item.get('current')}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    query_ranges()
