import requests
import json

account_id = "002979c5-7c23-43ab-aa98-3fa7dce6e4d0"
auth_token = "a4afb1e20e856e8fb031b487efbfd239"
url = "https://api.dataico.com/direct/dataico_api/v2/invoices"

headers = {
    "Content-Type": "application/json",
    "Dataico_account_id": account_id,
    "Auth-token": auth_token
}

payload = {
    "actions": {"send_dian": False},
    "invoice": {
        "dataico_account_id": account_id,
        "number": 999999, # Un numero de prueba
        "issue_date": "2026-03-03 12:00:00",
        "customer": {
            "company_id": "123456789",
            "company_name": "Test Customer"
        },
        "items": [
            {"description": "Test Item", "price": 1000, "quantity": 1}
        ]
    }
}

def test_post():
    print("Enviando POST con ID dentro de invoice...")
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")

if __name__ == "__main__":
    test_post()
