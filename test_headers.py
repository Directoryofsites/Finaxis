import subprocess
import json

account_id = "002979c5-7c23-43ab-aa98-3fa7dce6e4d0"
auth_token = "a4afb1e20e856e8fb031b487efbfd239"
url = "https://api.dataico.com/direct/dataico_api/v2/invoices"

def test_curl(header_name, token_name):
    print(f"\n--- Probando con {header_name} y {token_name} ---")
    cmd = [
        "curl", "-v", "-X", "GET", url,
        "-H", f"Content-Type: application/json",
        "-H", f"{header_name}: {account_id}",
        "-H", f"{token_name}: {auth_token}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Status: {result.stdout[:200]}")
    if "dataico account id" in result.stdout.lower():
        print("RESULTADO: RECHAZADO (ID Inválido)")
    elif "no se encuentra documento" in result.stdout.lower() or "401" in result.stdout:
         print("RESULTADO: PARECE QUE LAS CABECERAS SON RECONOCIDAS (404 o 401)")
    else:
         print(f"Respuesta cruda: {result.stdout}")

if __name__ == "__main__":
    # Variaciones de cabeceras
    test_curl("Dataico_account_id", "Auth-token")
    test_curl("dataico_account_id", "auth-token")
    test_curl("Dataico-Account-Id", "Auth-Token")
