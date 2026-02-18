import sys
import os
import json
import requests

sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.configuracion_fe import ConfiguracionFE

def brute_force_ranges():
    session = SessionLocal()
    try:
        empresa_id = 134 # Verduras la 21
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
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

        print("Searching ranges 1 to 200...")
        found = []
        for rid in range(1, 201):
            query_url = f"https://api-sandbox.factus.com.co/v1/numbering-ranges/{rid}"
            resp = requests.get(query_url, headers=headers)
            if resp.status_code == 200:
                data = resp.json().get('data', {})
                if data:
                    prefix = data.get('prefix')
                    expired = data.get('is_expired')
                    end = data.get('end_date')
                    doc = data.get('document')
                    print(f"ID: {rid} | Prefix: {prefix} | Doc: {doc} | Expired: {expired} | End: {end}")
                    found.append(rid)
        
        if not found:
            print("No individual ranges found by ID.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    brute_force_ranges()
