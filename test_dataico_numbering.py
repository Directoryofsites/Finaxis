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

def test_numbering(prefix, resolution=None):
    print(f"\n--- Probando con Prefijo: {prefix}, Res: {resolution} ---")
    payload = {
        "actions": {"send_dian": False, "send_email": False},
        "invoice": {
            "env": "PRUEBAS",
            "dataico_account_id": account_id,
            "invoice_type_code": "FACTURA_VENTA",
            "number": "99999",
            "issue_date": "04/03/2026",
            "numbering": {
                "prefix": prefix,
                "flexible": True
            },
            "customer": {"company_id": "123456789", "company_name": "Test"},
            "items": [{"sku": "1", "description": "Test", "price": 1000, "quantity": 1}]
        }
    }
    if resolution:
        payload["invoice"]["numbering"]["resolution_number"] = resolution

    response = requests.post(url, headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")

if __name__ == "__main__":
    # Prueba 1: Solo prefijo
    test_numbering("SETP")
    # Prueba 2: Prefijo SETT (comun en Dataico pruebas)
    test_numbering("SETT")
