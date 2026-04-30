from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import permiso as models
from app.schemas import permiso as schemas

# --- PERMISOS ---
def get_all_permisos(db: Session) -> List[models.Permiso]:
    """Retorna todos los permisos disponibles en el sistema."""
    return db.query(models.Permiso).all()

# --- ROLES ---
def get_roles_by_empresa(db: Session, empresa_id: int) -> List[models.Rol]:
    """
    Retorna roles globales (empresa_id IS NULL) Y roles de la empresa dada.
    """
    return db.query(models.Rol).filter(
        or_(
            models.Rol.empresa_id == None,
            models.Rol.empresa_id == empresa_id
        )
    ).all()

def get_rol_by_id(db: Session, rol_id: int) -> Optional[models.Rol]:
    return db.query(models.Rol).filter(models.Rol.id == rol_id).first()

def create_rol(db: Session, rol_data: schemas.RolCreate, empresa_id: int) -> models.Rol:
    """Crea un rol personalizado para una empresa."""
    db_rol = models.Rol(
        nombre=rol_data.nombre,
        descripcion=rol_data.descripcion,
        empresa_id=empresa_id
    )
    
    # Asignar permisos
    if rol_data.permisos_ids:
        permisos = db.query(models.Permiso).filter(models.Permiso.id.in_(rol_data.permisos_ids)).all()
        db_rol.permisos = permisos
        
    db.add(db_rol)
    db.commit()
    db.refresh(db_rol)
    return db_rol

def update_rol(db: Session, rol: models.Rol, rol_update: schemas.RolUpdate) -> models.Rol:
    """Actualiza un rol existente."""
    if rol_update.nombre is not None:
        rol.nombre = rol_update.nombre
    if rol_update.descripcion is not None:
        rol.descripcion = rol_update.descripcion
        
    if rol_update.permisos_ids is not None:
        permisos = db.query(models.Permiso).filter(models.Permiso.id.in_(rol_update.permisos_ids)).all()
        rol.permisos = permisos
        
    db.commit()
    db.refresh(rol)
    return rol

def delete_rol(db: Session, rol: models.Rol):
    """Elimina un rol."""
    db.delete(rol)
    db.commit()


# ============================================================
# SERVICIOS PARA EXCEPCIONES DE PERMISOS POR USUARIO
# ============================================================

def get_permisos_con_estado(db: Session, usuario_id: int, empresa_id: int) -> list:
    """
    Retorna TODOS los permisos del sistema con el estado real de ese usuario:
    - si lo hereda del rol
    - si tiene una excepción (CONCEDIDO/REVOCADO)
    - cuál es el resultado final (estado_efectivo)

    Esta es la fuente de datos para la pantalla de edición de permisos del usuario.
    """
    from app.models.usuario import Usuario
    from app.schemas.permiso import PermisoConEstado

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        return []

    # 1. Construir set de permisos que el usuario TIENE por su rol
    permisos_por_rol: set[int] = set()
    for rol in usuario.roles:
        for p in rol.permisos:
            permisos_por_rol.add(p.id)

    # 2. Construir mapa de excepciones: {permiso_id: permitido(bool)}
    mapa_excepciones: dict[int, bool] = {
        exc.permiso_id: exc.permitido
        for exc in usuario.excepciones
    }

    # 3. Obtener todos los permisos del sistema (filtrados por empresa si fuera necesario)
    todos_los_permisos = db.query(models.Permiso).order_by(models.Permiso.nombre).all()

    resultado = []
    for permiso in todos_los_permisos:
        tiene_por_rol = permiso.id in permisos_por_rol
        tiene_excepcion = permiso.id in mapa_excepciones
        excepcion_permitido = mapa_excepciones.get(permiso.id)  # None si no hay excepción

        # Estado efectivo: la excepción manda sobre el rol
        if tiene_excepcion:
            estado_efectivo = excepcion_permitido
        else:
            estado_efectivo = tiene_por_rol

        resultado.append(PermisoConEstado(
            id=permiso.id,
            nombre=permiso.nombre,
            descripcion=permiso.descripcion,
            tiene_por_rol=tiene_por_rol,
            tiene_excepcion=tiene_excepcion,
            excepcion_permitido=excepcion_permitido,
            estado_efectivo=estado_efectivo,
        ))

    return resultado


def upsert_excepciones(db: Session, usuario_id: int, excepciones_data: list) -> int:
    """
    Guarda un batch de excepciones para un usuario.
    Si ya existe una excepción para ese permiso, la actualiza (upsert).
    Retorna la cantidad de excepciones procesadas.
    """
    from app.models.usuario import Usuario

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        return 0

    # Mapa actual de excepciones en BD
    mapa_actual: dict[int, models.UsuarioPermisoExcepcion] = {
        exc.permiso_id: exc for exc in usuario.excepciones
    }

    count = 0
    for item in excepciones_data:
        permiso_id = item["permiso_id"]
        permitido = item["permitido"]

        # Verificar que el permiso existe
        permiso = db.query(models.Permiso).filter(models.Permiso.id == permiso_id).first()
        if not permiso:
            continue

        if permiso_id in mapa_actual:
            # Actualizar existente
            mapa_actual[permiso_id].permitido = permitido
        else:
            # Crear nueva excepción
            nueva = models.UsuarioPermisoExcepcion(
                usuario_id=usuario_id,
                permiso_id=permiso_id,
                permitido=permitido,
            )
            db.add(nueva)

        count += 1

    db.commit()
    return count


def delete_excepcion(db: Session, usuario_id: int, permiso_id: int) -> bool:
    """
    Elimina una excepción específica de un usuario.
    Al eliminarla, el usuario vuelve a heredar el comportamiento de su rol.
    Retorna True si existía y fue eliminada, False si no existía.
    """
    excepcion = db.query(models.UsuarioPermisoExcepcion).filter(
        models.UsuarioPermisoExcepcion.usuario_id == usuario_id,
        models.UsuarioPermisoExcepcion.permiso_id == permiso_id,
    ).first()

    if not excepcion:
        return False

    db.delete(excepcion)
    db.commit()
    return True


def clear_all_excepciones(db: Session, usuario_id: int) -> int:
    """
    Elimina TODAS las excepciones de un usuario.
    Usado cuando el admin quiere "resetear" al usuario a su rol puro.
    Retorna la cantidad de excepciones eliminadas.
    """
    deleted = db.query(models.UsuarioPermisoExcepcion).filter(
        models.UsuarioPermisoExcepcion.usuario_id == usuario_id
    ).delete(synchronize_session=False)
    db.commit()
    return deleted
