from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.services import usuario as services_usuario
from app.schemas import usuario as schemas_usuario
from app.core.security import get_current_user, has_permission, get_user_permissions
from app.models import usuario as models_usuario
from app.models import permiso as models_permiso

router = APIRouter()

# --- UTILS ---
def get_current_active_soporte_user(
    current_user: models_usuario.Usuario = Depends(get_current_user)
) -> models_usuario.Usuario:
    if current_user.empresa_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para realizar esta operación de soporte."
        )
    return current_user

# --- ENDPOINTS GLOBALES (AUTOSERVICIO) ---

@router.get("/me", response_model=schemas_usuario.User)
def read_users_me(
    current_user: models_usuario.Usuario = Depends(get_current_user),
):
    """
    Retorna el perfil del usuario actual, incluyendo ROLES y PERMISOS.
    Esencial para que el frontend pueda renderizar los menús correctamente.
    """
    from app.core.database import SessionLocal
    
    clean_db = SessionLocal()
    try:
        # Consultamos el usuario "puro" de la BD
        db_user = clean_db.query(models_usuario.Usuario).filter(
            models_usuario.Usuario.id == current_user.id
        ).first()
        
        home_company = "Consorcio"
        if db_user and db_user.empresa:
            curr_emp = db_user.empresa
            while curr_emp.padre:
                print(f"DEBUG WELCOME: Climbing up from {curr_emp.razon_social} to parent...")
                curr_emp = curr_emp.padre
            home_company = curr_emp.razon_social
            print(f"DEBUG WELCOME: Root Company Found: {home_company}")
            
        current_user.empresa_original_nombre = home_company
        print(f"DEBUG WELCOME: Final Field Set: {current_user.empresa_original_nombre}")
        
        # CAPA 3: Recargar el usuario CON TODAS SUS RELACIONES desde clean_db
        # Esto garantiza que roles, permisos y excepciones estén cargados correctamente
        # sin depender del estado de la sesión principal de la request.
        user_for_perms = clean_db.query(models_usuario.Usuario).options(
            selectinload(models_usuario.Usuario.roles).selectinload(models_permiso.Rol.permisos),
            selectinload(models_usuario.Usuario.excepciones).selectinload(
                models_permiso.UsuarioPermisoExcepcion.permiso
            ),
        ).filter(models_usuario.Usuario.id == current_user.id).first()
        
        if user_for_perms:
            calculated_permissions = list(get_user_permissions(user_for_perms))
            print(f"DEBUG PERMISOS: Calculados para {current_user.email}: {calculated_permissions}")
        else:
            calculated_permissions = []
            
        current_user.permissions = calculated_permissions
        
    finally:
        clean_db.close()
    
    return current_user



@router.get("/", response_model=List[schemas_usuario.User])
def read_company_users(
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("empresa:usuarios_roles"))
):
    """
    Lista usuarios.
    - Si es Soporte: Lista TODOS (o debería filtrar? Usaremos /soporte para soporte).
      Aquí listaremos los de la empresa actual si el usuario tiene empresa.
    """
    if current_user.empresa_id:
        # Usuario de empresa: listar solo los de SU empresa
        return services_usuario.get_users_by_company(db, current_user.empresa_id)
    else:
        # Usuario de soporte: prohibido listar TODO el sistema por aquí por performance/seguridad
        # Usar endpoints específicos de soporte o retornar lista vacía
        return []

@router.post("/", response_model=schemas_usuario.User, status_code=status.HTTP_201_CREATED)
def create_company_user(
    user_data: schemas_usuario.UserCreateInCompany,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("empresa:usuarios_roles"))
):
    """
    Crea un usuario en la MISMMA empresa que el usuario actual.
    Autoservicio.
    """
    if not current_user.empresa_id:
        raise HTTPException(status_code=400, detail="Soporte debe usar el panel de empresas.")
    
    return services_usuario.create_user_in_company(db, user_data, current_user.empresa_id)

@router.put("/{usuario_id}", response_model=schemas_usuario.User)
def update_user_details(
    usuario_id: int,
    user_update: schemas_usuario.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """
    Actualiza usuario.
    Permitido si:
    1. Soy Soporte (role 'soporte').
    2. Soy Admin de empresa (permiso 'empresa:usuarios_roles') Y el usuario destino es de MI empresa.
    """
    # 1. Verificar si es usuario soporte
    is_soporte = any(role.nombre == 'soporte' for role in current_user.roles)

    # 2. Verificar permisos estándar si NO es soporte
    if not is_soporte:
        user_permissions = get_user_permissions(current_user)
        if "empresa:usuarios_roles" not in user_permissions:
             raise HTTPException(status_code=403, detail="Acceso denegado: se requiere el permiso 'empresa:usuarios_roles'")

    user_to_update = services_usuario.get_user_by_id(db, usuario_id=usuario_id)
    if not user_to_update:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    
    # Validacion de scope
    is_same_company = user_to_update.empresa_id == current_user.empresa_id
    
    # Si NO es soporte y NO es de la misma empresa -> PROHIBIDO
    if not is_soporte and not is_same_company:
         raise HTTPException(status_code=403, detail="No tiene permiso para editar este usuario (pertenece a otra empresa).")

    return services_usuario.update_user(db=db, user=user_to_update, user_update=user_update)

@router.delete("/{usuario_id}", response_model=schemas_usuario.UserDeleteResponse)
def delete_single_user(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """
    Elimina usuario.
    Mismas reglas: Soporte o Misma Empresa.
    """
    # 1. Verificar si es usuario soporte
    is_soporte = any(role.nombre == 'soporte' for role in current_user.roles)

    # 2. Verificar permisos estándar si NO es soporte
    if not is_soporte:
        user_permissions = get_user_permissions(current_user)
        if "empresa:usuarios_roles" not in user_permissions:
             raise HTTPException(status_code=403, detail="Acceso denegado: se requiere el permiso 'empresa:usuarios_roles'")

    user_to_delete = services_usuario.get_user_by_id(db, usuario_id=usuario_id)
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
        
    is_same_company = user_to_delete.empresa_id == current_user.empresa_id
    
    if not is_soporte and not is_same_company:
         raise HTTPException(status_code=403, detail="No tiene permiso para eliminar este usuario.")

    return services_usuario.delete_usuario(db=db, usuario_id=usuario_id)

# --- ENDPOINTS DE SOPORTE (LEGACY/SPECIFIC) ---

@router.get("/soporte", response_model=List[schemas_usuario.User])
def read_soporte_users(
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_active_soporte_user)
):
    return services_usuario.get_soporte_users(db)

@router.post("/soporte", response_model=schemas_usuario.User, status_code=status.HTTP_201_CREATED)
def create_new_soporte_user(
    user_data: schemas_usuario.SoporteUserCreate,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_active_soporte_user)
):
    return services_usuario.create_soporte_user(db, user_data)

