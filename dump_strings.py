
import os
import re

base_path = r"c:\ContaPY2\backups\modelos\inf 1"
files = ["CONI1621.XXX", "COMA1621.XXX", "COTE1621.XXX"]

def extract_strings(path, min_len=4):
    print(f"\n--- STRINGS IN {os.path.basename(path)} ---")
    try:
        with open(path, 'rb') as f:
            content = f.read()
            # Regex for printable ASCII sequences
            strings = re.findall(b'[ -~]{' + str(min_len).encode() + b',}', content)
            
            count = 0
            for s in strings:
                try:
                    decoded = s.decode('ascii')
                    # Filter out noise (like just numbers or symbols) if needed, 
                    # but for now we want to see everything to id field types.
                    print(f"{decoded}")
                    count += 1
                    if count > 50: # Limit output
                        print("... (truncated)")
                        break
                except:
                    pass
            
            if count == 0:
                print("(No strings found)")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    for fname in files:
        extract_strings(os.path.join(base_path, fname))
