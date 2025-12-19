import requests
import sys

try:
    url = "http://localhost:8002/api/conciliacion-bancaria/manual-reconciliation/unmatched-movements"
    params = {"bank_account_id": 1}
    
    print("Probando endpoint...")
    response = requests.get(url, params=params, timeout=5)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Endpoint funciona")
        print(f"Bank movements: {len(data.get('bank_movements', []))}")
        print(f"Accounting movements: {len(data.get('accounting_movements', []))}")
    else:
        print(f"❌ Error: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")