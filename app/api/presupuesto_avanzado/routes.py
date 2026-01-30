from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import presupuesto_avanzado as service
from app.schemas import presupuesto_avanzado as schemas
from app.models import Usuario as models_usuario
from app.core.security import get_current_user

router = APIRouter()

# --- ESCENARIOS ---

@router.get("/escenarios", response_model=List[schemas.Escenario])
def get_escenarios(
    empresa_id: Optional[int] = None, # Opcional filter en query, pero obligatorio logicamente
    anio: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    # Si no pasa empresa_id, usa la del usuario
    e_id = empresa_id if empresa_id else current_user.empresa_id
    if not e_id:
         raise HTTPException(status_code=400, detail="Empresa ID requerido")
         
    return service.get_escenarios(db, e_id, anio)

@router.post("/escenarios", response_model=schemas.Escenario)
def create_escenario(
    data: schemas.EscenarioCreate,
    empresa_id: Optional[int] = None, # Query param override
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    e_id = empresa_id if empresa_id else current_user.empresa_id
    if not e_id:
         raise HTTPException(status_code=400, detail="Empresa ID requerido")
         
    return service.create_escenario(db, e_id, data, current_user.id)

@router.put("/escenarios/{escenario_id}", response_model=schemas.Escenario)
def update_escenario(
    escenario_id: int,
    data: schemas.EscenarioUpdate,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    # TODO: Validar ownership de empresa
    updated = service.update_escenario(db, escenario_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Escenario no encontrado")
    return updated

@router.delete("/escenarios/{escenario_id}")
def delete_escenario(
    escenario_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    success = service.delete_escenario(db, escenario_id)
    if not success:
         raise HTTPException(status_code=404, detail="Escenario no encontrado")
    return {"status": "success", "message": "Escenario eliminado"}

# --- PROYECCIÓN ---

@router.post("/escenarios/{escenario_id}/proyectar")
def proyectar_escenario(
    escenario_id: int,
    base_year: int,
    metodo: schemas.MetodoProyeccion,
    factor: float = 0,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    """
    Ejecuta el motor de proyección para llenar/actualizar los items del escenario
    basado en datos históricos.
    """
    result = service.proyectar_escenario_automatico(db, escenario_id, base_year, metodo, factor)
    if not result:
         raise HTTPException(status_code=404, detail="Escenario no encontrado")
    return result

# --- ITEMS ---

@router.get("/escenarios/{escenario_id}/items", response_model=List[schemas.PresupuestoItem])
def get_items(
    escenario_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    return service.get_items_escenario(db, escenario_id)

@router.put("/items/{item_id}", response_model=schemas.PresupuestoItem)
def update_item(
    item_id: int,
    data: schemas.PresupuestoItemUpdate,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    item = service.update_item_manual(db, item_id, data)
    if not item:
         raise HTTPException(status_code=404, detail="Item no encontrado")
    return item

# --- EJECUCIÓN ---

@router.get("/escenarios/{escenario_id}/ejecucion", response_model=schemas.ReporteEjecucion)
def get_reporte_ejecucion(
    escenario_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    reporte = service.calcular_ejecucion_comparativa(db, escenario_id)
    if not reporte:
         raise HTTPException(status_code=404, detail="Escenario no encontrado")
    return reporte

# --- PDF REPORTS ---

from app.services import pdf_presupuesto as pdf_service
from app.core.security import create_signed_token, validate_signed_token

@router.get("/escenarios/{escenario_id}/pdf-token")
def get_pdf_token(
    escenario_id: int,
    current_user: models_usuario = Depends(get_current_user)
):
    """Genera un token de corta duración (30s) para descargar el PDF."""
    token = create_signed_token(data=str(escenario_id), salt="presupuesto_pdf", max_age=30)
    return {"token": token}

@router.get("/escenarios/{escenario_id}/pdf")
def get_presupuesto_pdf(
    escenario_id: int,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # 1. Validar Token (Prioridad para Navegador)
    if token:
        valid_id = validate_signed_token(token, salt="presupuesto_pdf", max_age=30)
        if not valid_id or int(valid_id) != escenario_id:
            raise HTTPException(status_code=401, detail="Token PDF inválido o expirado")
        # Access Granted via Token
        return pdf_service.generate_pdf_matriz_presupuesto(db, escenario_id)
        
    # 2. Si no hay token, rechazar (o implementar lógica manual de Header si fuera necesario)
    raise HTTPException(status_code=401, detail="Se requiere token de descarga (flujo seguro)")

@router.get("/escenarios/{escenario_id}/ejecucion/pdf")
def get_ejecucion_pdf(
    escenario_id: int,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # 1. Validar Token
    if token:
        valid_id = validate_signed_token(token, salt="presupuesto_pdf", max_age=30)
        if not valid_id or int(valid_id) != escenario_id:
            raise HTTPException(status_code=401, detail="Token PDF inválido o expirado")
        return pdf_service.generate_pdf_ejecucion(db, escenario_id)
        
    raise HTTPException(status_code=401, detail="Se requiere token de descarga (flujo seguro)")
