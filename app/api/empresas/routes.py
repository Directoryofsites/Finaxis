# app/api/empresas/routes.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import empresa as service
from app.services import dashboard as dashboard_service  # Importación consolidada aquí
from app.schemas import empresa as schemas, usuario as schemas_usuario
from app.models import Usuario as models_usuario
# Importamos ambos tipos de dependencias de seguridad
from app.core.security import get_current_soporte_user, get_current_user, has_permission, get_user_permissions 

router = APIRouter()

# --- FUNCION AUXILIAR DE PERMISOS ---
def verificar_permiso_empresa(usuario: models_usuario, empresa_id: int):
    """
    Permite el paso si:
    1. El usuario es rol 'soporte'.
    2. O el usuario pertenece a la empresa que intenta editar.
    """
    es_soporte = any(r.nombre == 'soporte' for r in usuario.roles)
    pertenece_a_empresa = (usuario.empresa_id == empresa_id)
    
    if not es_soporte and not pertenece_a_empresa:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para gestionar esta empresa."
        )

@router.get("/", response_model=List[schemas.Empresa])
def read_empresas(
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user),
    mes: Optional[int] = None,
    anio: Optional[int] = None
):
    """
    Lista las empresas.
    - Si es Soporte: Devuelve TODAS.
    - Si es Usuario Normal: Devuelve SOLO SU PROPIA EMPRESA.
    - mes/anio: Opcionales para calcular consumo histórico.
    """
    return service.get_empresas_para_usuario(db, current_user, mes, anio)

