
import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://127.0.0.1:8000/api"

def check_api():
    # 1. Login
    try:
        url = f"{BASE_URL}/auth/login"
        data = urllib.parse.urlencode({"username": "soporte@soporte.com", "password": "Jh811880"}).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        
        with urllib.request.urlopen(req) as resp:
            if resp.status != 200:
                print(f"[ERROR] Login Failed: {resp.status}")
                return
            resp_body = resp.read().decode()
            token = json.loads(resp_body).get("access_token")
            print(f"[OK] Login Successful. Token obtained.")
    except Exception as e:
        print(f"[ERROR] Connection Error: {e}")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # Helper function for GET
    def get_json(endpoint):
        try:
            req = urllib.request.Request(f"{BASE_URL}{endpoint}", headers=headers)
            with urllib.request.urlopen(req) as r:
                if r.status == 200:
                    return json.loads(r.read().decode())
        except Exception as e:
            print(f"[ERROR] Fetching {endpoint}: {e}")
        return None

    # 2. Get Recetas
    print("--> Fetching Recetas...")
    recetas = get_json("/produccion/recetas")
    if recetas is not None:
        print(f"[OK] Recetas Found: {len(recetas)}")
        for r in recetas:
            print(f"   [{r['id']}] {r['nombre']} (Activa: {r.get('activa')})")
    
    # 3. Get Ordenes
    print("--> Fetching Ordenes...")
    ordenes = get_json("/produccion/ordenes")
    if ordenes is not None:
        print(f"[OK] Ordenes Found: {len(ordenes)}")
        for o in ordenes:
            print(f"   [{o['id']}] {o['numero_orden']} (Estado: {o.get('estado')})")

if __name__ == "__main__":
    check_api()
