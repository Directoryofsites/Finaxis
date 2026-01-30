
import csv

def cleanup_csv(input_path, output_path):
    print(f"Cleaning {input_path}...")
    
    clean_rows = []
    
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or len(row) < 2: continue
            
            code = row[0].strip()
            name = row[1].strip()
            
            # Filter 1: Code must not start with 0
            if code.startswith('0'): continue
            
            # Filter 2: Name must not contain 'ÿ'
            if 'ÿ' in name: continue
            
            # Filter 3: Name must have some alphabet chars
            if not any(c.isalpha() for c in name): continue
            
            # Filter 4: Name length reasonable
            if len(name) < 3: continue
            
            clean_rows.append([code, name])
            
    print(f"Kept {len(clean_rows)} valid rows.")
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(clean_rows)
        
    print(f"Saved cleaned file to {output_path}")

if __name__ == "__main__":
    cleanup_csv(r"c:\ContaPY2\PUC_PARA_IMPORTAR.csv", r"c:\ContaPY2\PUC_PARA_IMPORTAR.csv")