@router.get("/templates", response_model=List[schemas.Empresa])
def read_templates(
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    """
    Obtiene la lista de plantillas disponibles (Globales + Privadas).
    """
    return service.get_templates(db, current_user)

@router.post("/", response_model=schemas.Empresa)
def create_empresa(
    empresa: schemas.EmpresaConUsuariosCreate, 
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    # 1. Autorización y Contexto (Soporte vs Contador)
    user_roles = {r.nombre for r in current_user.roles}
    is_soporte = "soporte" in user_roles
    is_contador = "contador" in user_roles
    
    if not is_soporte and not is_contador:
         raise HTTPException(status_code=403, detail="No tiene permisos para crear empresas.")
         
    padre_id = None
    owner_id = None
    
    if is_contador:
        # El contador crea empresas HIJAS de su Holding (si la tiene) o de sí mismo (si es freelance)
        # Asumimos que la 'empresa_id' del usuario contador es su Holding.
        padre_id = current_user.empresa_id 
        owner_id = current_user.id
        
    # 2. Lógica de Creación (Plantilla vs Standard)
    # Support both category (legacy) and ID (new)
    if empresa.template_category or empresa.template_id:
        return service.create_empresa_from_template(
            db=db,
            empresa_data=empresa,
            template_category=empresa.template_category, # Service will handle None if ID is present
            owner_id=owner_id,
            padre_id=padre_id
        )
    
    # Fallback Standard (Solo Soporte debería usar esto para empresas sin molde)
    return service.create_empresa_con_usuarios(db=db, empresa_data=empresa, owner_id=owner_id, padre_id=padre_id)

@router.post("/{empresa_id}/extract-template", response_model=schemas.Empresa)
def extract_template(
    empresa_id: int,
    payload: schemas.TemplateExtraction,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    """
    Convierte la configuración de una empresa existente en una nueva Plantilla.
    Si es Contador, la plantilla será Privada (owner_id = current_user).
    Si es Soporte, la plantilla será Pública (owner_id = None) o asignada según lógica.
    """
    # 1. Permisos
    verificar_permiso_empresa(current_user, empresa_id)
    
    user_roles = {r.nombre for r in current_user.roles}
    is_soporte = "soporte" in user_roles
    
    # 2. Definir Dueño de la Plantilla
    new_template_owner = None
    if not is_soporte:
        # Si es contador, la plantilla es SUYA.
        new_template_owner = current_user.id
        
    # 3. Llamar al servicio de clonación
    try:
        nueva_plantilla = service.create_template_from_existing(
            db=db,
            source_empresa_id=empresa_id,
            template_category=payload.category,
            owner_id=new_template_owner,
            custom_name=payload.name
        )
        return nueva_plantilla
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando plantilla: {str(e)}")

@router.get("/{empresa_id}", response_model=schemas.Empresa)
def read_empresa(
    empresa_id: int, 
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    # Validamos permiso manualmente para permitir Soporte
    # Validamos permiso: Soporte O Permiso Gestión O Es Su Propia Empresa
    is_soporte = any(r.nombre == 'soporte' for r in current_user.roles)
    user_permissions = get_user_permissions(current_user)
    has_perm = "empresa:gestionar_empresas" in user_permissions
    es_su_empresa = (current_user.empresa_id == empresa_id)
    
    if not is_soporte and not has_perm and not es_su_empresa:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: No tiene permisos para ver esta empresa."
        )

    verificar_permiso_empresa(current_user, empresa_id)
    
    db_empresa = service.get_empresa(db, empresa_id=empresa_id)
    if db_empresa is None:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return db_empresa

@router.put("/{empresa_id}", response_model=schemas.Empresa)
def update_empresa(
    empresa_id: int, 
    empresa: schemas.EmpresaUpdate, 
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    # Validamos permiso manualmente para permitir Soporte
    # Validamos permiso: Soporte O Permiso Gestión O Es Su Propia Empresa
    is_soporte = any(r.nombre == 'soporte' for r in current_user.roles)
    user_permissions = get_user_permissions(current_user)
    has_perm = "empresa:gestionar_empresas" in user_permissions
    es_su_empresa = (current_user.empresa_id == empresa_id)
    
    if not is_soporte and not has_perm and not es_su_empresa:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: No tiene permisos para editar esta empresa."
        )

    verificar_permiso_empresa(current_user, empresa_id)
    
    db_empresa = service.update_empresa(db, empresa_id=empresa_id, empresa=empresa)
    if db_empresa is None:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return db_empresa

# --- NUEVA RUTA: ACTUALIZAR LÍMITE DE REGISTROS (SOLO SOPORTE) ---
@router.put("/{empresa_id}/limite", response_model=schemas.Empresa)
def update_limite_empresa(
    empresa_id: int,
    limite: schemas.EmpresaLimiteUpdate,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_soporte_user) # Blindado solo para soporte
):
    """
    Actualiza el cupo máximo de registros permitidos para una empresa.
    Exclusivo para el panel de soporte.
    """
    db_empresa = service.update_limite_registros(db, empresa_id=empresa_id, limite_data=limite)
    if not db_empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return db_empresa
# ------------------------------------------------------------------

@router.get("/{empresa_id}/usuarios", response_model=List[schemas.EmpresaConUsuarios])
def read_usuarios_empresa(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    verificar_permiso_empresa(current_user, empresa_id)
    
    empresa = service.get_empresa(db, empresa_id=empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
        
    return empresa.usuarios

@router.post("/{empresa_id}/usuarios", response_model=schemas_usuario.User)
def create_usuario_empresa(
    empresa_id: int,
    user_data: schemas_usuario.UserCreateInCompany,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    """
    Crea un nuevo usuario asociado directamente a esta empresa.
    """
    verificar_permiso_empresa(current_user, empresa_id)
    
    # Importamos el servicio aquí o arriba, pero como no lo teníamos arriba:
    from app.services import usuario as usuario_service
    
    return usuario_service.create_user_in_company(db=db, user_data=user_data, empresa_id=empresa_id)

@router.delete("/{empresa_id}")
def delete_empresa(
    empresa_id: int, 
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_soporte_user)
):
    # Usamos la versión robusta que limpia referencias complejas (Nómina, PH, etc.)
    service.delete_empresa_y_usuarios(db, empresa_id=empresa_id)
    return {"message": "Empresa eliminada exitosamente"}

@router.post("/{empresa_id}/adicionales")
def set_cupo_adicional(
    empresa_id: int,
    payload: schemas.CupoAdicionalCreate,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_soporte_user) # Solo soporte
):
    service.agregar_cupo_adicional(db, empresa_id, payload)
    return {"message": "Cupo adicional actualizado correctamente"}

@router.get("/{empresa_id}/consumo")
def read_consumo_empresa_periodo(
    empresa_id: int,
    mes: int,
    anio: int,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user) # Permite a soporte o al dueño
):
    """
    Obtiene el consumo y límite REAL (Base o Excepción) de una empresa 
    para un periodo específico.
    """
    # Validamos permisos (Soporte o Dueño)
    verificar_permiso_empresa(current_user, empresa_id)
    
    # Reutilizamos la lógica maestra del dashboard
    return dashboard_service.get_consumo_actual(db, empresa_id, mes, anio)



# ------------------------------------------------------------------
# NUEVO: ACTUALIZAR PLAN MENSUAL ESPECÍFICO (MANUAL OVERRIDE)
# ------------------------------------------------------------------
class PlanMensualUpdate(schemas.BaseModel):
    anio: int
    mes: int
    limite: int
    es_manual: bool = True

@router.put("/{empresa_id}/plan-mensual")
def update_plan_mensual_manual(
    empresa_id: int,
    data: PlanMensualUpdate,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_soporte_user)
):
    """
    Permite fijar manualmente el límite de un mes específico, 
    bypassando la lógica automática de sincronización.
    """
    from app.models.consumo_registros import ControlPlanMensual, EstadoPlan
    
    # Buscar o crear el plan (la función _get_or_create ya existe en consumo_service, 
    # pero aquí queremos editarlo directamente).
    # Hacemos query directa para ser explícitos en la edición.
    plan = db.query(ControlPlanMensual).filter(
        ControlPlanMensual.empresa_id == empresa_id,
        ControlPlanMensual.anio == data.anio,
        ControlPlanMensual.mes == data.mes
    ).first()
    
    if not plan:
        # Si no existe, lo creamos manualmente
        plan = ControlPlanMensual(
            empresa_id=empresa_id,
            anio=data.anio,
            mes=data.mes,
            limite_asignado=data.limite,
            cantidad_disponible=data.limite, # Asumimos full o calculamos consumo?
            estado=EstadoPlan.ABIERTO,
            es_manual=data.es_manual
        )
        db.add(plan)
        # Deberíamos restar el consumo real si ya hubo? Sí, para ser consistentes.
        # Pero por simplicidad inicial, dejemos que el auto-healing DE CANTIDAD (no limite) actúe después
        # O llamamos a _get_or_create primero.
    else:
        plan.limite_asignado = data.limite
        plan.es_manual = data.es_manual
        # La cantidad disponible se debería ajustar proporcionalmente o recalcular
        # Llamaremos a una lógica de ajuste simple aquí
        # Ojo: No podemos importar services.consumo si causa ciclo, pero intentemos evitarlo.
    
    db.commit()
    db.refresh(plan)
    return {"status": "success", "limite_asignado": plan.limite_asignado, "es_manual": plan.es_manual}

# --- BLOQUE AÑADIDO: CONFIGURACIÓN DE PRECIOS POR EMPRESA ---
@router.get("/{empresa_id}/config-precio")
def get_precio_empresa_endpoint(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_soporte_user)
):
    """
    Obtiene la configuración de precio de una empresa específica.
    """
    from app.models.configuracion_sistema import ConfiguracionSistema
    from sqlalchemy import inspect
    
    db_empresa = service.get_empresa(db, empresa_id=empresa_id)
    if db_empresa is None:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
        
    global_price = 150
    if inspect(db.get_bind()).has_table("configuracion_sistema"):
         config = db.query(ConfiguracionSistema).filter_by(clave="PRECIO_POR_REGISTRO").first()
         if config: global_price = int(config.valor)
         
    return {
        "precio_personalizado": db_empresa.precio_por_registro,
        "precio_global": global_price,
        "precio_efectivo": db_empresa.precio_por_registro if db_empresa.precio_por_registro else global_price
    }

