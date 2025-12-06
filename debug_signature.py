import json
import hmac
import hashlib
import os
from dotenv import load_dotenv

# Load env exactly like the app
load_dotenv(r"c:\ContaPY2\.env")
SECRET_KEY = os.getenv("SECRET_KEY")

def compute_signature(data: dict) -> str:
    """Replicates the backend logic exactly."""
    # Ordenamos las llaves para asegurar consistencia en la serialización
    json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        json_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

def verify():
    print(f"Loaded SECRET_KEY: {SECRET_KEY[:5]}...{SECRET_KEY[-5:]}")
    
    file_path = r"c:\ContaPY2\Manual\maestros\Maestro_Impuestos.json"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = json.load(f)
    
    data = content.get("data")
    existing_signature = content.get("signature")
    
    if not data:
        print("ERROR: No 'data' key found in JSON.")
        return
        
    computed = compute_signature(data)
    
    print(f"Existing Signature: {existing_signature}")
    print(f"Computed Signature: {computed}")
    
    if existing_signature == computed:
        print("SUCCESS: Signatures match!")
    else:
        print("FAILURE: Signatures do NOT match.")

if __name__ == "__main__":
    verify()
