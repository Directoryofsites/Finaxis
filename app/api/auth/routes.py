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
    # FIX: Incluir roles en el token para que el frontend pueda redireccionar
    roles_list = [rol.nombre for rol in user.roles]
    access_token = security.create_access_token(
        data={"sub": user.email, "empresa_id": user.empresa_id, "roles": roles_list},
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
    roles_list = [rol.nombre for rol in user.roles]
    access_token = security.create_access_token(
        data={"sub": user.email, "empresa_id": user.empresa_id, "roles": roles_list},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

from pydantic import BaseModel
class CompanySwitchRequest(BaseModel):
    empresa_id: int

@router.post("/switch-company", response_model=token_schema.Token)
def switch_company_context(
    switch_data: CompanySwitchRequest,
    current_user: models_usuario.Usuario = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Genera un nuevo token con el contexto de la empresa seleccionada.
    Verifica que el usuario tenga acceso a dicha empresa.
    """
    target_empresa_id = switch_data.empresa_id
    
    # 1. Verificar si el usuario es Super Admin (Soporte) -> Acceso Total
    user_roles = {rol.nombre for rol in current_user.roles}
    if "soporte" in user_roles:
        # Permitir switch a cualquier empresa
        pass
    else:
        # 2. Verificar acceso en lista de empresas asignadas
        # Usamos la relación N:M definida en el modelo Usuario
        access_found = False
        
        # A. Empresa Propia (Directa legacy)
        if current_user.empresa_id == target_empresa_id:
            access_found = True
            
        # B. Empresas Asignadas (Multi-Tenancy)
        if not access_found:
            for emp in current_user.empresas_asignadas:
                if emp.id == target_empresa_id:
                    access_found = True
                    break
        
        # C. Check Jerarquía y Propiedad (FIX 403)
        if not access_found:
             from app.models import empresa as models_empresa
             target_company = db.query(models_empresa.Empresa).filter(models_empresa.Empresa.id == target_empresa_id).first()
             
             if target_company:
                 # Check Owner
                 if target_company.owner_id == current_user.id:
                     access_found = True
                 # Check Padre (Si soy usuario de la holding)
                 elif current_user.empresa_id and target_company.padre_id == current_user.empresa_id:
                     access_found = True

        if not access_found:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes acceso a esta empresa."
            )

    # 3. Generar nuevo token con el empresa_id actualizado
    access_token_expires = timedelta(minutes=security.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Propagar roles
    roles_list = [rol.nombre for rol in current_user.roles]
    
    access_token = security.create_access_token(
        data={"sub": current_user.email, "empresa_id": target_empresa_id, "roles": roles_list},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}