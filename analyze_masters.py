
import os
import struct
import re

# Paths
base_path = r"c:\ContaPY2\backups\modelos\inf 1"
files = {
    "CONI": os.path.join(base_path, "CONI1621.XXX"), # Third Parties
    "COMA": os.path.join(base_path, "COMA1621.XXX"), # Accounts
    "COTE": os.path.join(base_path, "COTE1621.XXX")  # Third Party Moves
}

def analyze_file(name, path):
    print(f"\n{'='*40}")
    print(f"ANALYZING: {name} ({os.path.basename(path)})")
    print(f"{'='*40}")
    
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    try:
        with open(path, 'rb') as f:
            content = f.read()
            
        total_size = len(content)
        print(f"Total Size: {total_size} bytes")
        
        # 1. Find text density to guess record start
        # Many DOS files have a header. Let's look for the first dense text block.
        text_start = 0
        for i in range(0, min(2000, total_size), 16):
            chunk = content[i:i+16]
            # Simple heuristic: if > 50% bytes are ASCII printable text
            txt_chars = sum(1 for b in chunk if 32 <= b < 127)
            if txt_chars > 8:
                text_start = i
                break
        
        print(f"Likely data start offset: {text_start}")
        
        # 2. Dump a sample block from likely start
        print("\n--- HEX DUMP (First 5 records approx 512 bytes) ---")
        dump_end = min(total_size, text_start + 512)
        chunk = content[text_start:dump_end]
        
        for i in range(0, len(chunk), 16):
            sub = chunk[i:i+16]
            hex_vals = ' '.join(f"{b:02x}" for b in sub)
            text = ''.join((chr(b) if 32 <= b < 127 else '.') for b in sub)
            print(f"{text_start+i:04x}: {hex_vals:<48} | {text}")
            
        # 3. Frequency Analysis (Finding Delimiters or Record Length)
        # Often records start with a specific byte or have 00 padding at fixed intervals
        if total_size > 0:
            print("\n--- PATTERN SEARCH ---")
            # Common NIT/ID patterns (digits)
            if name == "CONI":
                 # Look for what looks like a NIT (sequences of digits)
                 # Converting a chunk to string to use regex might be easier for quick scan
                 sample_str = chunk.decode('latin1', errors='ignore')
                 # Find sequences of 6+ digits
                 nits = re.findall(r'\d{6,}', sample_str)
                 print(f"Possible IDs found: {nits[:5]}")
                 
            if name == "COMA":
                # Accounts usually start with 1105...
                sample_str = chunk.decode('latin1', errors='ignore')
                accs = re.findall(r'[1-9]\d{3,}', sample_str)
                print(f"Possible Accounts found: {accs[:5]}")

    except Exception as e:
        print(f"Error analyzing {name}: {e}")

if __name__ == "__main__":
    for k, v in files.items():
        analyze_file(k, v)
