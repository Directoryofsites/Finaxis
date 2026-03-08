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

def test_name(label, inv_num, p_type, f_name, l_name, c_name):
    payload = {
        "actions": {"send_dian": False, "send_email": False},
        "invoice": {
            "env": "PRUEBAS",
            "dataico_account_id": account_id,
            "invoice_type_code": "FACTURA_VENTA",
            "number": inv_num,
            "issue_date": "04/03/2026",
            "payment_means": "CASH",
            "payment_means_type": "DEBITO",
            "payment_date": "04/03/2026",
            "currency_code": "COP",
            "numbering": {"prefix": "FEE", "resolution_number": "18760000001", "flexible": True},
            "customer": {
                "party_type": p_type,
                "party_identification_type": "NIT",
                "party_identification": "121007877",
                "check_digit": "",
                "first_name": f_name,
                "family_name": l_name,
                "company_name": c_name,
                "email": "hfg9428@gmail.com",
                "address": {
                    "address_line": "cll 20 50-50",
                    "city": "BOGOTA, D.C.",
                    "department": "BOGOTA",
                    "country": "CO"
                }
            },
            "items": [
                {
                    "sku": "000",
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
    test_name("1. Natural sin apellido", "3001", "PERSONA_NATURAL", "Alberto Cespedes", "", "Alberto Cespedes")
    test_name("2. Natural con apellido", "3002", "PERSONA_NATURAL", "Alberto", "Cespedes", "Alberto Cespedes")
    test_name("3. Juridico sin nombres", "3003", "PERSONA_JURIDICA", "", "", "Alberto Cespedes")
    test_name("4. Natural mandando guion de apellido", "3004", "PERSONA_NATURAL", "Alberto Cespedes", "-", "Alberto Cespedes")
