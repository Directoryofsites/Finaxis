import imaplib
import email
import os
import zipfile
import tempfile
import re
from datetime import datetime
from email.header import decode_header
from typing import Any
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
        
        # Tipo de Factura (01=Factura, 05=Doc Soporte, 91=Nota Credito, 92=Nota Debito)
        type_code_match = re.search(r'<cbc:InvoiceTypeCode[^>]*>(.*?)</cbc:InvoiceTypeCode>', content)
        invoice_type_code = type_code_match.group(1).strip() if type_code_match else "01"

        # Emisor / Vendedor (AccountingSupplierParty)
        emisor_name = "DESCONOCIDO"
        nit_emisor = "000000000"
        
        supplier_match = re.search(r'<cac:AccountingSupplierParty>(.*?)</cac:AccountingSupplierParty>', content, re.DOTALL)
        if supplier_match:
            supplier_xml = supplier_match.group(1)
            emisor_name_match = re.search(r'<cac:RegistrationName>\s*<cbc:Name>(.*?)</cbc:Name>\s*</cac:RegistrationName>', supplier_xml)
            if not emisor_name_match:
                emisor_name_match = re.search(r'<cbc:Name>(.*?)</cbc:Name>', supplier_xml)
            if emisor_name_match:
                emisor_name = emisor_name_match.group(1).strip()
            
            nit_match = re.search(r'<cbc:CompanyID[^>]*>(.*?)</cbc:CompanyID>', supplier_xml)
            if nit_match:
                nit_emisor = nit_match.group(1).strip()
        
        # Receptor / Comprador (AccountingCustomerParty)
        receptor_name = "DESCONOCIDO"
        nit_receptor = "000000000"
        
        customer_match = re.search(r'<cac:AccountingCustomerParty>(.*?)</cac:AccountingCustomerParty>', content, re.DOTALL)
        if customer_match:
            customer_xml = customer_match.group(1)
            receptor_name_match = re.search(r'<cac:RegistrationName>\s*<cbc:Name>(.*?)</cbc:Name>\s*</cac:RegistrationName>', customer_xml)
            if not receptor_name_match:
                receptor_name_match = re.search(r'<cbc:Name>(.*?)</cbc:Name>', customer_xml)
            if receptor_name_match:
                receptor_name = receptor_name_match.group(1).strip()
            
            nit_rec_match = re.search(r'<cbc:CompanyID[^>]*>(.*?)</cbc:CompanyID>', customer_xml)
            if nit_rec_match:
                nit_receptor = nit_rec_match.group(1).strip()

        # Número de Factura
        num_match = re.search(r'<cbc:ID>(.*?)</cbc:ID>', content)
        numero_factura = num_match.group(1) if num_match else "0"
        numero_clean = re.sub(r'\D', '', numero_factura)
        numero_int = int(numero_clean) if numero_clean else 0

        # Fecha de Emision
        fecha_match = re.search(r'<cbc:IssueDate>(.*?)</cbc:IssueDate>', content)
        fecha_emision = fecha_match.group(1) if fecha_match else None

        if not cufe or total == 0:
            return None # XML inválido o no es factura
            
        return {
            "nit": nit_emisor,
            "razon_social": emisor_name,
            "nit_receptor": nit_receptor,
            "razon_social_receptor": receptor_name,
            "total": total,
            "cufe": cufe,
            "numero": numero_int,
            "fecha": fecha_emision,
            "invoice_type_code": invoice_type_code
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
    config: Any
):
    """
    Se conecta al correo, extrae XML y los contabiliza (Compra, Venta o Soporte).
    """
    from ..models.empresa import Empresa
    from ..models.documento import Documento

    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    nit_empresa = empresa.nit if empresa else ""
    # Limpiar NIT de la empresa (solo números)
    nit_empresa_clean = re.sub(r'\D', '', nit_empresa)

    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    facturas_procesadas = []
    
    try:
        clean_email = ''.join(email_addr.split())
        clean_password = ''.join(password.split())
        mail.login(clean_email, clean_password)
        mail.select("inbox")
        
        status, messages = mail.search(None, "UNSEEN")
        if status != "OK" or not messages[0]:
            return {"status": "ok", "procesadas": 0, "total_correos": 0, "detalle": []}
            
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
                                        if data:
                                            # Validar si este CUFE ya existe
                                            existe = db.query(Documento).filter(
                                                Documento.empresa_id == empresa_id,
                                                Documento.dian_cufe == data['cufe']
                                            ).first()
                                            
                                            if not existe:
                                                # --- LÓGICA DE CLASIFICACIÓN ---
                                                nit_xml_emisor = re.sub(r'\D', '', str(data['nit']))
                                                nit_xml_receptor = re.sub(r'\D', '', str(data['nit_receptor']))
                                                
                                                categoria = "COMPRA" # Default
                                                if nit_xml_emisor == nit_empresa_clean:
                                                    if data['invoice_type_code'] == '05':
                                                        categoria = "SOPORTE"
                                                    else:
                                                        categoria = "VENTA"
                                                elif nit_xml_receptor == nit_empresa_clean:
                                                    categoria = "COMPRA"
                                                else:
                                                    categoria = "COMPRA"

                                                # Selección de parámetros según categoría
                                                tipo_doc_id = None
                                                cta_principal_id = None 
                                                cta_caja_id = None
                                                label_concepto = ""

                                                if categoria == "COMPRA":
                                                    tipo_doc_id = config.tipo_documento_id
                                                    cta_principal_id = config.cuenta_gasto_id
                                                    cta_caja_id = config.cuenta_caja_id
                                                    label_concepto = f"Compra: {data['razon_social']}"
                                                elif categoria == "VENTA":
                                                    tipo_doc_id = config.venta_tipo_documento_id
                                                    cta_principal_id = config.venta_cuenta_ingreso_id
                                                    cta_caja_id = config.venta_cuenta_caja_id
                                                    label_concepto = f"Venta: {data['razon_social_receptor']}"
                                                elif categoria == "SOPORTE":
                                                    tipo_doc_id = config.soporte_tipo_documento_id
                                                    cta_principal_id = config.soporte_cuenta_gasto_id
                                                    cta_caja_id = config.soporte_cuenta_caja_id
                                                    label_concepto = f"Doc. Soporte: {data['razon_social']}"

                                                if not tipo_doc_id or not cta_principal_id or not cta_caja_id:
                                                    continue

                                                # --- CREACIÓN DEL DOCUMENTO ---
                                                otro_nit = data['nit'] if categoria != "VENTA" else data['nit_receptor']
                                                otra_razon = data['razon_social'] if categoria != "VENTA" else data['razon_social_receptor']
                                                
                                                tercero = find_or_create_proveedor(
                                                    db, empresa_id, otro_nit, otra_razon, user_id
                                                )
                                                
                                                if categoria == "VENTA":
                                                    movimientos = [
                                                        MovimientoContableCreate(
                                                            cuenta_id=cta_caja_id,
                                                            debito=data['total'], credito=0,
                                                            concepto=label_concepto
                                                        ),
                                                        MovimientoContableCreate(
                                                            cuenta_id=cta_principal_id,
                                                            debito=0, credito=data['total'],
                                                            concepto=label_concepto
                                                        )
                                                    ]
                                                else:
                                                    final_cta_gasto = tercero.cuenta_gasto_defecto_id if tercero.cuenta_gasto_defecto_id else cta_principal_id
                                                    movimientos = [
                                                        MovimientoContableCreate(
                                                            cuenta_id=final_cta_gasto,
                                                            debito=data['total'], credito=0,
                                                            concepto=label_concepto
                                                        ),
                                                        MovimientoContableCreate(
                                                            cuenta_id=cta_caja_id,
                                                            debito=0, credito=data['total'],
                                                            concepto=label_concepto
                                                        )
                                                    ]
                                                
                                                try:
                                                    fecha_doc = datetime.strptime(data['fecha'], '%Y-%m-%d').date() if data.get('fecha') else datetime.now().date()
                                                except:
                                                    fecha_doc = datetime.now().date()

                                                doc_create = DocumentoCreate(
                                                    tipo_documento_id=tipo_doc_id,
                                                    numero=data['numero'],
                                                    empresa_id=empresa_id,
                                                    beneficiario_id=tercero.id,
                                                    fecha=fecha_doc,
                                                    movimientos=movimientos
                                                )
                                                
                                                nuevo_doc = create_documento(db, doc_create, user_id, commit=True)
                                                nuevo_doc.dian_cufe = data['cufe']
                                                nuevo_doc.observaciones = f"Importado vía Buzón ({categoria})."
                                                db.commit()
                                                
                                                facturas_procesadas.append({
                                                    "numero": data['numero'],
                                                    "nit": otro_nit,
                                                    "proveedor": otra_razon,
                                                    "total": data['total'],
                                                    "tipo": categoria,
                                                    "documento_id": nuevo_doc.id
                                                })
                                            
    except Exception as e:
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
