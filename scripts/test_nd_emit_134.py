
import sys
import os
import requests
import json
import datetime
sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.configuracion_fe import ConfiguracionFE

def test_nd_emission():
    session = SessionLocal()
    try:
        empresa_id = 134
        config = session.query(ConfiguracionFE).filter_by(empresa_id=empresa_id).first()
        
        if not config:
            print("No config found for company 134")
            return

        print(f"Using Config: ND Range {config.nd_rango_id}, Environment {config.ambiente}")
        
        # 1. Login to Factus
        auth_url = "https://api-sandbox.factus.com.co/oauth/token"
        
        try:
            creds = json.loads(config.api_token)
        except Exception as e:
            print(f"Invalid JSON in api_token: {e}")
            return
            
        payload = {
            "grant_type": "password",
            "client_id": creds.get('client_id'),
            "client_secret": creds.get('client_secret'),
            "username": creds.get('username'), # Key is username
            "password": creds.get('password')
        }
        
        print("Authenticating...")
        token_resp = requests.post(auth_url, data=payload)
        
        if token_resp.status_code != 200:
            print(f"Login failed: {token_resp.text}")
            return
            
        token = token_resp.json()['access_token']
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # 2. Construct Payload
        # Dummy ND payload for range 10
        range_id = config.nd_rango_id
        if not range_id:
             print("Range ID is null in DB, using 10 fallback")
             range_id = 10
             
        
        # Unique reference
        ref_code = f"NC-TEST-VERIFY-{datetime.datetime.now().strftime('%H%M%S')}"
        
        # TEST CROSS-CHECK: Range 9 (NC) with DebitNote type
        range_id = 9

        nd_payload = {
            "numbering_range_id": range_id, 
            "bill_type": "DebitNote",
            "reference_code": ref_code,
            "observation": "Prueba ND",
            "payment_form": "1",
            "payment_method_code": "10",
            "billing_reference": {
                "number": "SETP-990000001",
                "uuid": "cufe-dummy-1234567890",
                "issue_date": datetime.date.today().strftime("%Y-%m-%d")
            },
            "correction_concept_code": "3",
            "discrepancy_response": {
                "reference_code": "SETP-990000001",
                "correction_concept_id": "3",
                "description": "Cambio del valor"
            },
            "customer": {
                "identification": "222222222222",
                "dv": "2",
                "company": "Adquirente Prueba",
                "trade_name": "Adquirente Prueba",
                "names": "Adquirente Prueba",
                "address": "Calle 123",
                "email": "test@test.com",
                "phone": "3003003000",
                "legal_organization_id": "2",
                "tribute_id": "21",
                "identification_document_id": "3",
                "municipality_id": "1", 
                "is_vat_responsible": 0
            },
            "items": [
                {
                    "code_reference": "ITEM-001",
                    "name": "Item Prueba",
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
            "billing_period": {
                 "start_date": datetime.date.today().isoformat(),
                 "start_time": "00:00:00",
                 "end_date": datetime.date.today().isoformat(),
                 "end_time": "23:59:59"
            }
        }
        
        print(f"Sending Payload to Factus with Range {range_id}...")
        # Endpoint for Debit Note validation is same as Credit Note
        url = "https://api-sandbox.factus.com.co/v1/credit-notes/validate"
        
        resp = requests.post(url, json=nd_payload, headers=headers)
        
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {resp.text}")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    test_nd_emission()
