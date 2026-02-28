import imaplib
import email
import os
import zipfile
import tempfile
import re
from datetime import datetime
from email.header import decode_header
from sqlalchemy.orm import Session
from fastapi import HTTPException

from ..models.tercero import Tercero
from ..models.tipo_documento import TipoDocumento
from ..schemas.documento import DocumentoCreate, MovimientoContableCreate
from ..services.documento import create_documento

def decode_str(s):
    if not isinstance(s, str):
        decoded_bytes, charset = decode_header(s)[0]
        if charset:
            try: return decoded_bytes.decode(charset)
            except: return decoded_bytes.decode('utf-8', errors='ignore')
        else:
            if isinstance(decoded_bytes, bytes):
                return decoded_bytes.decode('utf-8', errors='ignore')
            return decoded_bytes
    return s

def extract_dian_data(xml_path):
    """Extrae datos clave de un XML UBL 2.1 de la DIAN."""
    try:
        with open(xml_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Parseo Básico (Regex para prototipo rápido)
        cufe_match = re.search(r'<cbc:UUID[^>]*>(.*?)</cbc:UUID>', content)
        cufe = cufe_match.group(1) if cufe_match else None
        
        total_match = re.search(r'<cbc:PayableAmount[^>]*>(.*?)</cbc:PayableAmount>', content)
        total = float(total_match.group(1)) if total_match else 0.0
        
        # Emisor / Proveedor (Enfocado en el Supplier Party para no extraer a Cadena u otros)
        emisor_name = "PROVEEDOR DESCONOCIDO"
        nit = "000000000"
        
        supplier_match = re.search(r'<cac:AccountingSupplierParty>(.*?)</cac:AccountingSupplierParty>', content, re.DOTALL)
        if supplier_match:
            supplier_xml = supplier_match.group(1)
            # Razón Social (La oficial es RegistrationName, pero probamos Name si no está)
            emisor_name_match = re.search(r'<cac:RegistrationName>\s*<cbc:Name>(.*?)</cbc:Name>\s*</cac:RegistrationName>', supplier_xml)
            if not emisor_name_match:
                emisor_name_match = re.search(r'<cac:RegistrationName>(.*?)</cac:RegistrationName>', supplier_xml)
            if not emisor_name_match:
                emisor_name_match = re.search(r'<cbc:Name>(.*?)</cbc:Name>', supplier_xml)
            
            if emisor_name_match:
                emisor_name = emisor_name_match.group(1).strip()
            
            # NIT (UBL 2.1 estándar de la DIAN guarda el NIT en cac:CompanyID o cbc:CompanyID)
            nit_match = re.search(r'<cbc:CompanyID[^>]*>(.*?)</cbc:CompanyID>', supplier_xml)
            if not nit_match:
                nit_match = re.search(r'<cac:CompanyID[^>]*>(.*?)</cac:CompanyID>', supplier_xml)
            if not nit_match:
                nit_match = re.search(r'<cbc:ID[^>]*schemeID="31"[^>]*>(.*?)</cbc:ID>', supplier_xml)
            if not nit_match:
                nit_match = re.search(r'<cbc:ID[^>]*>(.*?)</cbc:ID>', supplier_xml)

            if nit_match:
                nit = nit_match.group(1).strip()
        
        # Número de Factura
        num_match = re.search(r'<cbc:ID>(.*?)</cbc:ID>', content)
        # El primer cbc:ID suele ser el número de factura en UBL
        numero_factura = num_match.group(1) if num_match else "0"
        # Limpiar prefijos si los hay (ej: FE123 -> 123)
        numero_clean = re.sub(r'\D', '', numero_factura)
        numero_int = int(numero_clean) if numero_clean else 0

        # Fecha de Emision
        fecha_match = re.search(r'<cbc:IssueDate>(.*?)</cbc:IssueDate>', content)
        fecha_emision = fecha_match.group(1) if fecha_match else None

        if not cufe or total == 0:
            return None # XML inválido o no es factura
            
        return {
            "nit": nit,
            "razon_social": emisor_name,
            "total": total,
            "cufe": cufe,
            "numero": numero_int,
            "fecha": fecha_emision
        }
    except Exception as e:
        print(f"Error procesando XML {xml_path}: {e}")
        return None

def find_or_create_proveedor(db: Session, empresa_id: int, nit: str, razon_social: str, user_id: int):
    tercero = db.query(Tercero).filter(Tercero.empresa_id == empresa_id, Tercero.nit == nit).first()
    if not tercero:
        tercero = Tercero(
            empresa_id=empresa_id,
            nit=nit,
            razon_social=razon_social,
            es_proveedor=True,
            created_by=user_id
        )
        db.add(tercero)
        db.commit()
        db.refresh(tercero)
    return tercero

def procesar_buzon(
    db: Session, 
    empresa_id: int, 
    user_id: int, 
    email_addr: str, 
    password: str, 
    tipo_documento_id: int, 
    cuenta_gasto_id: int, 
    cuenta_caja_id: int
):
    """
    Se conecta al correo, extrae facturas XML y las contabiliza.
    """
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    facturas_procesadas = []
    
    try:
        # Se remueven espacios normales y "No-Breaking Spaces" (\xa0) comunes al copiar de html
        clean_password = ''.join(password.split())
        mail.login(email_addr, clean_password)
        mail.select("inbox")
        
        status, messages = mail.search(None, "UNSEEN") # Leer solo "no leídos"
        if status != "OK" or not messages[0]:
            return {"status": "ok", "procesadas": 0, "total_correos": 0, "detalle": []}
            
        # Revisar en ráfagas de hasta 50 correos no leídos por cada clic
        mail_ids = messages[0].split()[-50:]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            for mail_id in reversed(mail_ids):
                status, msg_data = mail.fetch(mail_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        for part in msg.walk():
                            if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
                                continue
                                
                            filename = part.get_filename()
                            if filename:
                                filename = decode_str(filename).lower()
                                filepath = os.path.join(temp_dir, filename)
                                
                                if filename.endswith('.xml') or filename.endswith('.zip'):
                                    with open(filepath, 'wb') as f:
                                        f.write(part.get_payload(decode=True))
                                        
                                    xml_to_process = None
                                    
                                    if filename.endswith('.zip'):
                                        try:
                                            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                                                for zinfo in zip_ref.infolist():
                                                    if zinfo.filename.lower().endswith('.xml'):
                                                        xml_to_process = zip_ref.extract(zinfo, temp_dir)
                                                        break
                                        except zipfile.BadZipFile:
                                            continue
                                    else:
                                        xml_to_process = filepath
                                        
                                    if xml_to_process:
                                        data = extract_dian_data(xml_to_process)
                                        if data: # Es una factura válida DIAN
                                            # Validar si este CUFE ya existe para no duplicar
                                            from ..models.documento import Documento
                                            existe = db.query(Documento).filter(
                                                Documento.empresa_id == empresa_id,
                                                Documento.dian_cufe == data['cufe']
                                            ).first()
                                            
                                            if not existe:
                                                # 1. Asegurar Proveedor
                                                proveedor = find_or_create_proveedor(
                                                    db, empresa_id, data['nit'], data['razon_social'], user_id
                                                )
                                                
                                                # 2. DEFINIR CUENTA GASTO (PRIORIDAD TERCERO)
                                                # Si el proveedor tiene una cuenta por defecto, la usamos. 
                                                # Si no, usamos la cuenta global que envía el frontend.
                                                cuenta_gasto_final = proveedor.cuenta_gasto_defecto_id if proveedor.cuenta_gasto_defecto_id else cuenta_gasto_id
                                                
                                                # 3. Crear Movimientos (Gasto al Débito, Caja al Crédito)
                                                movimientos = [
                                                    MovimientoContableCreate(
                                                        cuenta_id=cuenta_gasto_final,
                                                        debito=data['total'],
                                                        credito=0,
                                                        concepto=f"Compra escaneada: {data['razon_social']}"
                                                    ),
                                                    MovimientoContableCreate(
                                                        cuenta_id=cuenta_caja_id,
                                                        debito=0,
                                                        credito=data['total'],
                                                        concepto=f"Pago automático compra {data['razon_social']}"
                                                    )
                                                ]
                                                
                                                # Intentar usar la fecha del XML en lugar de hoy
                                                try:
                                                    fecha_doc = datetime.strptime(data['fecha'], '%Y-%m-%d').date() if data.get('fecha') else datetime.now().date()
                                                except (ValueError, TypeError):
                                                    fecha_doc = datetime.now().date()

                                                # 3. Crear Documento Borrador (estado 'ACTIVO' o 'BORRADOR')
                                                doc_create = DocumentoCreate(
                                                    tipo_documento_id=tipo_documento_id,
                                                    numero=data['numero'],
                                                    empresa_id=empresa_id,
                                                    beneficiario_id=proveedor.id,
                                                    fecha=fecha_doc,
                                                    movimientos=movimientos
                                                )
                                                
                                                nuevo_doc = create_documento(db, doc_create, user_id, commit=True)
                                                
                                                # Guardar el CUFE para evitar duplicados en el futuro
                                                nuevo_doc.dian_cufe = data['cufe']
                                                nuevo_doc.observaciones = "Importado automáticamente vía Buzón Tributario DIAN."
                                                db.commit()
                                                
                                                facturas_procesadas.append({
                                                    "numero": data['numero'],
                                                    "nit": data['nit'],
                                                    "proveedor": data['razon_social'],
                                                    "total": data['total'],
                                                    "documento_id": nuevo_doc.id
                                                })
                                            
    except Exception as e:
        print(f"Error procesando buzón: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try: mail.logout()
        except: pass
        
    return {
        "status": "ok",
        "procesadas": len(facturas_procesadas),
        "total_correos": len(mail_ids) if 'mail_ids' in locals() else 0,
        "detalle": facturas_procesadas
    }
