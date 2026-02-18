import sys
import os
sys.path.append(os.getcwd())
from app.core.database import SessionLocal
from app.models.configuracion_fe import ConfiguracionFE
from app.services.providers.factus_provider import FactusProvider
import requests

db = SessionLocal()
config = db.query(ConfiguracionFE).first()
if not config or not config.api_token:
    print("No API Token found")
    sys.exit(1)

import json
provider_config = json.loads(config.api_token)
provider_config["environment"] = "PRUEBAS"

provider = FactusProvider(provider_config)
# Login solo si es necesario, pero aqui forzamos para test
access_token = provider.login()
if not access_token:
    print(f"Login failed")
    sys.exit(1)

url = "https://api-sandbox.factus.com.co/v1/numbering-ranges?filter[id]=&filter[document_type]=&filter[resolution_number]=&filter[is_active]=1"
headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json"
}

response = requests.get(url, headers=headers)
if response.status_code == 200:
    data = response.json()
    print(json.dumps(data, indent=2))
else:
    print(f"Error {response.status_code}: {response.text}")

db.close()
