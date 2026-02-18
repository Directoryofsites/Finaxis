
import sys
import os
import requests
import json

sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.configuracion_fe import ConfiguracionFE
from app.models.empresa import Empresa

def probe_endpoints():
    db = SessionLocal()
    try:
        empresa = db.query(Empresa).filter(Empresa.razon_social == "Verduras la 21").first()
        if not empresa:
            empresa = db.query(Empresa).get(134)
            
        config = db.query(ConfiguracionFE).filter_by(empresa_id=empresa.id).first()
        creds = json.loads(config.api_token)
        
        # Quick Login
        login_url = "https://api-sandbox.factus.com.co/oauth/token"
        payload = {
            "grant_type": "password",
            "client_id": creds.get("client_id"),
            "client_secret": creds.get("client_secret"),
            "username": creds.get("username"),
            "password": creds.get("password")
        }
        resp = requests.post(login_url, data=payload)
        token = resp.json()['access_token']
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        base_url = "https://api-sandbox.factus.com.co"
        
        endpoints = [
            ("/v1/debitnotes/validate", "POST"),
            ("/v1/debitnotes", "POST"),
            ("/v1/debit-notes", "POST"), # Retry
        ]
        
        # Test bills/validate with DebitNote type but Invoice Range (8)
        print("Testing v1/bills/validate with DebitNote type + Range 8...")
        dn_payload = {
            "bill_type": "DebitNote",
            "numbering_range_id": 8, # Invoice Range
            "reference_code": "TEST-ND",
            "observation": "Test",
            "payment_form": "1",
            "payment_method_code": "10",
            "bill_date": "2026-02-16 00:00:00",
            "date_issue": "2026-02-16 00:00:00",
             "customer": {
                "identification": "41411660",
                "dv": "",
                "company": "Jaime Mu\u00f1oz",
                "trade_name": "Jaime Mu\u00f1oz",
                "names": "Jaime Mu\u00f1oz",
                "address": "cll 44 44-32",
                "email": "hfg9428@gmail.com",
                "phone": "350889977",
                "legal_organization_id": "2",
                "tribute_id": "21",
                "municipality_id": "980",
                "country_code": "CO",
                "identification_document_id": "3"
            },
            "items": [
                 {
                  "code_reference": "1634",
                  "name": "Arracacha",
                  "quantity": 1.0,
                  "discount_rate": 0.0,
                  "price": 5950.0,
                  "tax_rate": "19.00",
                  "unit_measure_id": 70,
                  "standard_code_id": 1,
                  "is_excluded": 0,
                  "tribute_id": 1,
                  "withholding_taxes": []
                }
            ],
             "billing_reference": {
                "number": "15",
                "uuid": "dummy",
                "issue_date": "2026-02-16"
            },
           "correction_concept_code": "1",
           "discrepancy_response": {
                "reference_code": "15",
                "description": "NOTA DEBITO PRUEBA AUTOMATICA"
            }
        }
        
        try:
             r = requests.post(base_url + "/v1/bills/validate", headers=headers, json=dn_payload)
             print(f"Status: {r.status_code}")
             print(f"Response: {r.text[:500]}")
        except Exception as e:
             print(f"Error: {e}")
        dummy_payload = { "test": "payload" }
        
        endpoints = [
            "/v1/bills/validate",
            "/v1/credit-notes/validate",
            "/v1/debit-notes/validate",
            "/v1/debit-note/validate",
            "/v1/debit-notes",
            "/v1/debit-note",
            "/v1/notes/validate",
            "/v1/notes",
            "/v1/nd/validate",
            "/v1/nds/validate"
        ]
        
        for ep in endpoints:
            url = f"{base_url}{ep}"
            print(f"Probing: {url}")
            try:
                # We use a minimal payload to just see if the route exists (expecting 422 or 401, not 404)
                resp = requests.post(url, headers=headers, json={})
                print(f"   -> Status: {resp.status_code}")
                if resp.status_code != 404:
                    print(f"   -> FOUND! (Method Allowed/Validation Error)")
                    if 'Allow' in resp.headers:
                         print(f"   -> Allow: {resp.headers['Allow']}")
            except Exception as e:
                print(f"   -> Error: {e}")

    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    probe_endpoints()
