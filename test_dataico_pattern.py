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

def test_payload(label, city, sku, family_name, first_name):
    payload = {
        "actions": {"send_dian": False, "send_email": False},
        "invoice": {
            "env": "PRUEBAS",
            "dataico_account_id": account_id,
            "invoice_type_code": "FACTURA_VENTA",
            "number": "2136",
            "issue_date": "04/03/2026",
            "payment_means": "CASH",
            "payment_means_type": "DEBITO",
            "payment_date": "04/03/2026",
            "currency_code": "COP",
            "numbering": {"prefix": "FEE", "resolution_number": "18760000001", "flexible": True},
            "customer": {
                "party_type": "PERSONA_NATURAL",
                "party_identification_type": "NIT",
                "party_identification": "121007877",
                "check_digit": "",
                "first_name": first_name,
                "family_name": family_name,
                "company_name": "Alberto Cespedes",
                "email": "hfg9428@gmail.com",
                "phone": "320 5511610",
                "address": {
                    "address_line": "cll 20 50-50",
                    "city": city,
                    "department": "CUNDINAMARCA",
                    "country": "CO"
                }
            },
            "items": [
                {
                    "sku": sku,
                    "description": "Arracacha",
                    "price": 1392.3,
                    "quantity": 51.0,
                    "taxes": [{"tax_category": "IVA", "tax_rate": 19}]
                }
            ]
        }
    }

    print(f"--- Probando: {label} ---")
    response = requests.post(url, headers=headers, json=payload)
    print(response.status_code)
    try:
        data = response.json()
        if "errors" in data:
            print(json.dumps(data, indent=2))
        else:
            print("SUCCESS!")
    except:
        print(response.text)

if __name__ == "__main__":
    test_payload("1. Payload Exacto que fallo", "cll 20 50-50", "", "", "Alberto Cespedes")
    test_payload("2. Sin Familia, SKU corregido, Ciudad corregida", "BOGOTA, D.C.", "1634", "", "Alberto Cespedes")
    test_payload("3. Todo Corregido (Ciudad, SKU y Familia)", "BOGOTA, D.C.", "1634", "Cespedes", "Alberto")
    test_payload("4. Solo corrigiendo Ciudad", "BOGOTA, D.C.", "", "", "Alberto Cespedes")
    test_payload("5. Solo corrigiendo SKU vacio", "cll 20 50-50", "1634", "", "Alberto Cespedes")
