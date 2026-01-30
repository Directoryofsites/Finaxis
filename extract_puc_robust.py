
import re
import csv

def extract_strings_and_parse(input_path, output_path):
    print(f"Reading {input_path}...")
    with open(input_path, 'rb') as f:
        content = f.read()

    # Decode to latin1 to preserve byte-to-char mapping 1:1
    try:
        text = content.decode('utf-8')
    except:
        text = content.decode('latin1')
    
    # Remove nulls for easier regex
    # text = text.replace('\x00', ' ')
    
    # Regex Strategy:
    # Look for 8 to 16 Digits (The Code)
    # Followed by Content (The Name)
    # Stop when we see another sequence of 8+ Digits OR End of String.
    # formatting: Code(Group 1), Name(Group 2)
    # Use DOTALL so '.' matches newlines if any are embedded in the stream
    
    # We use \d{8,20} to be safe.
    # Lookahead (?=\d{8,}|$) ensures we stop before the next code.
    
    pattern = re.compile(r'(\d{6,20})\s*([^\d]+?)(?=\d{6,20}|$)', re.DOTALL)
    
    # Refined Regex:
    # If Name contains a digit? e.g. "CAJA 1".
    # The [^\d] excludes digits in name. That's safer but might truncate "CAJA 1".
    # But given the dump format, names seem to be text.
    # Let's try to allow digits if they are short?
    # Or just rely on the Lookahead of 6+ digits.
    
    pattern = re.compile(r'(\d{6,20})(.+?)(?=\d{6,20}|$)', re.DOTALL)

    matches = pattern.findall(text)
    
    print(f"Found {len(matches)} potential matches.")
    
    clean_accounts = []
    seen_codes = set()
    
    for code, raw_name in matches:
        code = code.strip()
        
        # Clean the name
        # Remove nulls, weird chars
        name = "".join(c for c in raw_name if c.isprintable()).strip()
        
        if len(code) < 4: continue
        if len(name) < 3: continue
        
        # Filter: if name is just junk
        if not any(c.isalpha() for c in name): continue
        
        if code in seen_codes: continue
        
        seen_codes.add(code)
        clean_accounts.append([code, name])

    print(f"Extracted {len(clean_accounts)} unique accounts.")
    
    # Sort
    clean_accounts.sort(key=lambda x: x[0])
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # writer.writerow(['codigo', 'nombre'])
        writer.writerows(clean_accounts)
        
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    extract_strings_and_parse(r"c:\ContaPY2\temp_legacy.txt", r"c:\ContaPY2\PUC_PARA_IMPORTAR.csv")
