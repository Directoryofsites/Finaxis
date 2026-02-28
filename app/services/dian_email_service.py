import imaplib
import email
import re
import time
from email.header import decode_header
from typing import Optional, Tuple

class DianEmailService:
    """
    Servicio para automatizar la captura del token de acceso de la DIAN
    desde el correo electrónico del contribuyente.
    """
    
    def __init__(self, imap_server: str, email_user: str, email_password: str):
        self.imap_server = imap_server
        self.email_user = email_user
        self.email_password = email_password
        self.mail = None

    def connect(self):
        """Establece conexión con el servidor IMAP"""
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_server)
            self.mail.login(self.email_user, self.email_password)
            self.mail.select("inbox")
            return True
        except Exception as e:
            print(f"Error conectando al correo: {e}")
            return False

    def disconnect(self):
        """Cierra la conexión"""
        if self.mail:
            try:
                self.mail.logout()
            except:
                pass

    def buscar_enlace_acceso(self, max_wait_seconds: int = 60) -> Optional[str]:
        """
        Busca el correo de la DIAN y extrae el enlace de acceso.
        Realiza varios intentos (polling) durante max_wait_seconds.
        """
        start_time = time.time()
        
        while (time.time() - start_time) < max_wait_seconds:
            # Buscar correos no leídos de la DIAN (o simplemente los más recientes)
            # El remitente suele ser: facturacion_electronica@dian.gov.co
            status, messages = self.mail.search(None, '(FROM "dian.gov.co" UNSEEN)')
            
            if status == "OK":
                mail_ids = messages[0].split()
                if mail_ids:
                    # Tomar el último correo recibido
                    latest_email_id = mail_ids[-1]
                    status, data = self.mail.fetch(latest_email_id, "(RFC822)")
                    
                    if status == "OK":
                        raw_email = data[0][1]
                        msg = email.message_from_bytes(raw_email)
                        
                        # Extraer el cuerpo del mensaje
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                if content_type == "text/html":
                                    body = part.get_payload(decode=True).decode()
                                    break
                        else:
                            body = msg.get_payload(decode=True).decode()

                        # Extracción con Regex del enlace de la DIAN
                        # El enlace suele tener un formato específico con un TOKEN
                        # Ejemplo: https://catalogo-vpfe.dian.gov.co/User/Login/TOKEN_AQUÍ
                        url_pattern = r'https?://[^\s<>"]+catalogo[^\s<>"]+/User/Login/[^\s<>"]+'
                        matches = re.findall(url_pattern, body)
                        
                        if matches:
                            # Marcar como leído
                            self.mail.store(latest_email_id, '+FLAGS', '\\Seen')
                            return matches[0]
            
            # Esperar un poco antes del siguiente intento
            time.sleep(5)
            # Re-seleccionar inbox para refrescar estado en algunos servidores
            self.mail.select("inbox")
            
        return None

# Ejemplo de uso (Prototipo)
if __name__ == "__main__":
    # Estos datos vendrían de la configuración de la empresa en Finaxis
    service = DianEmailService(
        imap_server="imap.gmail.com",
        email_user="facturacion.ejemplo@gmail.com",
        email_password="app_password_segura"
    )
    
    if service.connect():
        print("Buscando enlace de la DIAN...")
        enlace = service.buscar_enlace_acceso(max_wait_seconds=30)
        if enlace:
            print(f"¡Enlace capturado!: {enlace}")
        else:
            print("No se encontró el correo de la DIAN en el tiempo esperado.")
        service.disconnect()
