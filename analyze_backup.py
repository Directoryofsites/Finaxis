
import os
import re

file_path = r"c:\ContaPY2\backups\modelos\inf 1\COTR1621.ABR"

def analyze_file(path):
    print(f"Analyzing: {path}")
    try:
        with open(path, 'rb') as f:
            content = f.read()
            
        print(f"Total Size: {len(content)} bytes")
        
        # Find first non-zero byte
        first_data = next((i for i, b in enumerate(content) if b != 0), None)
        print(f"First non-zero byte at index: {first_data}")
        
        # Find specific account pattern "1105"
        pattern = b'1105'
        matches = [m.start() for m in re.finditer(pattern, content)]
        
        print(f"Found {len(matches)} occurrences of '1105'")
        if len(matches) > 0:
            print(f"First 5 matches at: {matches[:5]}")
            if len(matches) > 1:
                diff_list = [matches[i+1] - matches[i] for i in range(min(10, len(matches)-1))]
                print(f"Distances between first few '1105': {diff_list}")
                
            # Use the first match as anchor
            anchor = matches[0]
            start = max(0, anchor - 32)
            end = min(len(content), start + 512)
            
            print("-" * 20)
            print(f"Context from {start} to {end} (Hex + ASCII):")
            chunk = content[start:end]
            for i in range(0, len(chunk), 16):
                sub = chunk[i:i+16]
                hex_vals = ' '.join(f"{b:02x}" for b in sub)
                text = ''.join((chr(b) if 32 <= b < 127 else '.') for b in sub)
                print(f"{start+i:06x}: {hex_vals:<48} | {text}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_file(file_path)
