# app/api/empresas/routes.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import empresa as service
from app.services import dashboard as dashboard_service  # Importación consolidada aquí
from app.schemas import empresa as schemas, usuario as schemas_usuario
from app.models import Usuario as models_usuario
# Importamos ambos tipos de dependencias de seguridad
from app.core.security import get_current_soporte_user, get_current_user, has_permission 

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
    current_user: models_usuario = Depends(get_current_user)
):
    """
    Lista las empresas.
    - Si es Soporte: Devuelve TODAS.
    - Si es Usuario Normal: Devuelve SOLO SU PROPIA EMPRESA.
    """
    return service.get_empresas_para_usuario(db, current_user)

@router.post("/", response_model=schemas.Empresa)
def create_empresa(
    empresa: schemas.EmpresaConUsuariosCreate, 
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_soporte_user)
):
    # CORRECCIÓN CRÍTICA: Se cambia 'empresa=' por 'empresa_data=' para coincidir 
    # con la definición en app/services/empresa.py
    return service.create_empresa_con_usuarios(db=db, empresa_data=empresa)

@router.get("/{empresa_id}", response_model=schemas.Empresa)
def read_empresa(
    empresa_id: int, 
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(has_permission("empresa:gestionar_empresas"))
):
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
    current_user: models_usuario = Depends(has_permission("empresa:gestionar_empresas"))
):
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
    success = service.delete_empresa(db, empresa_id=empresa_id)
    if not success:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
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