from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.services import usuario as services_usuario
from app.core import security
from app.core.hashing import verify_password
from app.core.database import get_db
from app.schemas import token as token_schema
from app.models import usuario as models_usuario
from app.core.security import limiter
from fastapi import Request

router = APIRouter()


# ==============================================================================
# 🔑 LOGIN — PASO 1: Verificación de Credenciales
# ==============================================================================
@router.post("/login", response_model=token_schema.LoginResponse)
@limiter.limit("10/5minutes")
def login_for_access_token(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    # 1. Anti-fuerza bruta: verificar si la cuenta está bloqueada
    security.check_account_lockout(form_data.username)

    user = services_usuario.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        security.register_failed_login(form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrecta",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Limpiar contador de fallos tras login exitoso
    security.reset_failed_login(form_data.username)
    roles_list = [rol.nombre for rol in user.roles]

    # 3. ¿El usuario requiere 2FA? (rol privilegiado + 2FA activo)
    if security.user_requires_2fa(user):
        temp_token = security.create_temp_2fa_token(
            email=user.email,
            empresa_id=user.empresa_id,
            roles=roles_list
        )
        # Respuesta de primer paso: el frontend debe mostrar la pantalla TOTP
        return token_schema.LoginResponse(requires_2fa=True, temp_token=temp_token)

    # 4. Flujo normal (sin 2FA configurado)
    access_token_expires = timedelta(minutes=security.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email, "empresa_id": user.empresa_id, "roles": roles_list},
        expires_delta=access_token_expires
    )

    # Verificar backups en segundo plano
    try:
        from app.services.scheduler_backup import check_missed_backups
        background_tasks.add_task(check_missed_backups)
    except Exception as e:
        import logging
        logging.error(f"Error programando validacion de backups en login: {e}")

    return token_schema.LoginResponse(access_token=access_token, token_type="bearer")


# ==============================================================================
# 🔐 LOGIN — PASO 2: Verificación del Código TOTP
# ==============================================================================
@router.post("/verify-2fa", response_model=token_schema.LoginResponse)
@limiter.limit("5/5minutes")  # Límite estricto: 5 intentos máximo
def verify_two_factor(
    request: Request,
    payload: token_schema.TwoFactorVerifyRequest,
    db: Session = Depends(get_db)
):
    """
    Segunda fase del login para usuarios con 2FA activo.
    Recibe el token temporal del paso 1 y el código TOTP de 6 dígitos.
    """
    # 1. Decodificar y validar el token temporal (scope: 2fa_pending)
    token_data = security.decode_temp_2fa_token(payload.temp_token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión de verificación expirada o inválida. Por favor, inicia sesión nuevamente."
        )

    email = token_data.get("sub")

    # 2. Cargar el usuario y su secreto TOTP
    user = services_usuario.get_user_by_email(db, email=email)
    if not user or not user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de configuración 2FA. Contacta al administrador."
        )

    # 3. Verificar el código TOTP contra el secreto del usuario
    if not security.verify_totp_code(user.totp_secret, payload.totp_code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código de autenticación incorrecto o expirado. Intenta con el código actual de tu autenticador."
        )

    # 4. ¡Todo válido! Emitir el JWT completo de sesión
    roles_list = token_data.get("roles", [])
    empresa_id = token_data.get("empresa_id", user.empresa_id)
    access_token_expires = timedelta(minutes=security.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": email, "empresa_id": empresa_id, "roles": roles_list},
        expires_delta=access_token_expires
    )

    return token_schema.LoginResponse(access_token=access_token, token_type="bearer")


