
import os

def test_coma_parsing():
    filepath = r"c:\ContaPY2\backups\modelos\inf 1\COMA1621.XXX"
    if not os.path.exists(filepath):
        print("File not found")
        return

    print(f"Testing COMA parsing on {filepath}")
    with open(filepath, 'rb') as f:
        file_content = f.read()

    accounts = []
    # Dynamic scan logic + Strict Filter
    start_offset = 1024 # Skip initial header
    total_len = len(file_content)
    
    # We will search for alignment dynamically
    # But seeing the garbage, maybe just strict filtering is enough
    
    # Try iterating every 64 bytes and printing what PASSES the filter
    print("\n--- Valid Accounts Found (Code starts with 1-9) ---")
    
    found_count = 0
    # Try multiple alignments to be safe: 0, 16, 32, 48... NO, usually it's mod 64.
    # But let's check strict filter efficacy first.
    
    for offset in range(0, 64): # Scan all phases
        # print(f"Checking alignment offset {offset}")
        valid_in_this_phase = 0
        
        for i in range(1024 + offset, total_len, 64):
            chunk = file_content[i:i+64]
            if len(chunk) < 64: break
            
            try:
                code_raw = chunk[0:16].decode('latin1', errors='ignore').strip()
                code_clean = "".join(c for c in code_raw if c.isdigit())
                
                # STRICT FILTER
                if not code_clean: continue
                if code_clean.startswith('0'): continue # KILL GARBAGE
                if len(code_clean) < 4: continue
                
                name_raw = chunk[16:56].decode('latin1', errors='ignore').replace('\x00', '').strip()
                if len(name_raw) < 3: continue
                if not any(c.isalpha() for c in name_raw): continue # Must have letters
                
                valid_in_this_phase += 1
                if valid_in_this_phase <= 5: # Print first 5 of this phase
                    print(f"Phase {offset} | Code: {code_clean} | Name: {name_raw}")
                    
            except:
                pass
        
        if valid_in_this_phase > 10:
            print(f"===> PHASE {offset} looks promising with {valid_in_this_phase} valid records.")

if __name__ == "__main__":
    test_coma_parsing()
