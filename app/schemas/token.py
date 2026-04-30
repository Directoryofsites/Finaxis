from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None
    empresa_id: Optional[int] = None

# --- 2FA: Respuesta flexible del login ---
class LoginResponse(BaseModel):
    """
    Respuesta unificada del endpoint /login.
    - Flujo normal: access_token + token_type
    - Flujo 2FA:    requires_2fa=True + temp_token
    """
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    requires_2fa: bool = False
    temp_token: Optional[str] = None  # JWT temporal de 5 min, solo válido para /verify-2fa

# --- 2FA: Petición para el segundo paso ---
class TwoFactorVerifyRequest(BaseModel):
    temp_token: str   # JWT temporal recibido en el primer paso del login
    totp_code: str    # Código de 6 dígitos del autenticador

# --- 2FA: Setup inicial (genera el QR) ---
class TwoFactorSetupResponse(BaseModel):
    secret: str   # Clave base32 para respaldo manual
    qr_uri: str   # URI otpauth:// para mostrar como QR

# --- 2FA: Activación (confirma que el usuario escaneó el QR) ---
class TwoFactorActivateRequest(BaseModel):
    totp_code: str  # El usuario provee un código válido para confirmar el setup