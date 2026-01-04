
import struct

file_path = r"c:\ContaPY2\backups\modelos\inf 1\COTR1621.ABR"

def parse_record(chunk):
    # Format:
    # 0-4: Header (FFFFFFFF)
    # 4-16: Text (12 bytes)
    # 16-32: Account (16 bytes)
    # 32-36: Value 1 (Int32 Big Endian)
    # 36-40: Value 2 (Int32 Big Endian)
    try:
        # Interpret text as ASCII
        text_part = chunk[4:16].decode('ascii', errors='replace')
        account_part = chunk[16:32].decode('ascii', errors='replace')
        
        # Interpret values as Big Endian Integers
        val1 = struct.unpack('>i', chunk[32:36])[0]
        val2 = struct.unpack('>i', chunk[36:40])[0]
        
        return {
            "ref": text_part,
            "account": account_part,
            "val1": val1,
            "val2": val2
        }
    except Exception as e:
        return {"error": str(e)}

def extract_sample(path):
    record_size = 40
    print(f"{'REF/DOC':<15} | {'ACCOUNT':<18} | {'VAL1':>10} | {'VAL2':>10}")
    print("-" * 60)
    
    with open(path, 'rb') as f:
        # Skip potential empty header? 
        # But our analysis found data starting at index 6212 (offset 0x1844 for account '1' -> 0x1834 start record)
        # 0x1834 = 6196 decimal
        
        # Let's start reading from 6196
        f.seek(6196)
        
        for _ in range(20):
            chunk = f.read(record_size)
            if len(chunk) < record_size:
                break
            
            # Check for FFFFFFFF marker to be sure we are aligned
            if chunk[0:4] == b'\xff\xff\xff\xff':
                data = parse_record(chunk)
                if "error" not in data:
                    print(f"{data['ref']:<15} | {data['account']:<18} | {data['val1']:10d} | {data['val2']:10d}")
            else:
                # print(f"Skipping misaligned chunk: {chunk[:4].hex()}")
                pass

if __name__ == "__main__":
    extract_sample(file_path)
