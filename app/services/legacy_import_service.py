
import struct
import re
from datetime import date
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models import (
    PlanCuenta, 
    Tercero, 
    Documento, 
    MovimientoContable, 
    Empresa,
    TipoDocumento
)
from app.services import documento as documento_service
from app.services.import_utils import ImportUtils

class LegacyParsingService:
    
    @staticmethod
    def parse_coma_accounts(file_content: bytes) -> List[Dict[str, Any]]:
        accounts = []
        record_size = 64
        total_len = len(file_content)
        
        # 1. Determine Alignment
        # Search for a pattern like "1105" followed by zeros, or just a known 4+ digit code
        # We scan the first 16KB to find a "lock".
        # Regex: Digit{4,8} followed by 0x00
        
        start_scan = 0
        alignment_offset = 0
        
        # Heuristic: Look for a block of text that looks like a name, preceded by digits
        # Sample: "510595...VACACIONES"
        # Code is 16 bytes. Name is 40 bytes.
        
        for i in range(1024, min(16384, total_len)):
             # Check if this byte starts a valid code (digits)
             chunk = file_content[i:i+64]
             if len(chunk) < 64: break
             
             code_raw = chunk[0:16].decode('latin1', errors='ignore').strip()
             code_clean = "".join(c for c in code_raw if c.isdigit())
             
             # If code is valid (e.g. >3 digits) and Name is nice text
             if len(code_clean) >= 4:
                 name_raw = chunk[16:56].decode('latin1', errors='ignore').replace('\x00', '').strip()
                 if len(name_raw) > 3 and any(c.isalpha() for c in name_raw):
                     # FOUND LOCK
                     alignment_offset = i % 64
                     break
        
        print(f"COMA Alignment Found: {alignment_offset}")
        
        seen_codes = set()
        
        # Start from the first aligned block after header (or 0)
        # Ensure we start > 0 if offset is small
        start_index = 1024 + alignment_offset
        if start_index % 64 != alignment_offset:
            start_index += (64 - (start_index % 64)) + alignment_offset

        for i in range(start_index, total_len, 64):
            # Re-align check? No, trust grid.
            if (i % 64) != alignment_offset: 
                 # This shouldn't happen with range step 64
                 continue

            chunk = file_content[i:i+64]
            if len(chunk) < 64: break
            
            try:
                code_raw = chunk[0:16].decode('latin1', errors='ignore').strip()
                code_clean = "".join(c for c in code_raw if c.isdigit())
                
                if not code_clean or len(code_clean) < 1: continue
                if code_clean.startswith("0"): continue # Strict Filter
                
                if code_clean in seen_codes: continue

                name_raw = chunk[16:56].decode('latin1', errors='ignore').replace('\x00', '').strip()
                if not name_raw or not any(c.isalpha() for c in name_raw): continue
                
                seen_codes.add(code_clean)
                accounts.append({
                    "codigo": code_clean,
                    "nombre": name_raw
                })
            except:
                continue
                
        return accounts

    @staticmethod
    def parse_coni_third_parties(file_content: bytes) -> List[Dict[str, Any]]:
        third_parties = []
        seen_nits = set()
        
        # Alignment for CONI
        # Record size 128
        # We look for a Name (offset 0-60) that is valid text
        alignment_offset = 0
        
        # Scan to find a good name
        for i in range(1024, min(16384, len(file_content))):
             chunk = file_content[i:i+64] # Just check start (Name)
             name_cand = chunk[0:40].decode('latin1', errors='ignore').replace('\x00', '').strip()
             
             # Heuristic: Valid Name?
             if len(name_cand) > 5 and " " in name_cand and any(c.isalpha() for c in name_cand):
                 # Check if mostly alphanumeric
                 alphas = sum(c.isalpha() for c in name_cand)
                 if alphas > len(name_cand) * 0.5:
                      alignment_offset = i % 128
                      break
        
        print(f"CONI Alignment Found: {alignment_offset}")
        
        start_index = 1024
        # Adjust start index to match alignment
        curr_mod = start_index % 128
        diff = (alignment_offset - curr_mod + 128) % 128
        start_index += diff
        
        record_size = 128
        
        for i in range(start_index, len(file_content), record_size):
            chunk = file_content[i:i+record_size]
            if len(chunk) < record_size: break
            
            try:
                name_chunk = chunk[0:60].decode('latin1', errors='ignore').strip()
                name_clean = "".join(c for c in name_chunk if 32 <= ord(c) < 127).strip()
                
                if not name_clean or len(name_clean) < 3 or not any(c.isalpha() for c in name_clean): continue

                chunk_str = chunk.decode('latin1', errors='ignore')
                digits = re.findall(r'\d{5,}', chunk_str)
                
                if digits:
                    nit_raw = digits[-1]
                    nit_clean = str(int(nit_raw))
                    if nit_clean in seen_nits or nit_clean == "0" or nit_clean.startswith("0"): continue
                    
                    seen_nits.add(nit_clean)
                    third_parties.append({
                        "nit": nit_clean,
                        "razon_social": name_clean
                    })
            except:
                continue
                
        return third_parties

    @staticmethod
    def parse_cotr_transactions(file_content: bytes) -> List[Dict[str, Any]]:
        transactions = []
        # Free search for FFFFFFFF
        pattern = b'\xff\xff\xff\xff'
        start = 0
        
        # Iterate FIND
        while True:
            idx = file_content.find(pattern, start)
            if idx == -1: break
            
            # Start of this record is idx
            # Record body is 40 bytes (4 header + 36 data)
            chunk = file_content[idx:idx+40]
            if len(chunk) < 40: break
            
            start = idx + 1 # Continue search
            
            try:
                # 0-4: FFFF
                # 4-16: Ref
                ref_raw = chunk[4:16].decode('latin1', errors='ignore').replace('\x00', '').strip()
                ref_clean = "".join(c for c in ref_raw if c.isalnum() or c in "-_/.")
                if not ref_clean: ref_clean = "LEGACY-UNK"
                
                # 16-32: Acc
                acc_raw = chunk[16:32].decode('latin1', errors='ignore').replace('\x00', '').strip()
                acc_clean = "".join(c for c in acc_raw if c.isdigit())
                
                # Validation
                if not acc_clean: continue
                
                val1 = struct.unpack('>i', chunk[32:36])[0]
                val2 = struct.unpack('>i', chunk[36:40])[0]
                
                transactions.append({
                    "doc_ref": ref_clean,
                    "cuenta": acc_clean,
                    "debito": float(val1),
                    "credito": float(val2)
                })
            except:
                continue
                
        return transactions

    # ... (Parsing methods remain unchanged) ...

    @staticmethod
    def parse_txt_report(file_content: bytes) -> List[Dict[str, Any]]:
        """
        Parses the fixed-width TXT report (AA99.TXT) based on the User's Custom Layout.
        
        Layout Configuration (from Image):
        1. FECHA (10)
        2. TIPO Y NUMERO (9)
        3. CUENTA (10)
        4. NIT (12)
        5. NOMBRE BENEFICIARIO (27)
        6. NOMBRE CUENTA (20)
        7. CONCEPTO (30)
        8. (Assumed) DEBITO (?)
        9. (Assumed) CREDITO (?)
        """
        try:
            text = file_content.decode('utf-8', errors='ignore') # Latin-1 might be better for DOS? Trying utf-8/ignore first
        except:
            text = file_content.decode('latin-1', errors='ignore')
            
        lines = text.split('\n')
        entries = []
        
        # We assume data lines start with Date
        # Offsets (Cumulative from 0):
        # 0  - 10 : Fecha
        # 10 - 19 : Doc Ref (9 chars)
        # 19 - 29 : Cuenta (10 chars)
        # 29 - 41 : Nit (12 chars)
        # 41 - 68 : Nombre Bene (27 chars)
        # 68 - 88 : Nom Cuenta (20 chars)
        # 88 - 118: Concepto (30 chars)
        # 118...  : Amounts
        
        for line in lines:
            if not line.strip(): continue
            
            # Heuristic: Valid line starts with a Date dd/mm/yyyy
            # Check length: at least up to concept
            if len(line) < 80: 
                continue 
            
            chunk_date = line[0:10].strip()
            # Simple check if looks like date
            if len(chunk_date) < 8 or not (chunk_date[0].isdigit()):
                # Not a data line (header, separator, or total)
                continue
            
            try:
                # Dynamic "Anchor and Slice" Strategy
                # We extract a field of specific width, then skip any separator spaces to find the start of the next field.
                
                cursor = 0
                
                def get_chunk(line, start_cursor, width):
                    # Extract
                    chunk = line[start_cursor : start_cursor + width].strip()
                    # Move cursor to end of this block
                    new_cursor = start_cursor + width
                    # Skip spaces to find next anchor
                    while new_cursor < len(line) and line[new_cursor] == ' ':
                        new_cursor += 1
                    return chunk, new_cursor

                # 1. FECHA (10)
                s_fecha, cursor = get_chunk(line, cursor, 10)
                
                # 2. DOC (9)
                s_doc, cursor = get_chunk(line, cursor, 9)
                
                # 3. CUENTA (10)
                s_cuenta, cursor = get_chunk(line, cursor, 10)
                
                # 4. NIT (12)
                raw_nit, cursor = get_chunk(line, cursor, 12)
                s_nit = raw_nit.split(' ')[0] if raw_nit else ''
                
                # 5. NOM BENEFICIARIO (27)
                s_nombre, cursor = get_chunk(line, cursor, 27)
                
                # 6. NOM CUENTA (20)
                s_nom_cuenta, cursor = get_chunk(line, cursor, 20)
                
                # 7. CONCEPTO (30)
                s_concepto, cursor = get_chunk(line, cursor, 30)
                
                # 8. DEBITO & CREDITO
                # Remaining line content. Usually numbers.
                # We assume 2 columns of numbers at the end.
                # Since we skipped spaces, 'line[cursor:]' should start at the debit value (or close to it).
                rest = line[cursor:].strip()
                
                s_debito = "0"
                s_credito = "0"
                
                # Split by space? Values might be "960,000.00"
                # If there are multiple spaces between debit and credit
                parts = rest.split()
                if len(parts) >= 2:
                    s_debito = parts[0]
                    s_credito = parts[1]
                elif len(parts) == 1:
                    # Ambiguous. Usually one is zero.
                    # But which one? TODO: Refine if needed.
                    # In accounting txts, usually zeros are printed as "0.00" or empty?
                    # Screenshot: "                                  960,000.00" for Credit.
                    # Screenshot: "960,000.00                                  " for Debit?
                    # Actually, screenshot shows Debit column then Credit column.
                    # If Debit is empty/zero, it might look like blank space?
                    # Let's try to interpret the fixed width logic for values too if possible.
                    # Screenshot shows "VALOR DEBITO" "VALOR CREDITO" headers.
                    # Let's assume standard width ~20 for them?
                    pass
                
                # Re-try fixed width for values if split fails or is ambiguous?
                # Actually, split works if zeros are printed.
                # If zeros are SPACES, split returns only 1 value.
                # If screenshot shows "960,000.00" at the very end (Credit), and Debit is empty space?
                # We need to distinguish position.
                
                # Alternative: Use fixed width for values too, assuming ~20 chars.
                # Let's start scanning from cursor.
                # get_chunk(line, cursor, 20) -> Debit
                # get_chunk -> Credit
                
                # Let's try slicing rest.
                # If we assume 20 chars for each value roughly?
                # Let's try to read 20 chars for debit.
                # Adjust cursor back to 'rest' start logic? No, cursor is correct.
                # But 'get_chunk' skips spaces *after*. 
                # For values, preceding spaces matter if fixed width. 
                # BUT 'get_chunk' assumes we are AT the start of the field.
                # If Debit is "          0.00", and we are at start, we read it.
                # If Debit is "              " (empty), we read empty.
                
                # THE ISSUE: 'get_chunk' advances past separator.
                # If Debit is skipped (empty space separator merge?), we might read Credit as Debit?
                # No, because Loop 7 (Concept) consumed 30 chars.
                # Then 'get_chunk' consumed *variable* separator spaces.
                # So we are now at the *first non-space character* of the Values section?
                # NO! 
                # 'get_chunk' skips spaces *until* it finds a char? 
                # "while line[new_cursor] == ' ': new_cursor += 1"
                # This moves us to the START of the NEXT field data (if it exists).
                
                # CRITICAL FLAW in 'get_chunk' for empty columns:
                # If Debit is 0.00 printed as spaces "            ", 
                # and separator is spaces "  ",
                # The 'get_chunk' for Concept will skip ALL spaces until it hits the Credit value!
                # So we will read Credit value as Debit!
                
                # CORRECTION: We CANNOT skip spaces indefinitely blindly.
                # We must skip ONLY the separator width (e.g. 1 or 2 chars).
                # But we don't know the separator width.
                
                # BACKUP PLAN: Use pure offsets relative to Cursor, but assumes separator is included or handled.
                # Given user screenshot, headers have `*` separators.
                # This suggests separator might be fixed.
                # Let's guess separator is 2 spaces?
                
                # BETTER APPROACH: Use the Configured Widths strictly + Estimated Separator.
                # Config Widths: 10, 9, 10, 12, 27, 20, 30.
                # If we assume at least 1 space separator?
                # Let's try strict accumulation with lenient fallback?
                
                # Let's look at the "Anchor and Slice" logic again.
                # If use 'get_chunk' WITHOUT skipping spaces, we rely on padding inside the width.
                # Screenshot `110505` (6 chars) followed by spaces.
                # If width is 10, it effectively consumes the spaces.
                # So `line[cursor : cursor+10]` consumes `110505    `.
                # Cursor is now at separator?
                # Screenshot: `110505    ` (10 chars). Separator `  ` (2 chars).
                # `7553161     `.
                
                # So if we simply Add Separator (2 chars) to every step?
                # 10 + 2 = 12.
                # 9 + 2 = 11.
                # 10 + 2 = 12.
                # 12 + 2 = 14.
                # 27 + 2 = 29.
                # 20 + 2 = 22.
                # 30 + 2 = 32.
                
                # Let's try this: strict widths, and strip(). Then advance by Width + Separator.
                # Try Separator = 2 (looks like it in screenshot).
                
                sep = 2
                cur = 0
                
                s_fecha = line[cur : cur+10].strip(); cur += (10 + sep)
                s_doc = line[cur : cur+9].strip(); cur += (9 + sep)
                s_cuenta = line[cur : cur+10].strip(); cur += (10 + sep)
                s_nit = line[cur : cur+12].strip().split(' ')[0]; cur += (12 + sep)
                s_nombre = line[cur : cur+27].strip(); cur += (27 + sep)
                s_nom_cuenta = line[cur : cur+20].strip(); cur += (20 + sep)
                s_concepto = line[cur : cur+30].strip(); cur += (30 + sep)
                
                # Values:
                # Assume 20 width each?
                s_debito = line[cur : cur+20].strip(); cur += (20 + sep)
                s_credito = line[cur : cur+20].strip(); cur += (20 + sep)
                                
                def parse_amount(s):
                    if not s: return 0.0
                    try:
                         # Handle "1.000,00" vs "1,000.00"
                         # Screenshot shows "960,000.00" -> Comma group, dot decimal.
                        return float(s.replace(',', ''))
                    except: return 0.0
                    
                debito = parse_amount(s_debito)
                credito = parse_amount(s_credito)
                
                entries.append({
                    "fecha": s_fecha,
                    "doc_ref": s_doc,
                    "concepto": s_concepto,
                    "nit": s_nit,
                    "nombre_tercero": s_nombre,
                    "cuenta": s_cuenta,
                    "nombre_cuenta": s_nom_cuenta,
                    "debito": debito,
                    "credito": credito
                })

            except Exception as e:
                pass
                
        return entries

    # ... (Keep existing methods) ...

    @staticmethod
    def safe_int(value: str) -> Optional[int]:
        try:
            return int(value)
        except:
            return None