# ==============================================================================
# ⚙️ SETUP 2FA — Generar secreto y URI del QR
# ==============================================================================
@router.get("/setup-2fa", response_model=token_schema.TwoFactorSetupResponse)
def setup_two_factor(
    current_user: models_usuario.Usuario = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Genera un nuevo secreto TOTP y devuelve el URI para mostrar como QR.
    Este endpoint NO activa el 2FA todavía; se requiere confirmar con /activate-2fa.
    El QR puede escanearse con Google Authenticator, Authy, Microsoft Authenticator, etc.
    """
    secret = security.generate_totp_secret()

    # Guardar secreto en el usuario (aún no activado, totp_enabled sigue en False)
    user = db.query(models_usuario.Usuario).filter(
        models_usuario.Usuario.id == current_user.id
    ).first()
    user.totp_secret = secret
    user.totp_enabled = False  # Se activa solo después de confirmar en /activate-2fa
    db.commit()

    qr_uri = security.get_totp_uri(secret, current_user.email)

    return token_schema.TwoFactorSetupResponse(secret=secret, qr_uri=qr_uri)


# ==============================================================================
# ✅ ACTIVAR 2FA — Confirmar que el usuario escaneó el QR correctamente
# ==============================================================================
@router.post("/activate-2fa")
def activate_two_factor(
    payload: token_schema.TwoFactorActivateRequest,
    current_user: models_usuario.Usuario = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Activa el 2FA en la cuenta del usuario.
    Requiere un código válido de su autenticador para confirmar que el QR fue escaneado.
    """
    user = db.query(models_usuario.Usuario).filter(
        models_usuario.Usuario.id == current_user.id
    ).first()

    if not user.totp_secret:
        raise HTTPException(
            status_code=400,
            detail="Primero debes iniciar el setup con GET /api/auth/setup-2fa."
        )

    if not security.verify_totp_code(user.totp_secret, payload.totp_code):
        raise HTTPException(
            status_code=400,
            detail="Código incorrecto. Asegúrate de haber escaneado el QR correctamente y que el reloj de tu dispositivo esté sincronizado."
        )

    user.totp_enabled = True
    db.commit()

    return {
        "success": True,
        "message": "✅ Autenticación de dos factores activada correctamente. Tu cuenta ahora requiere el código del autenticador al iniciar sesión."
    }


# ==============================================================================
# 🗑️ DESACTIVAR 2FA — Solo el propio usuario autenticado puede hacerlo
# ==============================================================================
@router.delete("/disable-2fa")
def disable_two_factor(
    current_user: models_usuario.Usuario = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Desactiva el 2FA de la cuenta del usuario.
    Requiere una sesión completa activa (no acepta temp_token).
    Para recuperación de cuentas bloqueadas, el soporte puede hacerlo desde el panel.
    """
    user = db.query(models_usuario.Usuario).filter(
        models_usuario.Usuario.id == current_user.id
    ).first()
    user.totp_secret = None
    user.totp_enabled = False
    db.commit()

    return {
        "success": True,
        "message": "2FA desactivado. Tu cuenta ahora solo requiere usuario y contraseña."
    }


# ==============================================================================
# 🔑 LOGIN SOPORTE — Sin cambios (usa flujo independiente)
# ==============================================================================
@router.post("/soporte/login", response_model=token_schema.Token)
@limiter.limit("10/5minutes")
def login_soporte_for_access_token(
    request: Request,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    security.check_account_lockout(form_data.username)

    user: models_usuario.Usuario = services_usuario.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        security.register_failed_login(form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de soporte incorrectas.",
        )

    security.reset_failed_login(form_data.username)

    user_roles = {rol.nombre for rol in user.roles} if user.roles else set()

    if "soporte" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no tiene permisos de soporte.",
        )

    access_token_expires = timedelta(hours=4)
    roles_list = [rol.nombre for rol in user.roles]
    access_token = security.create_access_token(
        data={"sub": user.email, "empresa_id": user.empresa_id, "roles": roles_list},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# ==============================================================================
# 🏢 SWITCH COMPANY — Sin cambios
# ==============================================================================
from pydantic import BaseModel

class CompanySwitchRequest(BaseModel):
    empresa_id: int

@router.post("/switch-company", response_model=token_schema.Token)
def switch_company_context(
    switch_data: CompanySwitchRequest,
    current_user: models_usuario.Usuario = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    """Genera un nuevo token con el contexto de la empresa seleccionada."""
    target_empresa_id = switch_data.empresa_id

    user_roles = {rol.nombre for rol in current_user.roles}
    if "soporte" in user_roles:
        pass
    else:
        access_found = False

        if current_user.empresa_id == target_empresa_id:
            access_found = True

        if not access_found:
            for emp in current_user.empresas_asignadas:
                if emp.id == target_empresa_id:
                    access_found = True
                    break

        if not access_found:
            from app.models import empresa as models_empresa
            target_company = db.query(models_empresa.Empresa).filter(
                models_empresa.Empresa.id == target_empresa_id
            ).first()

            if target_company:
                if target_company.owner_id == current_user.id:
                    access_found = True
                elif current_user.empresa_id and target_company.padre_id == current_user.empresa_id:
                    if "Administrador" in user_roles:
                        access_found = True

        if not access_found:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes acceso a esta empresa."
            )

    access_token_expires = timedelta(minutes=security.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    roles_list = [rol.nombre for rol in current_user.roles]
    access_token = security.create_access_token(
        data={"sub": current_user.email, "empresa_id": target_empresa_id, "roles": roles_list},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}