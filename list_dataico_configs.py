import requests
import json

account_id = "002979c5-7c23-43ab-aa98-3fa7dce6e4d0"
auth_token = "a4afb1e20e856e8fb031b487efbfd239"

headers = {
    "Dataico-Account-Id": account_id,
    "Auth-token": auth_token
}

def list_numberings(module):
    url = f"https://api.dataico.com/direct/dataico_api/v2/numberings/{module}"
    print(f"\n--- Listando {module} ---")
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(json.dumps(data, indent=2))
    except:
        print(response.text)

if __name__ == "__main__":
    list_numberings("invoice")
    list_numberings("support_doc")
