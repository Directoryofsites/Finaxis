
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import smtplib
from ...core.database import get_db
from ...core.security import get_current_user
from ...models.usuario import Usuario
from ...models.empresa_config import EmpresaConfigEmail
from ...core.security_encryption import EncryptionManager

router = APIRouter(prefix="/email", tags=["Configuración"])

class EmailConfigSchema(BaseModel):
    smtp_user: EmailStr
    smtp_password: str # App Password (plaintext from frontend)

class ConfigResponse(BaseModel):
    smtp_user: str
    is_configured: bool

@router.get("/", response_model=ConfigResponse)
def get_email_config(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.empresa_id:
        raise HTTPException(status_code=400, detail="Usuario no asociado a empresa")
    
    config = db.query(EmpresaConfigEmail).filter(EmpresaConfigEmail.empresa_id == current_user.empresa_id).first()
    
    if config:
        return {"smtp_user": config.smtp_user, "is_configured": True}
    return {"smtp_user": "", "is_configured": False}

@router.post("/")
def save_email_config(data: EmailConfigSchema, current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.empresa_id:
        raise HTTPException(status_code=400, detail="Usuario no asociado a empresa")

    # Encrypt Password
    encrypted_pw = EncryptionManager.encrypt(data.smtp_password)
    
    config = db.query(EmpresaConfigEmail).filter(EmpresaConfigEmail.empresa_id == current_user.empresa_id).first()
    
    if config:
        config.smtp_user = data.smtp_user
        config.smtp_password_enc = encrypted_pw
    else:
        new_config = EmpresaConfigEmail(
            empresa_id=current_user.empresa_id,
            smtp_user=data.smtp_user,
            smtp_password_enc=encrypted_pw
        )
        db.add(new_config)
    
    db.commit()
    return {"message": "Configuración de correo guardada exitosamente."}

@router.post("/test")
def test_email_config(data: EmailConfigSchema):
    """
    Prueba la conexión SMTP antes de guardar.
    """
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(data.smtp_user, data.smtp_password)
        server.quit()
        return {"message": "Conexión exitosa", "success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fallo de conexión: {str(e)}")
