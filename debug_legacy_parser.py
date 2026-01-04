
import sys
import os
import struct
import re

# Mocking the service logic to avoid complex imports from app.*
# I'll paste the relevant logic here to ensure exact reproduction
class LegacyParsingService:
    @staticmethod
    def parse_coma_accounts(file_content: bytes):
        accounts = []
        total_len = len(file_content)
        for i in range(0, total_len, 64):
            chunk = file_content[i:i+64]
            if len(chunk) < 64: break
            try:
                code_raw = chunk[0:16].decode('latin1', errors='ignore').strip()
                code_clean = "".join(c for c in code_raw if c.isdigit())
                if not code_clean: continue
                if len(code_clean) < 1: continue

                name_raw = chunk[16:56].decode('latin1', errors='ignore').strip()
                name_clean = name_raw.replace('\x00', '')
                if not name_clean: continue
                
                # EMULATING THE IMPORT LOGIC THAT MIGHT FAIL
                # The service does: int(acc["codigo"][0])
                try:
                    clase = int(code_clean[0])
                except Exception as e:
                    print(f"ERROR parsing class for code '{code_clean}': {e}")
                    raise e
                
                accounts.append({"codigo": code_clean, "nombre": name_clean})
            except Exception as e:
                print(f"Error in COMA loop: {e}")
                continue
        return accounts

    @staticmethod
    def parse_coni_third_parties(file_content: bytes):
        third_parties = []
        record_size = 128
        for i in range(0, len(file_content), record_size):
            chunk = file_content[i:i+record_size]
            if len(chunk) < record_size: break
            try:
                chunk_str = chunk.decode('latin1', errors='ignore')
                digits = re.findall(r'\d{5,}', chunk_str)
                
                if digits:
                    nit_raw = digits[-1]
                    print(f"Debug CONI: Trying to convert '{nit_raw}' to int")
                    nit_clean = str(int(nit_raw))
                    
                    name_chunk = chunk[0:60].decode('latin1', errors='ignore').strip()
                    name_clean = "".join(c for c in name_chunk if 32 <= ord(c) < 127).strip()
                    
                    if name_clean:
                        third_parties.append({"nit": nit_clean, "razon_social": name_clean})
            except Exception as e:
                print(f"ERROR in CONI loop at offset {i}: {e}")
                raise e
        return third_parties

    @staticmethod
    def parse_cotr_transactions(file_content: bytes):
        transactions = []
        record_size = 40
        start_offset = 0
        pattern = b'\xff\xff\xff\xff'
        first_match = file_content.find(pattern)
        if first_match != -1: start_offset = first_match
        
        for i in range(start_offset, len(file_content), record_size):
            chunk = file_content[i:i+record_size]
            if len(chunk) < record_size: break
            if chunk[0:4] != b'\xff\xff\xff\xff': continue
                
            try:
                val1 = struct.unpack('>i', chunk[32:36])[0]
                val2 = struct.unpack('>i', chunk[36:40])[0]
                # These are already ints, so no int() call likely to fail here unless... 
            except:
                continue
        return transactions

def test_files():
    base_path = r"c:\ContaPY2\backups\modelos\inf 1"
    
    # 1. COMA
    try:
        with open(os.path.join(base_path, "COMA1621.XXX"), 'rb') as f:
            print("--- Testing COMA ---")
            LegacyParsingService.parse_coma_accounts(f.read())
    except Exception as e:
        print(f"COMA Failed: {e}")

    # 2. CONI
    try:
        with open(os.path.join(base_path, "CONI1621.XXX"), 'rb') as f:
            print("\n--- Testing CONI ---")
            LegacyParsingService.parse_coni_third_parties(f.read())
    except Exception as e:
        print(f"CONI Failed: {e}")

    # 3. COTR
    try:
        with open(os.path.join(base_path, "COTR1621.ABR"), 'rb') as f:
             print("\n--- Testing COTR ---")
             LegacyParsingService.parse_cotr_transactions(f.read())
    except Exception as e:
        print(f"COTR Failed: {e}")

if __name__ == "__main__":
    test_files()
