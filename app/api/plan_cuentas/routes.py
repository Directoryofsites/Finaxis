from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.services import plan_cuenta as services_plan
from app.schemas import plan_cuenta as schemas_plan
from app.models import Usuario as models_usuario
from app.core.security import get_current_user, has_permission

router = APIRouter()

@router.post("/", response_model=schemas_plan.PlanCuenta, status_code=status.HTTP_201_CREATED)
def create_cuenta(
    cuenta_input: schemas_plan.PlanCuentaInput,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(has_permission("contabilidad:gestionar_puc"))
):
    """
    Crea una nueva cuenta. La lógica de validación, cálculo de nivel y
    verificación de duplicados está completamente delegada al servicio.
    """
    # 1. Preparamos el objeto de datos completo que espera el servicio.
    cuenta_data = schemas_plan.PlanCuentaCreate(
        **cuenta_input.model_dump(),
        empresa_id=current_user.empresa_id,
        nivel=0 # El nivel real se calculará dentro del servicio.
    )
    
    # 2. Llamamos al servicio inteligente.
    # El servicio se encargará de todo: validar el padre, calcular el nivel, etc.
    # Si algo falla, el servicio lanzará la HTTPException correspondiente.
    return services_plan.create_cuenta(db=db, cuenta=cuenta_data, user_id=current_user.id)

@router.put("/{cuenta_id}", response_model=schemas_plan.PlanCuenta)
def update_cuenta(
    cuenta_id: int,
    cuenta_update: schemas_plan.PlanCuentaUpdate,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(has_permission("contabilidad:gestionar_puc"))
):
    """
    Actualiza una cuenta. La validación de la cuenta padre y otras reglas
    de negocio están completamente delegadas al servicio.
    """
    db_cuenta = services_plan.update_cuenta(
        db=db,
        cuenta_id=cuenta_id,
        cuenta_update=cuenta_update,
        empresa_id=current_user.empresa_id,
        user_id=current_user.id
    )
    if db_cuenta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")
    return db_cuenta

@router.delete("/{cuenta_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cuenta(
    cuenta_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(has_permission("contabilidad:gestionar_puc"))
):
    """
    Elimina una cuenta. La verificación de dependencias (hijos, movimientos)
    está completamente delegada al servicio.
    """
    # El servicio lanzará un 409 Conflict si no se puede borrar.
    deleted_cuenta = services_plan.delete_cuenta(
        db=db,
        cuenta_id=cuenta_id,
        empresa_id=current_user.empresa_id
    )
    
    if deleted_cuenta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")
    
    return

    return

# --- IMPORTACION AVANZADA ---

@router.post("/analizar-importacion", response_model=schemas_plan.AnalisisImportacionResponse)
def analizar_importacion(
    cuentas: List[schemas_plan.ImportarCuentaInput],
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(has_permission("contabilidad:gestionar_puc"))
):
    return services_plan.analizar_importacion_puc(db, cuentas, current_user.empresa_id)

@router.post("/importar-lote", status_code=status.HTTP_201_CREATED)
def importar_lote(
    request: schemas_plan.ImportarLoteRequest,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(has_permission("contabilidad:gestionar_puc"))
):
    return services_plan.importar_cuentas_lote(db, request.cuentas, current_user.empresa_id, current_user.id)

# --- RUTAS DE CONSULTA Y HERRAMIENTAS (SIMPLIFICADAS PERO SIN CAMBIOS DE LÓGICA) ---

@router.get("/analizar-depuracion/{cuenta_id}", response_model=schemas_plan.AnalisisDepuracionResponse)
def analizar_depuracion(
    cuenta_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    return services_plan.analizar_depuracion_jerarquica(
        db=db, 
        cuenta_id=cuenta_id, 
        empresa_id=current_user.empresa_id
    )

@router.post("/ejecutar-depuracion", status_code=status.HTTP_200_OK)
def ejecutar_depuracion(
    request: schemas_plan.EjecucionDepuracionRequest,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(has_permission("contabilidad:gestionar_puc"))
):
    return services_plan.ejecutar_depuracion_jerarquica(
        db=db, 
        ids_a_eliminar=request.ids_a_eliminar, 
        empresa_id=current_user.empresa_id
    )

@router.get("/list-flat", response_model=List[schemas_plan.PlanCuentaSimple])
def get_plan_cuentas_flat(
    permite_movimiento: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    cuentas = services_plan.get_plan_cuentas_flat(
        db, 
        empresa_id=current_user.empresa_id, 
        permite_movimiento=permite_movimiento
    )
    return cuentas

@router.get("/", response_model=List[schemas_plan.PlanCuenta])
def read_cuentas(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    return services_plan.get_cuentas(db, empresa_id=current_user.empresa_id, skip=skip, limit=limit)

@router.get("/{cuenta_id}", response_model=schemas_plan.PlanCuenta)
def read_cuenta(
    cuenta_id: int, db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    db_cuenta = services_plan.get_cuenta(db, cuenta_id=cuenta_id, empresa_id=current_user.empresa_id)
    if db_cuenta is None:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    return db_cuenta

@router.get("/codigo/{codigo}", response_model=schemas_plan.PlanCuenta)
def get_cuenta_by_codigo(
    codigo: str, db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    db_cuenta = services_plan.get_cuenta_by_codigo(db, codigo=codigo, empresa_id=current_user.empresa_id)
    if db_cuenta is None:
        raise HTTPException(status_code=404, detail=f"Cuenta con código {codigo} no encontrada")
    return db_cuenta