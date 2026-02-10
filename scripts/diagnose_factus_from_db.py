import sys
import os
import json
import requests

# Setup path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.configuracion_fe import ConfiguracionFE
from app.models.empresa import Empresa

def diagnose_factus():
    db = SessionLocal()
    try:
        print("--- DIAGNOSTICO FACTUS (CREDENCIALES DB) ---")
        
        # Obtener configuraciones
        configs = db.query(ConfiguracionFE).all()
        if not configs:
            print("[X] No se encontraron configuraciones de FE en la base de datos.")
            return

        for config in configs:
            empresa = db.query(Empresa).get(config.empresa_id)
            nombre_empresa = empresa.razon_social if empresa else f"Empresa {config.empresa_id}"
            
            print(f"\n[EMP] Analizando: {nombre_empresa} (ID: {config.empresa_id})")
            print(f"   Ambiente: {config.ambiente}")
            print(f"   Habilitado: {config.habilitado}")
            
            if not config.api_token:
                print("   [X] No tiene token API configurado.")
                continue
                
            try:
                creds = json.loads(config.api_token)
            except:
                print("   [X] Error decodificando JSON de credenciales.")
                continue

            # Extraer credenciales
            client_id = creds.get("client_id")
            client_secret = creds.get("client_secret")
            username = creds.get("username")
            password = creds.get("password")
            
            print(f"   Usuario API: {username}")
            
            # Intentar Login
            base_url = "https://api-sandbox.factus.com.co" if config.ambiente == 'PRUEBAS' else "https://api.factus.com.co"
            auth_url = f"{base_url}/oauth/token"
            
            try:
                resp = requests.post(auth_url, data={
                    "grant_type": "password",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "username": username,
                    "password": password
                })
                
                if resp.status_code == 200:
                    print("   [OK] Autenticacion EXITOSA.")
                    token = resp.json()['access_token']
                    
                    # Consultar ultimas facturas
                    print("   [INFO] Consultando ultimas facturas...")
                    resp_bills = requests.get(f"{base_url}/v1/bills?page=1", headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/json"
                    })
                    
                    if resp_bills.status_code == 200:
                        data = resp_bills.json()
                        bills = data.get('data', {}).get('bills', [])
                        # Fallback structure
                        if not bills and 'data' in data.get('data', {}):
                             bills = data.get('data', {}).get('data', [])
                             
                        print(f"   [DOCS] Se encontraron {len(bills)} facturas recientes.")
                        for bill in bills[:5]:
                            status = bill.get('status')
                            dian_status = bill.get('dian_status')
                            number = bill.get('number')
                            msg = bill.get('api_client_name') or "Sin mensaje"
                            print(f"      - {number}: Estado={status}, DIAN={dian_status}")
                    else:
                        print(f"   [!] Error listando facturas: {resp_bills.status_code} - {resp_bills.text[:100]}")
                        
                else:
                    print(f"   [X] Fallo al autenticar: {resp.status_code}")
                    print(f"   Respuesta: {resp.text}")
                    
            except Exception as e:
                print(f"   [X] Excepcion de conexion: {e}")
                
    finally:
        db.close()

if __name__ == "__main__":
    diagnose_factus()
