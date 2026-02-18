import sys
import os
import json
import requests
sys.path.append(os.getcwd())
from app.core.database import SessionLocal
from app.models.configuracion_fe import ConfiguracionFE
from app.services.providers.factus_provider import FactusProvider

db = SessionLocal()
config = db.query(ConfiguracionFE).first()
if not config:
    print("No config")
    sys.exit(1)

provider_config = json.loads(config.api_token)
provider_config["environment"] = "PRUEBAS"
provider = FactusProvider(provider_config)
token = provider.login()

url = "https://api-sandbox.factus.com.co/v1/credit-notes/validate" # TRYING SPECIFIC ENDPOINT
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Payload base from previous attempt
payload = {
  "numbering_range_id": 9,
  "reference_code": "NC-TEST-004",
  "observation": "TEST NC STRUCTURE",
  "payment_form": "1",
  "payment_method_code": "10",
  "bill_date": "2026-02-16 00:00:00",
  "date_issue": "2026-02-16 00:00:00",
  "items": [
    {
      "code_reference": "1634",
      "name": "Arracacha",
      "quantity": 1.0,
      "discount_rate": 0.0,
      "price": 11900.0,
      "tax_rate": "19.00",
      "unit_measure_id": 70,
      "standard_code_id": 1,
      "is_excluded": 0,
      "tribute_id": 1,
      "withholding_taxes": []
    }
  ],
  "bill_type": "CreditNote",
  "billing_reference": {
    "number": "6",
    "uuid": "54f478e617c1f3194c45c97a3b3adf40504d0a0e4e04408fdb95c40c464f084718802af13590ffab8ab99db14b427fec",
    "issue_date": "2026-02-16"
  },
  "billing_reference": {
    "number": "6",
    "uuid": "54f478e617c1f3194c45c97a3b3adf40504d0a0e4e04408fdb95c40c464f084718802af13590ffab8ab99db14b427fec",
    "issue_date": "2026-02-16"
  },
  "correction_concept_code": "1", # ROOT LEVEL
  "bill_id": "30682",             # DUMMY BILL ID
  "discrepancy_response": {
    "reference_code": "6",
    "description": "NOTA CREDITO PRUEBA AUTOMATICA"
  },
  "customer": {
    "identification": "41411660",
    "dv": "",
    "company": "Jaime Muñoz",
    "trade_name": "Jaime Muñoz",
    "names": "Jaime Muñoz",
    "address": "cll 44 44-32",
    "email": "hfg9428@gmail.com",
    "phone": "350889977",
    "legal_organization_id": "2",
    "tribute_id": "21",
    "municipality_id": "980",
    "country_code": "CO",
    "identification_document_id": "3"
  }
}

print("Testing with ROOT correction_concept_code and bill_id...")
resp = requests.post(url, headers=headers, json=payload)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text}")

