
import sys
import os
import json

# Add project root to path
sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.configuracion_fe import ConfiguracionFE
from app.models.empresa import Empresa

def verify_config():
    session = SessionLocal()
    try:
        configs = session.query(ConfiguracionFE).all()
        print(f"Encontradas {len(configs)} configuraciones de FE.\n")
        
        for conf in configs:
            empresa = session.query(Empresa).get(conf.empresa_id)
            emp_nombre = empresa.razon_social if empresa else f"ID {conf.empresa_id}"
            
            print(f"--- Empresa: {emp_nombre} ---")
            print(f"Ambiente DB: {conf.ambiente}")
            print(f"Habilitado: {conf.habilitado}")
            
            # Check Credentials
            if not conf.api_token:
                print("[ERROR] No hay campo api_token (Credenciales JSON).")
            else:
                try:
                    creds = json.loads(conf.api_token)
                    client_id = creds.get('client_id', 'MISSING')
                    bg_env = "SANDBOX" if "sandbox" in (creds.get('username') or "") else "UNKNOWN"
                    print(f"[OK] Credenciales JSON parseadas correctamente.")
                    print(f"   Client ID: {client_id[:5]}...")
                    print(f"   Username hint: {creds.get('username')}")
                    
                    if conf.ambiente != 'PRUEBAS':
                        print("[WARNING] El ambiente NO esta marcado como PRUEBAS.")
                    else:
                        print("[OK] Ambiente configurado correctamente como PRUEBAS.")
                        
                except json.JSONDecodeError:
                    print("[ERROR] api_token no contiene un JSON valido.")
            print("-" * 30 + "\n")
            
    finally:
        session.close()

if __name__ == "__main__":
    verify_config()
