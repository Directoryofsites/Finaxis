
import sys
import os
import json
sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.configuracion_fe import ConfiguracionFE

def inspect_token():
    session = SessionLocal()
    try:
        empresa_id = 134
        config = session.query(ConfiguracionFE).filter_by(empresa_id=empresa_id).first()
        
        if not config or not config.api_token:
            print("No config or token found")
            return
            
        try:
            creds = json.loads(config.api_token)
            print("Keys found in api_token:", list(creds.keys()))
            print("Username/Email present:", creds.get('username') or creds.get('email'))
        except Exception as e:
            print(f"JSON Error: {e}")
            print(f"Raw Token: {config.api_token[:50]}...")
            
    finally:
        session.close()

if __name__ == "__main__":
    inspect_token()
