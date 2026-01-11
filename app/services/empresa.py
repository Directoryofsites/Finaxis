# app/services/empresa.py
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from ..models.cupo_adicional import CupoAdicional

# Se importan todos los modelos necesarios para una limpieza completa
from ..models import (
    empresa as empresa_model,
    usuario as usuario_model,
    log_operacion as log_operacion_model,
    documento as documento_model,
    tercero as tercero_model,
    plan_cuenta as plan_cuenta_model,
    centro_costo as centro_costo_model,
    tipo_documento as tipo_documento_model,
    permiso as permiso_model,
    periodo_contable_cerrado as periodo_cerrado_model
)

from ..schemas import empresa as empresa_schema, usuario as usuario_schema

# --- CREACIÓN ---
def create_empresa_con_usuarios(db: Session, empresa_data: empresa_schema.EmpresaConUsuariosCreate) -> empresa_model.Empresa:
    db_empresa_existente = db.query(empresa_model.Empresa).filter(empresa_model.Empresa.nit == empresa_data.nit).first()
    if db_empresa_existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Ya existe una empresa con el NIT {empresa_data.nit}")
    
    emails_a_crear = [user.email for user in empresa_data.usuarios]
    db_usuarios_existentes = db.query(usuario_model.Usuario).filter(usuario_model.Usuario.email.in_(emails_a_crear)).all()
    if db_usuarios_existentes:
        emails_existentes = [user.email for user in db_usuarios_existentes]
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Los siguientes emails ya existen: {', '.join(emails_existentes)}")

    try:
        nueva_empresa = empresa_model.Empresa(
            razon_social=empresa_data.razon_social, 
            nit=empresa_data.nit,
            fecha_inicio_operaciones=empresa_data.fecha_inicio_operaciones, 
            # --- NUEVOS CAMPOS AÑADIDOS AQUÍ ---
            direccion=empresa_data.direccion,
            telefono=empresa_data.telefono,
            email=empresa_data.email,

            logo_url=empresa_data.logo_url,
            modo_operacion=empresa_data.modo_operacion, # <--- FALTABA ESTO
            # -----------------------------------
            created_at=datetime.utcnow()
        )
        db.add(nueva_empresa)
        db.flush()

        # Buscamos el rol con el nombre correcto en minúscula, tal como lo crea el seeder.
        # Buscamos el rol adecuado según el modo de operación
        if empresa_data.modo_operacion == 'AUDITORIA_READONLY':
             rol_nombre = "clon_restringido"
        else:
             rol_nombre = "administrador"

        # 3. Asignar Rol al Usuario
        rol_asignar = None

        # PRIORIDAD: Si se especifica ID de rol manualmente (nueva funcionalidad), usar ese.
        if empresa_data.rol_inicial_id:
            rol_asignar = db.query(permiso_model.Rol).filter(permiso_model.Rol.id == empresa_data.rol_inicial_id).first()
            if not rol_asignar:
                 db.rollback()
                 raise HTTPException(status_code=400, detail=f"El Rol Inicial ID {empresa_data.rol_inicial_id} no existe.")

        # FALLBACK: Si no se especifica, usar el nombre por defecto
        if not rol_asignar:
            admin_role = db.query(permiso_model.Rol).filter(permiso_model.Rol.nombre == rol_nombre).first()
            # Renombramos variable para usarla abajo consistentemente
            rol_asignar = admin_role

        if not rol_asignar:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"CRÍTICO: El rol '{rol_nombre}' no está definido en la base de datos.")

        for usuario_data in empresa_data.usuarios:
            from . import usuario as usuario_service
            # Asignar rol seleccionado (o default)
            user_payload = usuario_schema.UserCreateInCompany(
                email=usuario_data.email, password=usuario_data.password, roles_ids=[rol_asignar.id]
            )
            usuario_service.create_user_in_company(db=db, user_data=user_payload, empresa_id=nueva_empresa.id)
        
        db.commit()
        db.refresh(nueva_empresa)
        return nueva_empresa
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error de integridad de datos: {e.orig}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Un error inesperado ocurrió: {str(e)}")

# --- ACTUALIZACIÓN (AQUÍ ESTABA EL PROBLEMA) ---
def update_empresa(db: Session, empresa_id: int, empresa: empresa_schema.EmpresaUpdate) -> empresa_model.Empresa:
    # Nota: Renombré el argumento 'empresa_data' a 'empresa' para coincidir con la llamada del router.
    db_empresa = get_empresa_by_id(db, empresa_id=empresa_id)
    if not db_empresa:
        return None # El router manejará el 404
    
    # Usamos model_dump(exclude_unset=True) para actualizar solo lo que envió el usuario
    try:
        update_data = empresa.model_dump(exclude_unset=True)
    except AttributeError:
        # Fallback para versiones viejas de Pydantic
        update_data = empresa.dict(exclude_unset=True)

    for key, value in update_data.items():
        if hasattr(db_empresa, key):
            setattr(db_empresa, key, value)

    db.add(db_empresa)
    db.commit()
    db.refresh(db_empresa)
    return db_empresa

# --- GETTERS ---
def get_empresas(db: Session, skip: int = 0, limit: int = 100):
    """Devuelve la lista de todas las empresas (Paginada)."""
    return db.query(empresa_model.Empresa).offset(skip).limit(limit).all()

def get_empresa(db: Session, empresa_id: int):
    """Alias para get_empresa_by_id, requerido por el router."""
    return get_empresa_by_id(db, empresa_id)

