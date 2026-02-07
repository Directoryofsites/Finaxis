import sys
import os
import json
import requests

sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.configuracion_fe import ConfiguracionFE

def query_factus():
    session = SessionLocal()
    try:
        empresa_id = 218
        numero = 990021823
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
        
        # Query Bills sin filtros para ver todo lo de esta cuenta
        query_url = "https://api-sandbox.factus.com.co/v1/bills"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        resp = requests.get(query_url, headers=headers)
        data = resp.json().get('data', {}).get('items', [])
        print(f"Facturas encontradas: {len(data)}")
        for i, item in enumerate(data[:10]):
            print(f"[{i}] ID: {item.get('id')} | No: {item.get('number')} | Status: {item.get('status')} | DIAN: {item.get('dian_status')}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    query_factus()
