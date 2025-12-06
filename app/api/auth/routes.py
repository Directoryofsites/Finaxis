from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.services import usuario as services_usuario
from app.core import security
# --- INICIO DE LA CORRECCIÓN ARQUITECTÓNICA ---
# Se importa la función de verificación desde su nuevo hogar en el módulo de hashing.
from app.core.hashing import verify_password
# --- FIN DE LA CORRECCIÓN ARQUITECTÓNICA ---
from app.core.database import get_db
from app.schemas import token as token_schema
from app.models import usuario as models_usuario

router = APIRouter()

@router.post("/login", response_model=token_schema.Token)
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = services_usuario.get_user_by_email(db, email=form_data.username)
    # --- INICIO DE LA CORRECCIÓN ARQUITECTÓNICA ---
    # Se llama directamente a la función verify_password importada.
    if not user or not verify_password(form_data.password, user.password_hash):
    # --- FIN DE LA CORRECCIÓN ARQUITECTÓNICA ---
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrecta",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email, "empresa_id": user.empresa_id},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/soporte/login", response_model=token_schema.Token)
def login_soporte_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user: models_usuario.Usuario = services_usuario.get_user_by_email(db, email=form_data.username)
    # --- INICIO DE LA CORRECCIÓN ARQUITECTÓNICA ---
    # Se aplica la misma corrección a la ruta de login de soporte.
    if not user or not verify_password(form_data.password, user.password_hash):
    # --- FIN DE LA CORRECCIÓN ARQUITECTÓNICA ---
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de soporte incorrectas.",
        )
    
    user_roles = {rol.nombre for rol in user.roles} if user.roles else set()

        # --- INICIO: SONDAS DE DIAGNÓSTICO DE LA CAJA NEGRA ---
    print("="*50)
    print(f"SONDA DE DIAGNÓSTICO: Verificando al usuario: {user.email}")
    print(f"SONDA DE DIAGNÓSTICO: ¿Atributo 'roles' existe?: {'roles' in dir(user)}")
    print(f"SONDA DE DIAGNÓSTICO: Contenido de user.roles: {user.roles}")
    print("="*50)
    # --- FIN: SONDAS DE DIAGNÓSTICO ---

    if "soporte" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no tiene permisos de soporte.",
        )

    access_token_expires = timedelta(hours=4)
    access_token = security.create_access_token(
        data={"sub": user.email, "empresa_id": user.empresa_id},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}