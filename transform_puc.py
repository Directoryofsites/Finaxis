
import re
import csv

def transform_legacy_puc(input_path, output_path):
    print(f"Reading {input_path}...")
    
    with open(input_path, 'rb') as f:
        content = f.read()
        
    # Attempt to decode
    try:
        text_content = content.decode('utf-8', errors='ignore')
    except:
        text_content = content.decode('latin1', errors='ignore')
        
    lines = text_content.split('\n')
    accounts = []
    
    print(f"Found {len(lines)} lines. Parsing...")
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Format found in file: "1105050000000000CAJA GENERAL"
        # 16 digits followed by Text.
        # Regex: Start with 4+ digits.
        match = re.match(r'^(\d{4,16})(.+)$', line)
        if match:
            code = match.group(1).strip()
            name = match.group(2).strip()
            
            # Clean weird chars from name (like binary junk)
            name_clean = "".join(c for c in name if c.isalnum() or c in " -_./()")
            
            # Additional cleanup for 'ÿ' if present
            name_clean = name_clean.replace('ÿ', '')
            
            if len(code) >= 4 and len(name_clean) > 2:
                accounts.append([code, name_clean])
        else:
            # Fallback for "Code Name" with space
            parts = line.split(None, 1)
            if len(parts) == 2 and parts[0].isdigit() and len(parts[0]) >= 4:
                accounts.append([parts[0], parts[1].strip()])

    print(f"Extracted {len(accounts)} accounts.")
    
    # Sort by code
    accounts.sort(key=lambda x: x[0])
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['codigo', 'nombre'])
        writer.writerows(accounts)
        
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    transform_legacy_puc(r"c:\ContaPY2\temp_legacy.txt", r"c:\ContaPY2\PUC_PARA_IMPORTAR.csv")
