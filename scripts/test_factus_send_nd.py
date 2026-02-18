
import requests
import json
import sys
import os

sys.path.append('c:\\ContaPY2')
from app.core.database import SessionLocal
from app.models.configuracion_fe import ConfiguracionFE

def test_send_nd():
    session = SessionLocal()
    try:
        empresa_id = 134
        config = session.query(ConfiguracionFE).filter_by(empresa_id=empresa_id).first()
        if not config or not config.api_token:
            print("No token")
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
        
        # Payload
        url = "https://api-sandbox.factus.com.co/v1/bills/validate"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Minimal data - using ID 149 (Nota Ajuste Documento Soporte)
        data = {
          "numbering_range_id": 149,
          "reference_code": "ND-TEST-005",
          "observation": "Test ND",
          "payment_form": "1",
          "payment_method_code": "10",
          "bill_date": "2026-02-18", # Adjust date if needed
          "date_issue": "2026-02-18",
          "items": [
            {
              "code_reference": "TEST-ITEM",
              "name": "Test Item",
              "quantity": 1,
              "discount_rate": 0,
              "price": 1000,
              "tax_rate": "19.00",
              "unit_measure_id": 70,
              "standard_code_id": 1,
              "is_excluded": 0,
              "tribute_id": 1,
              "withholding_taxes": []
            }
          ],
          "bill_type": "DebitNote",
          # Need a valid billing reference from a previous invoice
          # Since I don't have one handy, I'll use dummy data but this might fail validation too.
          # Ideally should be a real invoice.
          "billing_reference": {
            "number": "98", # From user logs
            "uuid": "a2f12316e1f86e263218322c3c6619c0aaafff2bc0c5242ad1eafc8f5e227c71e0094c96776dfe2b6405b924d00b6973",
            "issue_date": "2026-02-18" 
          },
          "bill_id": "30731", # Should be parent bill ID? Or Factus ID?
           "discrepancy_response": {
            "reference_code": "98",
            "correction_concept_id": "1",
            "description": "Test ND"
          },
          "correction_concept_code": "1",
          "customer": {
            "identification": "121007877",
            "dv": "",
            "company": "Alberto Cespedes",
            "trade_name": "Alberto Cespedes",
            "names": "Alberto Cespedes",
            "address": "cll 20 50-50",
            "email": "hfg9428@gmail.com",
            "phone": "320 5511610",
            "legal_organization_id": "2",
            "tribute_id": "21",
            "municipality_id": "980", 
            "identification_document_id": "3"
          }
        }
        
        print("Sending Payload...")
        resp = requests.post(url, headers=headers, json=data)
        print(f"Status: {resp.status_code}")
        print(resp.text)
        
    except Exception as e:
        print(e)
    finally:
        session.close()

if __name__ == "__main__":
    test_send_nd()
