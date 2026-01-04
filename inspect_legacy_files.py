
import os

def hex_dump_surrounding(content, index, context=64):
    start = max(0, index - context)
    end = min(len(content), index + context + len("TARGET"))
    chunk = content[start:end]
    
    # Visual pointer
    relative = index - start
    
    print(f"OFFSET MATCH: {index} (0x{index:x})")
    print(f"Hex: {' '.join(f'{b:02x}' for b in chunk)}")
    printable = "".join((chr(b) if 32 <= b < 127 else ".") for b in chunk)
    print(f"Txt: {printable}")
    print(f"     {' ' * relative}^ MATCH HERE")

def find_needles():
    files = {
        "COMA1621.XXX": [b"VACACIONES", b"PRIMA LEGAL", b"CESANTIAS"],
        "CONI1621.XXX": [b"DROGUERIA", b"BANCOLOMBIA", b"EL CAFE"],
        "COTR1621.ABR": [b"110505", b"233510"] # Common accounts
    }
    
    base_path = r"c:\ContaPY2\backups\modelos\inf 1"
    
    for filename, needles in files.items():
        filepath = os.path.join(base_path, filename)
        if not os.path.exists(filepath): continue
        
        print(f"\nScanning {filename}...")
        with open(filepath, 'rb') as f:
            content = f.read()
            
        for needle in needles:
            matches = []
            start = 0
            while True:
                idx = content.find(needle, start)
                if idx == -1: break
                matches.append(idx)
                start = idx + 1
            
            print(f"  Found '{needle.decode()}' at offsets: {matches[:3]}")
            if matches:
                hex_dump_surrounding(content, matches[0])

if __name__ == "__main__":
    find_needles()
