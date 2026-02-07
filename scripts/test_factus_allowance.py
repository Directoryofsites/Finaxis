
import requests
import json
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:mysecretpassword@localhost:5432/contapy_db"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    config = conn.execute(text("SELECT api_token FROM configuracion_fe WHERE api_token IS NOT NULL LIMIT 1")).fetchone()
    if not config: exit(1)
    creds = json.loads(config[0])

auth_url = "https://api-sandbox.factus.com.co/oauth/token"
login_payload = {
    "grant_type": "password",
    "client_id": creds.get("client_id"),
    "client_secret": creds.get("client_secret"),
    "username": creds.get("username"),
    "password": creds.get("password")
}
resp = requests.post(auth_url, data=login_payload)
token = resp.json().get('access_token')

validate_url = "https://api-sandbox.factus.com.co/v1/bills/validate"
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Prueba 1: Enviar precio EXCLUYENDO IVA (10.000) y ver si Factus le suma el 19%
payload_exclusive = {
    "numbering_range_id": 8,
    "reference_code": "TEST-EXCL-001",
    "customer": {
        "identification": "222222222222", "dv": "3", "company": "Consumidor Final", "names": "Consumidor Final",
        "email": "test@test.com", "phone": "3000000", "legal_organization_id": "2", "tribute_id": "21",
        "identification_document_id": "3", "municipality_id": "980"
    },
    "bill_type": "Standard",
    "items": [
        {
            "code_reference": "ITEM-X",
            "name": "Producto Exclusivo",
            "quantity": 1,
            "discount_rate": 0,
            "price": 10000, # Sin IVA
            "tax_rate": "19.00",
            "unit_measure_id": 70,
            "standard_code_id": 1,
            "is_excluded": 0,
            "tribute_id": 1
        }
    ]
}

print("Testing with EXCLUSIVE price...")
resp_test = requests.post(validate_url, json=payload_exclusive, headers=headers)
print(f"Status: {resp_test.status_code}")
data = resp_test.json()
if "data" in data and "bill" in data["data"]:
    bill = data["data"]["bill"]
    print(f"Total Factus: {bill['total']}")
    print(f"IVA Factus: {bill['tax_amount']}")
    print(f"Price in Response: {bill['items'][0]['price']}")
else:
    print(json.dumps(data, indent=2))
