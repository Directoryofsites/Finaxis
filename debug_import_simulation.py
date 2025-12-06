import json
import os
import sys

# Mocking SQLAlchemy models and session for simulation
class MockModel:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def simulate_import():
    json_path = r"c:\ContaPY2\Manual\maestros\PUC_Clase_1_Activos.json"
    
    if not os.path.exists(json_path):
        print("JSON file not found.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    rows = data['data']['maestros']['plan_cuentas']
    print(f"Total accounts in JSON: {len(rows)}")
    
    # Simulate existing accounts (empty for now, or populate if we knew the DB state)
    existing_codes = set() 
    # existing_codes = {'1', '11', ...} # Uncomment to simulate partial DB
    
    by_level = {}
    for r in rows:
        lvl = r.get('nivel', 1)
        if lvl not in by_level: by_level[lvl] = []
        by_level[lvl].append(r)
        
    count_created = 0
    count_skipped = 0
    
    for lvl in sorted(by_level.keys()):
        print(f"Processing Level {lvl} ({len(by_level[lvl])} accounts)...")
        for item in by_level[lvl]:
            key = str(item.get('codigo')).strip()
            
            # Check for potential issues
            if not key.isdigit():
                print(f"WARNING: Non-digit code found: {key} - {item.get('nombre')}")
            
            if key in existing_codes:
                count_skipped += 1
            else:
                # Simulate creation
                existing_codes.add(key)
                count_created += 1
                
                # Check specific account that failed
                if key == "124010":
                    print(f"SUCCESS: Account 124010 would be created. Name: {item.get('nombre')}")
                    
    print(f"Simulation Complete. Created: {count_created}, Skipped: {count_skipped}")

if __name__ == "__main__":
    simulate_import()
