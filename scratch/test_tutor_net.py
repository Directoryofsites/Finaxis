import requests

url = "http://localhost:8002/api/ai/tutor-debug"
payload = {"query": "hola", "history": []}
try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"STATUS: {response.status_code}")
    print(f"RESPONSE: {response.json()}")
except Exception as e:
    print(f"ERROR: {e}")
