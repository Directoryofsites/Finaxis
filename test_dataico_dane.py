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

def test_city(city, dept, discount=None):
    payload = {
        "actions": {"send_dian": False, "send_email": False},
        "invoice": {
            "env": "PRUEBAS",
            "dataico_account_id": account_id,
            "invoice_type_code": "FACTURA_VENTA",
            "number": "2135",
            "issue_date": "04/03/2026",
            "payment_means": "CASH",
            "payment_means_type": "DEBITO",
            "payment_date": "04/03/2026",
            "currency_code": "COP",
            "numbering": {"prefix": "FEE", "resolution_number": "18760000001", "flexible": True},
            "customer": {
                "party_type": "PERSONA_NATURAL",
                "party_identification_type": "NIT",
                "party_identification": "12345678",
                "first_name": "Test Name",
                "email": "test@example.com",
                "address": {
                    "address_line": "Calle 1",
                    "city": city,
                    "department": dept,
                    "country": "CO"
                }
            },
            "items": [
                {
                    "sku": "1634",
                    "description": "Arracacha",
                    "price": 1000,
                    "quantity": 1,
                    "taxes": [{"tax_category": "IVA", "tax_rate": 19}]
                }
            ]
        }
    }
    if discount is not None:
        payload["invoice"]["items"][0]["discount_rate"] = discount

    print(f"--- Probando City: {city}, Dept: {dept}, Discount: {discount} ---")
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
    test_city("BOGOTA, D.C.", "BOGOTA")
    test_city("BOGOTA D.C.", "BOGOTA")
    test_city("BOGOTA", "BOGOTA, D.C.")
    test_city("BOGOTA", "BOGOTA D.C.")
    test_city("BOGOTA", "CUNDINAMARCA")
    test_city("BOGOTA D.C.", "CUNDINAMARCA")
    test_city("BOGOTA, D.C.", "CUNDINAMARCA")
    test_city("BOGOTÁ, D.C.", "BOGOTÁ")
    test_city("BOGOTÁ", "BOGOTÁ, D.C.")
    test_city("BOGOTA", "BOGOTA")
