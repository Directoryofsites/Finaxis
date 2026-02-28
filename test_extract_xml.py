import imaplib
import email
import os
import zipfile
import tempfile
from email.header import decode_header
import xml.etree.ElementTree as ET

# Credenciales proporcionadas por el usuario
EMAIL = "iglesiaibgv5@gmail.com"
PASS = "dscqziesjsrhoxiy"

def decode_str(s):
    if not isinstance(s, str):
        decoded_bytes, charset = decode_header(s)[0]
        if charset:
            try:
                return decoded_bytes.decode(charset)
            except:
                return decoded_bytes.decode('utf-8', errors='ignore')
        else:
            if isinstance(decoded_bytes, bytes):
                return decoded_bytes.decode('utf-8', errors='ignore')
            return decoded_bytes
    return s

def process_xml_invoice(xml_path):
    """
    Intenta extraer datos básicos de una factura UBL 2.1 (DIAN).
    """
    print(f"\n--- Procesando XML: {os.path.basename(xml_path)} ---")
    try:
        # Los XML de la DIAN usan Namespaces muy pesados. 
        # Para un prototipo rápido, leemos como texto y buscamos tags básicos.
        # En producción usaremos xmltodict o manejaremos los namespaces de ElementTree.
        
        with open(xml_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Extracción súper básica por Regex/String find para el prototipo
        import re
        
        # Buscar CUFE
        cufe_match = re.search(r'<cbc:UUID[^>]*>(.*?)</cbc:UUID>', content)
        cufe = cufe_match.group(1) if cufe_match else "No encontrado"
        
        # Buscar Total
        total_match = re.search(r'<cbc:PayableAmount[^>]*>(.*?)</cbc:PayableAmount>', content)
        total = total_match.group(1) if total_match else "No encontrado"
        
        # Buscar Nombre Emisor (Proveedor) - Esto es variable según la estructura exacta, pero suele estar en AccountingSupplierParty
        emisor_match = re.search(r'<cac:PartyName>\s*<cbc:Name>(.*?)</cbc:Name>', content)
        if not emisor_match:
             emisor_match = re.search(r'<cac:RegistrationName>(.*?)</cac:RegistrationName>', content) # A veces está aquí
        emisor = emisor_match.group(1) if emisor_match else "No encontrado"
        
        print(f"[OK] Proveedor: {emisor}")
        print(f"[OK] Total: ${total}")
        print(f"[OK] CUFE: {cufe[:30]}...")
        return True
        
    except Exception as e:
        print(f"[ERROR] procesando {xml_path}: {e}")
        return False

def test_fetch_xml():
    print(f"Conectando a {EMAIL}...")
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    try:
        mail.login(EMAIL, PASS)
        mail.select("inbox")
        
        # Buscar correos recientes (últimos 10, por ejemplo)
        # O buscar todos. Aquí buscamos correos que tengan adjuntos.
        print("Buscando correos con posibles facturas (últimos 5)...")
        status, messages = mail.search(None, "ALL")
        
        if status == "OK" and messages[0]:
            mail_ids = messages[0].split()[-5:] # Tomar los últimos 5
            
            # Crear carpeta temporal para guardar los XML/ZIP
            with tempfile.TemporaryDirectory() as temp_dir:
                xmls_found = 0
                
                for mail_id in reversed(mail_ids): # Del más nuevo al más viejo
                    status, msg_data = mail.fetch(mail_id, "(RFC822)")
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            subject = decode_str(msg.get("Subject"))
                            safe_subject = subject.encode('ascii', 'ignore').decode('ascii') # Evitar charmap error
                            print(f"\nRevisando correo: {safe_subject}")
                            
                            # Buscar adjuntos
                            for part in msg.walk():
                                if part.get_content_maintype() == 'multipart':
                                    continue
                                if part.get('Content-Disposition') is None:
                                    continue
                                    
                                filename = part.get_filename()
                                if filename:
                                    filename = decode_str(filename)
                                    filename = filename.lower()
                                    
                                    if filename.endswith('.xml') or filename.endswith('.zip'):
                                        print(f"[ADJUNTO] Encontrado: {filename}")
                                        filepath = os.path.join(temp_dir, filename)
                                        
                                        with open(filepath, 'wb') as f:
                                            f.write(part.get_payload(decode=True))
                                            
                                        # Si es ZIP, extraer a ver si hay XML dentro
                                        if filename.endswith('.zip'):
                                            try:
                                                with zipfile.ZipFile(filepath, 'r') as zip_ref:
                                                    for zinfo in zip_ref.infolist():
                                                        if zinfo.filename.lower().endswith('.xml'):
                                                            extracted_path = zip_ref.extract(zinfo, temp_dir)
                                                            print(f"   [EXTRAIDO] de ZIP: {zinfo.filename}")
                                                            process_xml_invoice(extracted_path)
                                                            xmls_found += 1
                                            except zipfile.BadZipFile:
                                                print("   [ERROR] Archivo ZIP corrupto.")
                                                
                                        elif filename.endswith('.xml'):
                                            process_xml_invoice(filepath)
                                            xmls_found += 1
                                            
                if xmls_found == 0:
                    print("\n[INFO] No se encontraron archivos XML ni ZIP adjuntos en los ultimos correos.")
                    print("Por favor, reenvia una factura electronica de prueba (con su archivo .zip o .xml) a este correo para probar.")
                    
    except Exception as e:
         print(f"Error general: {e}")
         import traceback
         traceback.print_exc()
    finally:
         try: mail.logout()
         except: pass

if __name__ == "__main__":
    test_fetch_xml()
