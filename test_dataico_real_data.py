import requests
import json

account_id = "002979c5-7c23-43ab-aa98-3fa7dce6e4d0"
auth_token = "a4afb1e20e856e8fb031b487efbfd239"
url = "https://api.dataico.com/direct/dataico_api/v2/invoices"

headers = {
    "Content-Type": "application/json",
    "Dataico-Account-Id": account_id,
    "Auth-token": auth_token
}

def test_working_numbering():
    print(f"\n--- Probando con Prefijo: FEE, Res: 18760000001 ---")
    payload = {
        "actions": {"send_dian": False, "send_email": False},
        "invoice": {
            "env": "PRUEBAS",
            "dataico_account_id": account_id,
            "invoice_type_code": "FACTURA_VENTA",
            "number": "2000", # FEE empieza en 1, usemos uno alto para evitar conflictos
            "issue_date": "04/03/2026",
            "numbering": {
                "prefix": "FEE",
                "resolution_number": "18760000001",
                "flexible": True
            },
            "customer": {
                "party_type": "PERSON",
                "party_identification_type": "NIT",
                "company_id": "12345678",
                "first_name": "Test",
                "email": "test@example.com",
                "address": {"address_line": "Calle 1", "city": "BOGOTA", "department": "11", "country": "CO"}
            },
            "items": [{"sku": "1", "description": "Test", "price": 1000, "quantity": 1}]
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")

if __name__ == "__main__":
    test_working_numbering()