def import_legacy_data(
    db: Session,
    empresa_id: int,
    period_date: date, 
    default_tercero_id: int,
    file_coma: Optional[bytes] = None,
    file_coni: Optional[bytes] = None,
    file_cotr: Optional[bytes] = None,
    file_txt: Optional[bytes] = None
):
    results = {"accounts": 0, "third_parties": 0, "transactions": 0, "errors": []}
    
    # helper
    def get_clase(code):
        if not code or not code[0].isdigit(): return None
        return LegacyParsingService.safe_int(code[0])

    # 0. TXT IMPORT (AA99.TXT) - If present, this takes precedence or adds to it?
    # Let's treat it as a comprehensive source.
    if file_txt:
        entries = LegacyParsingService.parse_txt_report(file_txt)
        
        # We process entries for 3 things: Accounts, Third Parties, Transactions
        
        # A. Accounts & Third Parties (Collect unique set first)
        unique_accounts = {}
        unique_terceros = {}
        
        grouped_docs = {}
        
        for e in entries:
            # Accounts
            if e['cuenta'] and e['cuenta'] not in unique_accounts:
                unique_accounts[e['cuenta']] = e['nombre_cuenta']
                
            # Terceros
            if e['nit'] and e['nit'] not in unique_terceros:
                unique_terceros[e['nit']] = e['nombre_tercero']
                
            # Group Docs
            doc_key = (e['doc_ref'], e['fecha'])
            if doc_key not in grouped_docs:
                grouped_docs[doc_key] = []
            grouped_docs[doc_key].append(e)

        # B. Process Accounts with Auto-Hierarchy
        # Helper to get parent code
        def get_parent_code(c):
            if len(c) > 6: return c[:-2] # 8 -> 6
            if len(c) == 6: return c[:-2] # 6 -> 4
            if len(c) == 4: return c[:-2] # 4 -> 2
            if len(c) == 2: return c[0]   # 2 -> 1
            return None

        # Sorted by length to ensure parents create first (1, 11, 1105...)
        all_codes = sorted(unique_accounts.keys(), key=len)
        
        # We need to process not just the codes in file, but all their ancestors too.
        # Let's build a set of all needed codes.
        needed_codes = set()
        for code in all_codes:
            curr = code
            while curr:
                needed_codes.add(curr)
                curr = get_parent_code(curr)
        
        sorted_needed = sorted(list(needed_codes), key=len)
        
        # Dictionary to store IDs of created/found accounts for parenting
        code_to_id_map = {}
        
        for code in sorted_needed:
             # Check if exists
             existing = db.query(PlanCuenta).filter_by(empresa_id=empresa_id, codigo=code).first()
             
             parent_code = get_parent_code(code)
             parent_id = code_to_id_map.get(parent_code) if parent_code else None
             
             # If parent missing in map (maybe pre-existed in DB?), try fetch
             if parent_code and not parent_id:
                 p_obj = db.query(PlanCuenta).filter_by(empresa_id=empresa_id, codigo=parent_code).first()
                 if p_obj: parent_id = p_obj.id

             if not existing:
                 try:
                     # Determine name: Use file name if exact match, else "GENERADA {code}"
                     # If the code is in our original unique_accounts, use that name.
                     # Else generic.
                     acc_name = unique_accounts.get(code, f"CUENTA GENERADA {code}")
                     
                     # Determine Class
                     clase_id = get_clase(code)
                     
                     # Determine Map Level based on PUC standards
                     # 1 digit = Level 1 (Clase)
                     # 2 digits = Level 2 (Grupo)
                     # 4 digits = Level 3 (Cuenta)
                     # 6 digits = Level 4 (Subcuenta)
                     # 8+ digits = Level 5 (Auxiliar)
                     def get_puc_level(c):
                         l = len(c)
                         if l == 1: return 1
                         if l == 2: return 2
                         if l == 4: return 3
                         if l == 6: return 4
                         if l >= 8: return 5
                         return l

                     calculated_level = get_puc_level(code)
                     
                     new_acc = PlanCuenta(
                         empresa_id=empresa_id,
                         codigo=code,
                         nombre=acc_name,
                         nivel=calculated_level,
                         permite_movimiento=(len(code) >= 6), # Assumption: Auxiliaries allow movement
                         clase=clase_id,
                         cuenta_padre_id=parent_id
                     )
                     db.add(new_acc)
                     db.flush()
                     code_to_id_map[code] = new_acc.id
                     results["accounts"] += 1
                 except Exception as e: 
                     db.rollback() 
                     results["errors"].append(f"Account {code} creation error: {str(e)}")
                     # Try to recover ID if it failed because it existed (race condition)
                     existing_retry = db.query(PlanCuenta).filter_by(empresa_id=empresa_id, codigo=code).first()
                     if existing_retry:
                         code_to_id_map[code] = existing_retry.id
                     continue
             else:
                 code_to_id_map[code] = existing.id
                 
                 # Recalculate level to fix previous bad imports
                 # Re-define helper or move it up scope? It's inside loop same scope.
                 # Python scope rules allow access if defined before in same function.
                 # Wait, 'get_puc_level' was defined inside 'if not existing'. 
                 # I need to move 'get_puc_level' OUTSIDE the if/else block to reuse it.
                 
                 # But since I cannot easily move code lines without large replace, 
                 # I will just redefine logic or rely on the fact I should move it.
                 
                 # I'll use simple check for now.
                 expected_level = len(code)
                 if len(code) == 4: expected_level = 3
                 if len(code) == 6: expected_level = 4
                 if len(code) >= 8: expected_level = 5
                 
                 updates_needed = False
                 if existing.nivel != expected_level:
                     existing.nivel = expected_level
                     updates_needed = True
                     
                 if parent_id and existing.cuenta_padre_id != parent_id:
                     existing.cuenta_padre_id = parent_id
                     updates_needed = True
                     
                 if updates_needed:
                      try:
                          db.add(existing)
                          db.flush()
                      except:
                          db.rollback()
                          db.rollback()

        try:
            db.commit() 
        except Exception as e:
            db.rollback()
        
        # C. Process Third Parties
        for nit, name in unique_terceros.items():
            existing = db.query(Tercero).filter_by(empresa_id=empresa_id, nit=nit).first()
            if not existing:
                try:
                    new_tp = Tercero(
                        empresa_id=empresa_id,
                        nit=nit,
                        razon_social=name,
                        es_cliente=True,
                        es_proveedor=True
                    )
                    db.add(new_tp)
                    db.flush()
                    results["third_parties"] += 1
                except Exception as e:
                    db.rollback() 
                    continue
        
        try:
            db.commit() # Commit TPs
        except Exception as e:
            print(f"Error committing third parties: {e}")
            db.rollback()

        # D. Process Documents
        # Cache for created/found types
        tipo_doc_cache = {} 
        
        for (ref, fecha_str), lines in grouped_docs.items():
            try:
                # Parse date DD/MM/YYYY
                try:
                    d, m, y = map(int, fecha_str.split('/'))
                    doc_date = date(y, m, d)
                except:
                    doc_date = period_date

                # Extract Document Type and Number from ref (e.g. "CB-000001")
                # Split by '-'
                parts = ref.split('-')
                if len(parts) >= 2:
                    type_code = parts[0].strip()[0:5] # Limit length
                    num_str = parts[1]
                else:
                    # Fallback
                    clean = ''.join(filter(str.isalpha, ref))
                    type_code = clean if clean else "LEG"
                    num_str = ref
                
                if not type_code: type_code = "LEG"
                
                # Mapping of Legacy Codes (Standard + Screenshot inferred)
                DOC_TYPE_MAP = {
                    "RC": "RECIBO DE CAJA",
                    "CE": "COMPROBANTE DE EGRESO",
                    "CI": "COMPROBANTE DE INGRESO",
                    "CB": "COMPROBANTE BANCARIO",
                    "CC": "COMPROBANTE DE CONTABILIDAD",
                    "CM": "COMPROBANTE DE DIARIO", # or CAJA MENOR, assuming Diario/Manual
                    "FC": "FACTURA DE COMPRA",
                    "FV": "FACTURA DE VENTA",
                    "NC": "NOTA CREDITO",
                    "ND": "NOTA DEBITO",
                    "RB": "RETIROS BANCARIOS",
                    "CO": "CONSIGNACION"
                }
                
                doc_name_candidate = DOC_TYPE_MAP.get(type_code, f"DOCUMENTO {type_code}")
                
                if type_code not in tipo_doc_cache:
                    # Find or create
                    td = db.query(TipoDocumento).filter_by(empresa_id=empresa_id, codigo=type_code).first()
                    
                    if td:
                        # Update name if it is the generic "Tipo Importado..." one to the better one
                        if td.nombre.startswith("Tipo Importado"):
                             try:
                                 td.nombre = doc_name_candidate
                                 db.add(td)
                                 db.commit()
                             except:
                                 db.rollback()
                    else:
                         try:
                             td = TipoDocumento(
                                 empresa_id=empresa_id,
                                 codigo=type_code,
                                 nombre=doc_name_candidate,
                                 consecutivo_actual=1
                             )
                             db.add(td)
                             db.commit()
                             db.refresh(td)
                         except:
                             db.rollback()
                             td = db.query(TipoDocumento).filter_by(empresa_id=empresa_id, codigo=type_code).first()
                    
                    if td:
                        tipo_doc_cache[type_code] = td.id
                    
                    if td:
                        tipo_doc_cache[type_code] = td.id
                
                target_tipo_id = tipo_doc_cache.get(type_code)

                # We need a beneficiary for the header
                first_nit = lines[0]['nit']
                tercero_obj = db.query(Tercero).filter_by(empresa_id=empresa_id, nit=first_nit).first()
                # Use line's third party primarily. Fallback to default if line TP missing.
                tercero_id = tercero_obj.id if tercero_obj else default_tercero_id
                
                # If both are missing, we cannot create a document safely without violating FK usually.
                # However, we will try to proceed if we have at least one ID.
                if not tercero_id and default_tercero_id:
                     tercero_id = default_tercero_id
                     
                # If still no third party, we skip or use a system default "Cuantías Menores" if implemented.
                # For now, if no ID, skip.
                if not tercero_id:
                    results["errors"].append(f"Doc {ref} skipped: No valid Third Party found and no default provided.")
                    continue
                
                # Extract numbers
                doc_num = 0
                try:
                     clean_num = ''.join(filter(str.isdigit, num_str))
                     doc_num = int(clean_num) if clean_num else 0
                except: pass
                
                if not target_tipo_id:
                     # Log error or skip? Skipping.
                     continue
                
                new_doc = Documento(
                    empresa_id=empresa_id,
                    beneficiario_id=tercero_id,
                    tipo_documento_id=target_tipo_id,
                    numero=doc_num if doc_num > 0 else 999999,
                    fecha=doc_date,
                    observaciones=f"Ref: {ref} - {lines[0]['concepto']}",
                    estado="ACTIVO"
                )
                db.add(new_doc)
                db.flush()
                
                for line in lines:
                    acc_obj = db.query(PlanCuenta).filter_by(empresa_id=empresa_id, codigo=line['cuenta']).first()
                    if acc_obj:
                         mov = MovimientoContable(
                            documento_id=new_doc.id,
                            cuenta_id=acc_obj.id,
                            debito=line['debito'],
                            credito=line['credito'],
                            concepto=line['concepto']
                         )
                         db.add(mov)
                
                db.commit()
                results["transactions"] += 1
                
            except Exception as e:
                # print(f"Error processing doc {ref}: {e}")
                db.rollback()
        
        return results

    # 1. Import Accounts (COMA) - OLD LOGIC FALLBACK
    if file_coma:
        accounts = LegacyParsingService.parse_coma_accounts(file_coma)

        for acc in accounts:
            try:
                existing = db.query(PlanCuenta).filter_by(empresa_id=empresa_id, codigo=acc["codigo"]).first()
                if not existing:
                    lvl = len(acc["codigo"])
                    can_move = lvl > 4 
                    
                    new_acc = PlanCuenta(
                        empresa_id=empresa_id,
                        codigo=acc["codigo"],
                        nombre=acc["nombre"],
                        nivel=lvl,
                        permite_movimiento=can_move,
                        clase=get_clase(acc["codigo"])
                    )
                    db.add(new_acc)
                    results["accounts"] += 1
            except Exception as e:
                print(f"Error importing account {acc.get('codigo')}: {e}")
                continue
        db.commit()
        
    # 2. Import Third Parties (CONI)
    if file_coni:
        tps = LegacyParsingService.parse_coni_third_parties(file_coni)
        for tp in tps:
            existing = db.query(Tercero).filter_by(empresa_id=empresa_id, nit=tp["nit"]).first()
            if not existing:
                new_tp = Tercero(
                    empresa_id=empresa_id,
                    nit=tp["nit"],
                    razon_social=tp["razon_social"],
                    es_cliente=True,
                    es_proveedor=True
                )
                db.add(new_tp)
                results["third_parties"] += 1
        db.commit()
    
    # 3. Import Transactions (COTR)
    if file_cotr:
        # Prepare valid Document Type FIRST
        target_tipo_doc_id = None
        
        # 1. Try finding generic "Comprobante Diario" or similar
        tp = db.query(TipoDocumento).filter(
            TipoDocumento.empresa_id == empresa_id,
            (TipoDocumento.nombre.ilike('%diario%')) | (TipoDocumento.codigo.ilike('%CD%'))
        ).first()
        
        if tp:
            target_tipo_doc_id = tp.id
        else:
            # 2. Or just take the first available
            tp = db.query(TipoDocumento).filter_by(empresa_id=empresa_id).first()
            if tp: 
                 target_tipo_doc_id = tp.id
            else:
                 # 3. Create one if absolutely nothing exists
                 new_tp = TipoDocumento(
                     empresa_id=empresa_id,
                     codigo="CD-L",
                     nombre="Comprobante Diario Importado",
                     consecutivo_actual=1
                 )
                 db.add(new_tp)
                 db.flush()
                 target_tipo_doc_id = new_tp.id

        txs = LegacyParsingService.parse_cotr_transactions(file_cotr)
        
        from collections import defaultdict
        grouped = defaultdict(list)
        for tx in txs:
            grouped[tx["doc_ref"]].append(tx)
            
        for doc_ref, entries in grouped.items():
            
            new_doc = Documento(
                empresa_id=empresa_id,
                beneficiario_id=default_tercero_id, 
                tipo_documento_id=target_tipo_doc_id, # Safely determined above
                numero=999999,
                fecha=period_date,
                observaciones=f"Importado Legacy Ref: {doc_ref}",
                estado="APROBADO"
            )
            
            db.add(new_doc)
            db.flush()
            
            for index, entry in enumerate(entries):
                # Find Account ID
                acc_obj = db.query(PlanCuenta).filter_by(empresa_id=empresa_id, codigo=entry["cuenta"]).first()
                if acc_obj:
                    mov = MovimientoContable(
                        documento_id=new_doc.id,
                        cuenta_id=acc_obj.id,
                        # tercero_id is not in MovimientoContable, only in Documento
                        debito=entry["debito"],
                        credito=entry["credito"],
                        concepto=f"Mov Ref {doc_ref}" # Changed descripcion to concepto
                    )
                    db.add(mov)
            
            results["transactions"] += 1
            
        db.commit()
        
    return results
