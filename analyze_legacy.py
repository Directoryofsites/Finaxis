
import os

def analyze_file(filepath):
    print(f"Analyzing {filepath}...")
    with open(filepath, 'rb') as f:
        content = f.read()

    print(f"Total size: {len(content)} bytes")

    # 1. Search for known strings to find alignment
    # "1105050000000000CAJA GENERAL"
    # "1635000000000000ADELANTOS AL PERSONAL"
    
    # Let's find "1105050000000000" (Caja General code)
    target_code = b"1105050000000000"
    offsets = []
    start = 0
    while True:
        idx = content.find(target_code, start)
        if idx == -1: break
        offsets.append(idx)
        start = idx + 1
    
    print(f"Found code '{target_code.decode()}' at offsets: {offsets}")
    
    if not offsets:
        print("Could not find specific code. Trying generic pattern...")
    else:
        # Check alignment from offsets
        # If we have multiple, checks diff
        if len(offsets) > 1:
            diffs = [offsets[i+1] - offsets[i] for i in range(len(offsets)-1)]
            print(f"Differences between occurences: {diffs}")
    
    # 2. Heuristic Scan for Record Size
    # Check if we can find a repeating size
    
    # Let's print a hex dump around the first match
    if offsets:
        first_match = offsets[0]
        start_dump = max(0, first_match - 32)
        end_dump = min(len(content), first_match + 128)
        print(f"\nHex Dump around offset {first_match} ({start_dump}-{end_dump}):")
        chunk = content[start_dump:end_dump]
        print(chunk)
        print("Hex:", chunk.hex())

    # Try 64 byte records
    print("\n--- Trying 64-byte decoding ---")
    try:
        count = 0
        for i in range(offsets[0] if offsets else 0, len(content), 64):
            chunk = content[i:i+64]
            if len(chunk) < 64: break
            try:
                code_raw = chunk[0:16].decode('latin1').strip()
                name_raw = chunk[16:56].decode('latin1').replace('\x00', '').strip()
                if code_raw.isdigit() and len(code_raw) >= 4 and len(name_raw) > 3:
                     print(f"Offset {i}: [{code_raw}] {name_raw}")
                     count += 1
                     if count > 5: break
            except: pass
    except Exception as e:
        print(e)
        
    # Try 256 byte records
    print("\n--- Trying 256-byte decoding ---")
    try:
        count = 0
        # If the file has a huge header, we need to find the first record.
        # Assuming the offsets found earlier are valid starts.
        start_scan = offsets[0] if offsets else 0
        
        for i in range(start_scan, len(content), 256):
             chunk = content[i:i+256]
             if len(chunk) < 64: break
             try:
                 # Standard layout: Code(16), Name(40 or more?)
                 code_raw = chunk[0:16].decode('latin1').strip()
                 name_raw = chunk[16:60].decode('latin1').replace('\x00', '').strip() # Try reading more for name
                 if code_raw.isdigit() and len(code_raw) > 3:
                     print(f"Offset {i}: [{code_raw}] {name_raw}")
                     count += 1
                     if count > 5: break
             except: pass
    except: pass

if __name__ == "__main__":
    analyze_file(r"c:\ContaPY2\temp_legacy.txt")
