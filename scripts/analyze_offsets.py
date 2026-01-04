# scripts/analyze_offsets.py
import sys
import os

def analyze():
    file_path = "backups/modelos/inf 1/AA99.TXT"
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, "rb") as f:
        content = f.read().decode('latin1', errors='ignore')
        
    lines = content.splitlines()
    
    # Print a ruler
    ruler1 = "0" * 10 + "1" * 10 + "2" * 10 + "3" * 10 + "4" * 10 + "5" * 10 + "6" * 10 + "7" * 10 + "8" * 10 + "9" * 10 + "10" * 10 + "11" * 10 + "12" * 10 + "13" * 10 + "14" * 10 + "15" * 10 + "16" * 10
    ruler2 = "0123456789" * 17
    
    print(ruler1)
    print(ruler2)
    
    count = 0
    for line in lines:
        if not line.strip(): continue
        # Print first 10 lines
        print(line)
        
        # Analyze specific line for indices
        if "901464119" in line:
            print(f"-- NIT 901464119 starts at: {line.find('901464119')}")
            print(f"-- NAME IGLESIA starts at: {line.find('IGLESIA')}")
            print(f"-- ACCOUNT 110505 starts at: {line.find('110505')}")
            print(f"-- ACC NAME starts at: {line.find('CAJA GENERAL')}")
            # print(f"-- CREDIT/DEBIT starts at: {line.find('490,500.00')}")
            
        count += 1
        if count > 10: break

if __name__ == "__main__":
    analyze()
