
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

def test_payload(name, extra_fields):
    payload = {
        "numbering_range_id": 8,
        "reference_code": f"TEST-{name}-001",
        "customer": {
            "identification": "222222222222", "dv": "3", "company": "Consumidor Final", "names": "Consumidor Final",
            "email": "test@test.com", "phone": "3000000", "legal_organization_id": "2", "tribute_id": "21",
            "identification_document_id": "3", "municipality_id": "980"
        },
        "bill_type": "Standard",
        "items": [
            {
                "code_reference": "ITEM-1", "name": "Producto", "quantity": 1, "discount_rate": 0, "price": 10000,
                "tax_rate": "0.00", "unit_measure_id": 70, "standard_code_id": 1, "is_excluded": 0, "tribute_id": 1
            }
        ]
    }
    payload.update(extra_fields)
    print(f"Testing {name}...")
    r = requests.post(validate_url, json=payload, headers=headers)
    print(f"Status: {r.status_code}")
    if r.status_code == 201:
        bill = r.json().get('data', {}).get('bill', {})
        print(f"Recargo en Factus: {bill.get('allowance_charges')}")
    else:
        print(r.text[:200])

# Probar diferentes llaves
test_payload("indicator", {"allowance_charges": [{"id": 1, "indicator": True, "reason": "Cargo", "amount": 2000, "base_amount": 10000}]})
test_payload("is_surcharge", {"allowance_charges": [{"id": 1, "is_surcharge": True, "reason": "Cargo", "amount": 2000, "base_amount": 10000}]})
test_payload("simple_amount", {"allowance_charges": [{"charge_indicator": True, "amount": 2000, "reason": "Cargo"}]})
