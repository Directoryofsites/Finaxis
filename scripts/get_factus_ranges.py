
import sys
import os
import requests
import json

sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.configuracion_fe import ConfiguracionFE
from app.models.empresa import Empresa
from app.services.providers.factus_provider import FactusProvider

def check_ranges():
    db = SessionLocal()
    try:
        empresa = db.query(Empresa).filter(Empresa.razon_social == "Verduras la 21").first()
        if not empresa:
            empresa = db.query(Empresa).get(134)
            
        config = db.query(ConfiguracionFE).filter_by(empresa_id=empresa.id).first()
        
        if not config.api_token:
            print("No api_token found")
            return

        creds = json.loads(config.api_token)
        
        provider_config = {
            "environment": config.ambiente,
            "client_id": creds.get("client_id"),
            "client_secret": creds.get("client_secret"),
            "username": creds.get("username"),
            "password": creds.get("password")
        }
        
        provider = FactusProvider(provider_config)
        token = provider.login()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        url = f"{provider.base_url}/v1/numbering-ranges"
        print(f"Fetching ranges from: {url}")
        
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json().get('data', [])
            print(f"Raw Data: {data}")
            print(f"Found {len(data)} ranges:")
            for item in data:
                print(f" - Item: {item}")
        else:
            print(f"Error {resp.status_code}: {resp.text}")

    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_ranges()
