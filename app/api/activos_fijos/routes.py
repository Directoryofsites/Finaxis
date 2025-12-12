from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ...core.database import get_db
from ...core.security import get_current_user
from ...models.usuario import Usuario
from ...schemas import activo_fijo as schemas
from ...services import activo_fijo as service

from ...services import activo_fijo as service
from ...models.documento import Documento # Para retorno
from pydantic import BaseModel

router = APIRouter()

class DepreciacionRequest(BaseModel):
    anio: int
    mes: int
    tipo_documento_id: int

# --- CATEGORIAS ---

@router.post("/categorias", response_model=schemas.ActivoCategoria, status_code=status.HTTP_201_CREATED)
def crear_categoria(
    categoria: schemas.ActivoCategoriaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return service.create_categoria(db, categoria, current_user.empresa_id)

@router.get("/categorias", response_model=List[schemas.ActivoCategoria])
def listar_categorias(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return service.get_categorias(db, current_user.empresa_id, skip, limit)

# --- ACTIVOS FIJOS ---

@router.post("/", response_model=schemas.ActivoFijo, status_code=status.HTTP_201_CREATED)
def crear_activo(
    activo: schemas.ActivoFijoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return service.create_activo(db, activo, current_user.id, current_user.empresa_id)

@router.get("/", response_model=List[schemas.ActivoFijo])
def listar_activos(
    skip: int = 0,
    limit: int = 100,
    categoria_id: Optional[int] = None,
    responsable_id: Optional[int] = None,
    estado: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return service.get_activos(
        db, 
        current_user.empresa_id, 
        skip, limit,
        categoria_id, responsable_id, estado, q
    )

@router.get("/{id}", response_model=schemas.ActivoFijo)
def obtener_activo(
    id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    activo = service.get_activo_by_id(db, id, current_user.empresa_id)
    if not activo:
        raise HTTPException(status_code=404, detail="Activo no encontrado")
    return activo

@router.put("/{id}", response_model=schemas.ActivoFijo)
def actualizar_activo(
    id: int,
    activo_update: schemas.ActivoFijoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    db_activo = service.update_activo(db, id, activo_update, current_user.empresa_id)
    if not db_activo:
        raise HTTPException(status_code=404, detail="Activo no encontrado")
    return db_activo

@router.post("/depreciar", status_code=status.HTTP_201_CREATED)
def ejecutar_depreciacion_route(
    req: DepreciacionRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Ejecuta el proceso de depreciación masiva para el mes/año indicados.
    Genera un documento contable automático.
    """
    documento = service.ejecutar_depreciacion(
        db, 
        current_user.empresa_id, 
        req.anio, 
        req.mes, 
        current_user.id, 
        req.tipo_documento_id
    )
    return {"mensaje": "Depreciación exitosa", "documento_id": documento.id, "numero": documento.numero}

# --- REPORTES PDF ---

@router.get("/reportes/maestro-pdf")
def generar_reporte_maestro_pdf(
    categoria_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Genera PDF con el reporte maestro de activos fijos
    """
    from ...services.pdf_activos_fijos import generar_reporte_maestro_activos
    from fastapi.responses import StreamingResponse
    
    buffer = generar_reporte_maestro_activos(db, current_user.empresa_id, categoria_id)
    
    return StreamingResponse(
        io.BytesIO(buffer.read()),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=reporte_maestro_activos.pdf"}
    )

@router.get("/reportes/depreciacion-pdf")
def generar_reporte_depreciacion_pdf(
    anio: int,
    mes: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Genera PDF con el reporte de depreciación mensual
    """
    from ...services.pdf_activos_fijos import generar_reporte_depreciacion_mensual
    from fastapi.responses import StreamingResponse
    import io
    
    buffer = generar_reporte_depreciacion_mensual(db, current_user.empresa_id, anio, mes)
    
    return StreamingResponse(
        io.BytesIO(buffer.read()),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=depreciacion_{mes:02d}_{anio}.pdf"}
    )

@router.get("/{id}/hoja-vida-pdf")
def generar_hoja_vida_pdf(
    id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Genera PDF con la hoja de vida completa de un activo
    """
    from ...services.pdf_activos_fijos import generar_hoja_vida_activo
    from fastapi.responses import StreamingResponse
    import io
    
    buffer = generar_hoja_vida_activo(db, id, current_user.empresa_id)
    
    activo = service.get_activo_by_id(db, id, current_user.empresa_id)
    filename = f"hoja_vida_{activo.codigo}.pdf" if activo else "hoja_vida_activo.pdf"
    
    return StreamingResponse(
        io.BytesIO(buffer.read()),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