@router.put("/{empresa_id}/config-precio")
def update_precio_empresa_endpoint(
    empresa_id: int,
    data: dict, 
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_soporte_user)
):
    """
    Actualiza el precio por registro específico para esta empresa.
    """
    db_empresa = service.get_empresa(db, empresa_id=empresa_id)
    if not db_empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
        
    nuevo_precio = data.get("precio")
    if nuevo_precio is not None:
        try:
            nuevo_precio = int(nuevo_precio)
            if nuevo_precio < 0: raise ValueError
        except:
             raise HTTPException(status_code=400, detail="El precio debe ser un entero positivo.")
             
    db_empresa.precio_por_registro = nuevo_precio
    db.commit()
    db.refresh(db_empresa)
    
    return {"msg": "Configuración de precio actualizada", "nuevo_precio": nuevo_precio}

# --- TEMPORARY FIX ENDPOINT ---
@router.get("/fix-quota/{empresa_id}")
def fix_quota_manual_internal(
    empresa_id: int,
    db: Session = Depends(get_db)
):
    from app.models.empresa import Empresa
    from app.models.consumo_registros import ControlPlanMensual
    from datetime import datetime
    
    # 1. Update Master Limit
    empresa = db.query(Empresa).get(empresa_id)
    if not empresa: return {"error": "Empresa no encontrada"}
    
    limit_was = empresa.limite_registros
    empresa.limite_registros = 1800
    empresa.limite_registros_mensual = 1800
    db.add(empresa)
    
    # 2. Delete Current Plan (Nuclear Reset)
    now = datetime.now()
    plan = db.query(ControlPlanMensual).filter(
        ControlPlanMensual.empresa_id == empresa_id,
        ControlPlanMensual.anio == now.year,
        ControlPlanMensual.mes == now.month
    ).first()
    
    deleted_msg = "No plan found"
    if plan:
        deleted_msg = f"Plan {plan.id} deleted. Was: Lim={plan.limite_asignado} Avail={plan.cantidad_disponible}"
        db.delete(plan)
        
    db.commit()
    
    return {
        "status": "FIX APPLIED",
        "empresa": empresa.razon_social,
        "master_limit_before": limit_was,
        "master_limit_now": 1800,
        "reset_action": deleted_msg,
        "message": "Quota system reset. Please refresh your page and try to save."
    }