@router.put("/soporte/{usuario_id}/password", status_code=status.HTTP_200_OK)
def change_soporte_user_password(
    usuario_id: int,
    password_update: schemas_usuario.UserPasswordUpdate,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_active_soporte_user)
):
    user_to_update = services_usuario.get_user_by_id(db, usuario_id=usuario_id)
    if not user_to_update or user_to_update.empresa_id is not None:
        raise HTTPException(status_code=404, detail="Usuario de soporte no encontrado")

    services_usuario.update_password(db, user_to_update, password_update.nuevaPassword)
    return {"message": "Contraseña actualizada."}


# ============================================================
# ENDPOINTS: EXCEPCIONES DE PERMISOS POR USUARIO (Capa 3)
# ============================================================
from app.schemas.permiso import ExcepcionPermisoBatch, PermisoConEstado
from app.services import rol as rol_service

def _validar_acceso_a_usuario(
    usuario_id: int,
    current_user: models_usuario.Usuario,
    db: Session
) -> models_usuario.Usuario:
    """
    Valida que el current_user tenga derecho a gestionar las excepciones del usuario objetivo.
    Reglas: Soporte puede todo. Admin de empresa solo puede gestionar usuarios de SU empresa.
    """
    is_soporte = any(r.nombre == 'soporte' for r in current_user.roles)
    user_permissions = get_user_permissions(current_user)

    if not is_soporte and "empresa:usuarios_roles" not in user_permissions:
        raise HTTPException(status_code=403, detail="No tiene permiso para gestionar usuarios.")

    usuario_objetivo = services_usuario.get_user_by_id(db, usuario_id=usuario_id)
    if not usuario_objetivo:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    if not is_soporte and usuario_objetivo.empresa_id != current_user.empresa_id:
        raise HTTPException(status_code=403, detail="No puede gestionar usuarios de otra empresa.")

    return usuario_objetivo


@router.get(
    "/{usuario_id}/permisos",
    response_model=List[PermisoConEstado],
    summary="Ver permisos con estado de un usuario",
    description="Retorna todos los permisos del sistema indicando para cada uno: "
                "si viene del rol, si tiene excepción, y cuál es el resultado final."
)
def get_permisos_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user),
):
    usuario_objetivo = _validar_acceso_a_usuario(usuario_id, current_user, db)
    return rol_service.get_permisos_con_estado(
        db=db,
        usuario_id=usuario_id,
        empresa_id=usuario_objetivo.empresa_id,
    )


@router.put(
    "/{usuario_id}/permisos/excepciones",
    summary="Guardar excepciones de permisos",
    description="Aplica un batch de excepciones (CONCEDER / REVOCAR) a un usuario. "
                "Si la excepción ya existe, la actualiza. Si no, la crea."
)
def upsert_excepciones_usuario(
    usuario_id: int,
    payload: ExcepcionPermisoBatch,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user),
):
    _validar_acceso_a_usuario(usuario_id, current_user, db)

    excepciones_data = [
        {"permiso_id": e.permiso_id, "permitido": e.permitido}
        for e in payload.excepciones
    ]
    count = rol_service.upsert_excepciones(db=db, usuario_id=usuario_id, excepciones_data=excepciones_data)
    return {
        "msg": f"Se aplicaron {count} excepción(es) correctamente.",
        "total": count,
    }


@router.delete(
    "/{usuario_id}/permisos/excepciones/{permiso_id}",
    summary="Eliminar una excepción específica",
    description="Elimina la excepción de un permiso puntual. "
                "El usuario vuelve a heredar ese permiso de su rol."
)
def delete_excepcion_usuario(
    usuario_id: int,
    permiso_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user),
):
    _validar_acceso_a_usuario(usuario_id, current_user, db)
    eliminada = rol_service.delete_excepcion(db=db, usuario_id=usuario_id, permiso_id=permiso_id)
    if not eliminada:
        raise HTTPException(status_code=404, detail="No existe esa excepción para este usuario.")
    return {"msg": "Excepción eliminada. El usuario hereda el comportamiento de su rol."}


@router.delete(
    "/{usuario_id}/permisos/excepciones",
    summary="Resetear todas las excepciones",
    description="Elimina TODAS las excepciones del usuario. "
                "Queda con los permisos puros de su rol, sin ninguna personalización."
)
def reset_excepciones_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(get_current_user),
):
    _validar_acceso_a_usuario(usuario_id, current_user, db)
    total = rol_service.clear_all_excepciones(db=db, usuario_id=usuario_id)
    return {
        "msg": f"Se eliminaron {total} excepción(es). El usuario quedó con los permisos puros de su rol.",
        "total": total,
    }