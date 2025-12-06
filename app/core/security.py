from datetime import datetime, timedelta, timezone
from typing import Optional, Set
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, selectinload, joinedload 

from .config import settings
from app.core.database import get_db
from app.schemas import token as schemas_token
from app.models import usuario as models_usuario
from app.models import permiso as models_permiso
from app.core.hashing import verify_password, get_password_hash # Asegurar esta importación

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# --- Funciones Auxiliares de JWT (Print/PDF) ---

def create_print_token(documento_id: int, empresa_id: int) -> str:
    """Crea un token de corta duración para imprimir un documento (Ámbito 'document_print')."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=5)
    to_encode = {
        "exp": expire, "sub": f"doc_print:{documento_id}", "scope": "document_print",
        "doc_id": documento_id, "emp_id": empresa_id
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_print_token(token: str) -> dict:
    """Decodifica y valida el token de impresión."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        scope: str = payload.get("scope")
        if scope != "document_print":
            raise JWTError("Invalid token scope.")
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token de impresión inválido o expirado: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )

# === FUNCIONES DE PDF DE REPORTES (Scope 'report_pdf') ===
def create_pdf_jwt(data: dict) -> str:
    """Crea un token de corta duración para generar reportes PDF."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=5) 
    to_encode = data.copy()
    to_encode.update({"exp": expire, "scope": "report_pdf"}) 
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_pdf_jwt(token: str) -> dict:
    """Decodifica y valida el token de reporte PDF."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        scope: str = payload.get("scope")
        if scope != "report_pdf":
            raise JWTError("Invalid token scope.")
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token de reporte PDF inválido o expirado: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )

# === FUNCIONES GENÉRICAS DE TOKEN FIRMADO (RESTAURADAS Y SANEADAS - FIX CRÍTICO) ===
def create_signed_token(data: str, salt: str, max_age: int) -> str: # <-- FIX: SE AÑADE max_age
    """Crea un token firmado genérico con un 'salt'/'scope' específico."""
    # Usamos max_age (en segundos) para calcular el expire
    expire = datetime.now(timezone.utc) + timedelta(seconds=max_age) 
    to_encode = {"exp": expire, "sub": data, "scope": salt}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def validate_signed_token(token: str, salt: str, max_age: int) -> Optional[str]:
    """Valida un token firmado genérico y devuelve el campo 'sub' (data)."""
    try:
        # El tiempo de expiración es verificado automáticamente por jwt.decode con options={"verify_exp": True} (por defecto)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]) 
        if payload.get("scope") == salt:
            sub_data = payload.get("sub")
            if sub_data is None:
                raise JWTError("Token lacks required 'sub' payload.")
            return sub_data
        return None
    except JWTError:
        return None
# === FIN: FUNCIONES GENÉRICAS ===


def get_user_permissions(user: models_usuario.Usuario) -> Set[str]:
    # ... (Lógica de permisos) ...
    if not user.roles:
        return set()
    permissions = set()
    for role in user.roles:
        for permission in role.permisos:
            permissions.add(permission.nombre)
    for excepcion in user.excepciones:
        if excepcion.permitido:
            permissions.add(excepcion.permiso.nombre)
        else:
            permissions.discard(excepcion.permiso.nombre)
    return permissions

def has_permission(required_permission: str):
    def _permission_checker(
        current_user: models_usuario.Usuario = Depends(get_current_user)
    ) -> models_usuario.Usuario:
        # Lógica de verificación de permisos
        user_permissions = get_user_permissions(current_user)
        if required_permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado: se requiere el permiso '{required_permission}'"
            )
        return current_user

    return _permission_checker

# ... (El resto de las funciones de seguridad se mantienen) ...

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models_usuario.Usuario:
    # ... (Lógica de get_current_user con selectinload) ...
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_email: str = payload.get("sub")
        if user_email is None:
            raise credentials_exception
        token_data = schemas_token.TokenData(email=user_email)
    except JWTError:
        raise credentials_exception

    user = db.query(models_usuario.Usuario).options(
        selectinload(models_usuario.Usuario.roles).selectinload(models_permiso.Rol.permisos),
        selectinload(models_usuario.Usuario.excepciones).selectinload(models_permiso.UsuarioPermisoExcepcion.permiso)
    ).filter(models_usuario.Usuario.email == token_data.email).first()

    if user is None:
        raise credentials_exception
    return user

oauth2_soporte_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/soporte/login")

async def get_current_soporte_user(
    token: str = Depends(oauth2_soporte_scheme),
    db: Session = Depends(get_db)
) -> models_usuario.Usuario:
    # ... (Lógica de get_current_soporte_user) ...
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales de soporte",
        headers={"WWW-Authenticate": "Bearer"},
    )
    forbidden_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Acceso denegado: se requiere rol de soporte.",
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_email: str = payload.get("sub")
        if user_email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models_usuario.Usuario).options(
        selectinload(models_usuario.Usuario.roles)
    ).filter(models_usuario.Usuario.email == user_email).first()
    
    if user is None:
        raise credentials_exception

    is_soporte = any(role.nombre == 'soporte' for role in user.roles)
    if not is_soporte:
        raise forbidden_exception
    return user