def get_empresa_by_id(db: Session, empresa_id: int) -> Optional[empresa_model.Empresa]:
    return db.query(empresa_model.Empresa).filter(empresa_model.Empresa.id == empresa_id).first()

def get_empresas_para_usuario(db: Session, current_user: usuario_model.Usuario) -> List[empresa_model.Empresa]:
    user_roles = {rol.nombre for rol in current_user.roles} if current_user.roles else set()
    if "soporte" in user_roles:
        return db.query(empresa_model.Empresa).order_by(empresa_model.Empresa.razon_social).all()
    empresa_usuario = db.query(empresa_model.Empresa).filter(empresa_model.Empresa.id == current_user.empresa_id).first()
    return [empresa_usuario] if empresa_usuario else []

def get_usuarios_by_empresa_id(db: Session, empresa_id: int) -> List[usuario_model.Usuario]:
    return db.query(usuario_model.Usuario).options(
        joinedload(usuario_model.Usuario.roles)
    ).filter(
        usuario_model.Usuario.empresa_id == empresa_id
    ).order_by(
        usuario_model.Usuario.email
    ).all()

# --- OTROS UPDATES ---
def update_limite_registros(db: Session, empresa_id: int, limite_data: empresa_schema.EmpresaLimiteUpdate) -> empresa_model.Empresa:
    db_empresa = get_empresa_by_id(db, empresa_id=empresa_id)
    if not db_empresa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa no encontrada para actualizar el límite.")
    db_empresa.limite_registros = limite_data.limite_registros
    db.add(db_empresa)
    db.commit()
    db.refresh(db_empresa)
    return db_empresa

# --- BORRADO ---
def delete_empresa(db: Session, empresa_id: int):
    """Alias para delete_empresa_y_usuarios, adaptado para devolver bool."""
    try:
        delete_empresa_y_usuarios(db, empresa_id)
        return True
    except HTTPException:
        # Si delete_empresa_y_usuarios lanza excepción (ej: por tener documentos), la propagamos
        raise 
    except Exception:
        return False

def delete_empresa_y_usuarios(db: Session, empresa_id: int):
    db_empresa = get_empresa_by_id(db, empresa_id=empresa_id)
    if not db_empresa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No se encontró una empresa con el id {empresa_id}")
    
    documento_existente = db.query(documento_model.Documento).filter(documento_model.Documento.empresa_id == empresa_id).first()
    if documento_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Esta empresa no se puede eliminar porque tiene documentos contables históricos. Utilice el 'Erradicador Universal' para una eliminación forzada."
        )
    try:
        # Borrado en cascada manual (seguridad adicional)
        db.query(plan_cuenta_model.PlanCuenta).filter(plan_cuenta_model.PlanCuenta.empresa_id == empresa_id).delete(synchronize_session=False)
        db.query(tercero_model.Tercero).filter(tercero_model.Tercero.empresa_id == empresa_id).delete(synchronize_session=False)
        db.query(centro_costo_model.CentroCosto).filter(centro_costo_model.CentroCosto.empresa_id == empresa_id).delete(synchronize_session=False)
        db.query(tipo_documento_model.TipoDocumento).filter(tipo_documento_model.TipoDocumento.empresa_id == empresa_id).delete(synchronize_session=False)
        db.query(periodo_cerrado_model.PeriodoContableCerrado).filter(periodo_cerrado_model.PeriodoContableCerrado.empresa_id == empresa_id).delete(synchronize_session=False)
        db.query(log_operacion_model.LogOperacion).filter(log_operacion_model.LogOperacion.empresa_id == empresa_id).delete(synchronize_session=False)
        
        # --- FIX FK VIOLATION: Eliminar roles asignados a los usuarios primero ---
        # 1. Obtenemos los IDs de usuarios de la empresa
        usuarios_ids = db.query(usuario_model.Usuario.id).filter(usuario_model.Usuario.empresa_id == empresa_id).all()
        usuarios_ids = [uid[0] for uid in usuarios_ids]
        
        if usuarios_ids:
            # 2. Eliminamos manualmente de la tabla intermedia usuario_roles
            # Importamos la tabla intermedia desde el modelo
            from ..models.usuario import usuario_roles
            db.execute(usuario_roles.delete().where(usuario_roles.c.usuario_id.in_(usuarios_ids)))
        
        # 3. Ahora sí podemos borrar los usuarios
        db.query(usuario_model.Usuario).filter(usuario_model.Usuario.empresa_id == empresa_id).delete(synchronize_session=False)
        # ------------------------------------------------------------------------
        
        db.delete(db_empresa)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Un error inesperado ocurrió durante la limpieza en cascada: {str(e)}")
    


def agregar_cupo_adicional(db: Session, empresa_id: int, datos: empresa_schema.CupoAdicionalCreate):
    # 1. Buscar si ya existe un adicional para ese mes/año
    cupo_existente = db.query(CupoAdicional).filter(
        CupoAdicional.empresa_id == empresa_id,
        CupoAdicional.anio == datos.anio,
        CupoAdicional.mes == datos.mes
    ).first()

    if cupo_existente:
        # Si existe, sumamos o actualizamos (Estrategia: Actualizar el total)
        cupo_existente.cantidad_adicional = datos.cantidad_adicional
        db.add(cupo_existente)
    else:
        # Si no, creamos uno nuevo
        nuevo_cupo = CupoAdicional(
            empresa_id=empresa_id,
            anio=datos.anio,
            mes=datos.mes,
            cantidad_adicional=datos.cantidad_adicional
        )
        db.add(nuevo_cupo)
    
    db.commit()
    return True