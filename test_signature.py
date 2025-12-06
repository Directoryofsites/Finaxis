import sys
import os
import json
import hmac
import hashlib

# Add project root to path
sys.path.append(os.getcwd())

from app.core.config import settings
from app.services.migracion import compute_signature

def test_signature():
    print("Testing Digital Signature Logic...")
    
    # 1. Create dummy data
    data = {"empresa": {"nombre": "Test Corp", "cupos": 100}}
    print(f"Original Data: {data}")
    
    # 2. Sign it
    signature = compute_signature(data)
    print(f"Generated Signature: {signature}")
    
    # 3. Verify (Success Case)
    computed = compute_signature(data)
    if hmac.compare_digest(computed, signature):
        print("Verification PASSED for valid data.")
    else:
        print("Verification FAILED for valid data.")
        
    # 4. Tamper data (Failure Case)
    tampered_data = data.copy()
    tampered_data["empresa"]["cupos"] = 9999 # Hacker attack!
    print(f"Tampered Data: {tampered_data}")
    
    computed_tampered = compute_signature(tampered_data)
    if hmac.compare_digest(computed_tampered, signature):
        print("CRITICAL: Verification PASSED for tampered data! (Security Flaw)")
    else:
        print("Verification FAILED for tampered data (Security Active).")

if __name__ == "__main__":
    test_signature()
