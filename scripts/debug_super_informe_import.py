
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    print("Attempting to import app.services.super_informe...")
    from app.services import super_informe
    print("Import successful!")
except Exception as e:
    print(f"IMPORT ERROR: {e}")
    import traceback
    traceback.print_exc()
