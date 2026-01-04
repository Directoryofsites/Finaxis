
import os
import struct

base_path = r"c:\ContaPY2\backups\modelos\inf 1"
files = {
    "CONI": "CONI1621.XXX",
    "COMA": "COMA1621.XXX",
    "COTE": "COTE1621.XXX"
}

def hex_dump(data, start_offset=0):
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        hex_vals = ' '.join(f"{b:02x}" for b in chunk)
        ascii_vals = ''.join((chr(b) if 32 <= b < 127 else '.') for b in chunk)
        print(f"{start_offset+i:06x}: {hex_vals:<48} | {ascii_vals}")

def analyze_coni():
    path = os.path.join(base_path, files["CONI"])
    print(f"\nAnalyzing CONI (Third Parties) - {path}")
    with open(path, 'rb') as f:
        content = f.read()
    
    # Target: "SODIMAC"
    target = b'SODIMAC'
    idx = content.find(target)
    if idx != -1:
        print(f"Found '{target.decode()}' at offset {idx}")
        # Show context around it
        start = max(0, idx - 64)
        end = min(len(content), idx + 128)
        hex_dump(content[start:end], start)
        
        # Look for the NIT associated (likely nearby digits)
    else:
        print(f"Target '{target.decode()}' not found.")

def analyze_coma():
    path = os.path.join(base_path, files["COMA"])
    print(f"\nAnalyzing COMA (Accounts) - {path}")
    with open(path, 'rb') as f:
        content = f.read()
    
    # Target: "ADELANTOS AL PERSONAL" (seen in dump)
    target = b'ADELANTOS AL PERSONAL'
    idx = content.find(target)
    if idx != -1:
        print(f"Found '{target.decode()}' at offset {idx}")
        # Show context
        start = max(0, idx - 32) # Look before for the code 1635..
        end = min(len(content), idx + 64)
        hex_dump(content[start:end], start)
    else:
        print(f"Target '{target.decode()}' not found.")

def analyze_cote():
    path = os.path.join(base_path, files["COTE"])
    print(f"\nAnalyzing COTE (Moves) - {path}")
    with open(path, 'rb') as f:
        content = f.read()
        
    # Target: "511028...001094..." (seen in dump)
    target = b'5110280000000000001094901541'
    idx = content.find(target)
    if idx != -1:
        print(f"Found composite key at offset {idx}")
        start = max(0, idx - 32)
        end = min(len(content), idx + 64)
        hex_dump(content[start:end], start)
    else:
        print("Composite target not found, trying partial...")

if __name__ == "__main__":
    analyze_coni()
    analyze_coma()
    analyze_cote()
