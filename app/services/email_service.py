import os
import smtplib
from email.message import EmailMessage
from ..core.database import SessionLocal
from ..models.empresa_config import EmpresaConfigEmail
from ..core.security_encryption import EncryptionManager

class EmailService:
    def __init__(self):
        # Default fallback credentials (from .env)
        self.default_user = os.getenv("GMAIL_USER")
        self.default_password = os.getenv("GMAIL_PASSWORD")
        self.default_host = "smtp.gmail.com"
        self.default_port = 587

    def _get_credentials(self, empresa_id=None):
        """
        Retorna (user, password, host, port) buscando primero en DB pro empresa,
        luego fallback a .env global.
        """
        if empresa_id:
            try:
                db = SessionLocal()
                config = db.query(EmpresaConfigEmail).filter(EmpresaConfigEmail.empresa_id == empresa_id).first()
                db.close()

                if config:
                    decrypted_password = EncryptionManager.decrypt(config.smtp_password_enc)
                    if decrypted_password:
                        return config.smtp_user, decrypted_password, config.smtp_host, config.smtp_port
            except Exception as e:
                print(f"⚠️ Error fetching Email Config from DB: {e}")
        
        # Fallback to .env
        return self.default_user, self.default_password, self.default_host, self.default_port

    def send_email_with_pdf(self, to_email: str, subject: str, body: str, pdf_content: bytes, filename: str, empresa_id: int = None):
        """
        Envía un correo electrónico con un archivo PDF adjunto.
        Prioriza la configuración de la empresa si existe.
        """
        user, password, host, port = self._get_credentials(empresa_id)

        if not user or not password:
            print("⚠️ EMAIL CONFIG MISSING: No SMTP config found for this company or in .env")
            return False, "Configuración de correo no encontrada."

        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = user
        msg['To'] = to_email
        msg.set_content(body)

        # Adjuntar PDF
        msg.add_attachment(
            pdf_content,
            maintype='application',
            subtype='pdf',
            filename=filename
        )

        try:
            with smtplib.SMTP(host, port) as server:
                server.starttls()
                server.login(user, password)
                server.send_message(msg)
            print(f"✅ Correo enviado exitosamente a {to_email} (vía {user})")
            return True, "Correo enviado exitosamente."
        except Exception as e:
            print(f"❌ Error enviando correo: {str(e)}")
            return False, f"Error al enviar el correo: {str(e)}"

# Instancia global
email_service = EmailService()
