from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Usuario
from app.schemas.propiedad_horizontal import unidad as schemas
from app.schemas.propiedad_horizontal import configuracion as config_schemas
from app.schemas.propiedad_horizontal import modulo_contribucion as modulo_schemas
from app.services.propiedad_horizontal import unidad_service, configuracion_service, facturacion_service, pago_service, reportes as reportes_service, modulo_service

from . import conceptos

router = APIRouter()
router.include_router(conceptos.router)

# --- MÓDULOS DE CONTRIBUCIÓN (PH Mixta) ---

@router.get("/modulos", response_model=List[modulo_schemas.PHModuloContribucionResponse])
def listar_modulos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return modulo_service.get_modulos(db, current_user.empresa_id)

@router.post("/modulos", response_model=modulo_schemas.PHModuloContribucionResponse)
def crear_modulo(
    modulo: modulo_schemas.PHModuloContribucionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return modulo_service.create_modulo(db, modulo, current_user.empresa_id)

@router.put("/modulos/{id}", response_model=modulo_schemas.PHModuloContribucionResponse)
def actualizar_modulo(
    id: int,
    modulo: modulo_schemas.PHModuloContribucionUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return modulo_service.update_modulo(db, id, modulo, current_user.empresa_id)

@router.delete("/modulos/{id}")
def eliminar_modulo(
    id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return modulo_service.delete_modulo(db, id, current_user.empresa_id)

# --- REQUEST SCHEMAS ---
class ConceptoConfiguracion(BaseModel):
    concepto_id: int
    unidades_ids: List[int]

class FacturacionMasivaRequest(BaseModel):
    fecha: date
    conceptos_ids: Optional[List[int]] = None
    configuracion_conceptos: Optional[List[ConceptoConfiguracion]] = None

class PagoRequest(BaseModel):
    unidad_id: int
    monto: float
    fecha: date
    forma_pago_id: int = None # Opcional por ahora

# --- UNIDADES ---

@router.get("/unidades/propietarios")
def listar_propietarios_directorio(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Retorna el directorio consolidado de propietarios (Terceros con Unidades).
    """
    return unidad_service.get_propietarios_resumen(db, current_user.empresa_id)

@router.get("/unidades", response_model=List[schemas.PHUnidad])
def listar_unidades(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return unidad_service.get_unidades(db, empresa_id=current_user.empresa_id, skip=skip, limit=limit)

@router.post("/unidades", response_model=schemas.PHUnidad, status_code=status.HTTP_201_CREATED)
def crear_unidad(
    unidad: schemas.PHUnidadCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return unidad_service.crear_unidad(db, unidad, empresa_id=current_user.empresa_id)

@router.get("/unidades/{unidad_id}", response_model=schemas.PHUnidad)
def ver_unidad(
    unidad_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    db_unidad = unidad_service.get_unidad_by_id(db, unidad_id, empresa_id=current_user.empresa_id)
    if not db_unidad:
        raise HTTPException(status_code=404, detail="Unidad no encontrada")
    return db_unidad

@router.put("/unidades/{unidad_id}", response_model=schemas.PHUnidad)
def actualizar_unidad(
    unidad_id: int,
    unidad: schemas.PHUnidadCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    updated_unidad = unidad_service.update_unidad(
        db, 
        unidad_id, 
        unidad, 
        empresa_id=current_user.empresa_id,
        usuario_id=current_user.id
    )
    if not updated_unidad:
        raise HTTPException(status_code=404, detail="Unidad no encontrada")
    return updated_unidad

@router.delete("/unidades/{unidad_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_unidad(
    unidad_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    success = unidad_service.delete_unidad(db, unidad_id, empresa_id=current_user.empresa_id)
    if not success:
         raise HTTPException(status_code=404, detail="Unidad no encontrada")
    return None

# --- CONFIGURACION ---
@router.get("/configuracion", response_model=config_schemas.PHConfiguracionResponse)
def get_configuracion(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return configuracion_service.get_configuracion(db, current_user.empresa_id)

@router.put("/configuracion", response_model=config_schemas.PHConfiguracionResponse)
def update_configuracion(
    config: config_schemas.PHConfiguracionUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    print(f"DEBUG: update_configuracion called by user {current_user.id}. Payload: {config.dict()}")
    return configuracion_service.update_configuracion(db, current_user.empresa_id, config)


# Rutas de Conceptos movidas a conceptos.py y gestionadas por configuracion_service en unidad_service.py o similar si fuera necesario.
# Anteriormente estaban duplicadas aquí.

# --- FACTURACION MASIVA ---
@router.get("/facturacion/masiva/check")
def check_facturacion_masiva(
    fecha: date,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Verifica si ya existen facturas para el periodo indicado.
    """
    count = facturacion_service.check_facturacion_periodo(db, current_user.empresa_id, fecha)
    return {"existe": count > 0, "cantidad": count}

@router.post("/facturacion/masiva")
def generar_facturacion_masiva(
    payload: FacturacionMasivaRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    resultado = facturacion_service.generar_facturacion_masiva(
        db, 
        empresa_id=current_user.empresa_id, 
        fecha_factura=payload.fecha,
        usuario_id=current_user.id,
        conceptos_ids=payload.conceptos_ids,
        configuracion_conceptos=payload.configuracion_conceptos # Pasar nueva config
    )
    return resultado

@router.get("/facturacion/historial")
def get_historial_facturacion(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return facturacion_service.get_historial_facturacion(db, current_user.empresa_id)

@router.get("/facturacion/detalle/{periodo}")
def get_detalle_facturacion_periodo(
    periodo: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Retorna el detalle (lista de facturas) de un periodo especificado.
    """
    return facturacion_service.get_detalle_facturacion(db, current_user.empresa_id, periodo)

@router.get("/facturacion/detalle/{periodo}/pdf")
def get_detalle_facturacion_periodo_pdf(
    periodo: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Genera y descarga el PDF del detalle de facturación.
    """
    pdf_content = facturacion_service.generar_pdf_detalle_facturacion(db, current_user.empresa_id, periodo)
    
    headers = {
        'Content-Disposition': f'attachment; filename="Detalle_Facturacion_{periodo}.pdf"'
    }
    return Response(content=pdf_content, media_type="application/pdf", headers=headers)

@router.delete("/facturacion/masiva/{periodo}")
def eliminar_facturacion_masiva(
    periodo: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # periodo formato YYYY-MM
    return facturacion_service.eliminar_facturacion_masiva(db, current_user.empresa_id, periodo, current_user.id)

# --- RECALCULO INTELIGENTE ---
class RecalculoInteresesRequest(BaseModel):
    unidad_id: int
    fecha_pago: date

@router.post("/facturacion/recalcular-intereses")
def recalcular_intereses_endpoint(
    payload: RecalculoInteresesRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Recalcula intereses en facturas POSTERIORES a la fecha_pago.
    """
    return facturacion_service.recalcular_intereses_posteriores(
        db, 
        current_user.empresa_id, 
        payload.unidad_id, 
        payload.fecha_pago,
        current_user.id
    )

# --- PAGOS Y TESORERIA ---
@router.get("/pagos/estado-cuenta/{unidad_id}")
def get_estado_cuenta(
    unidad_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return pago_service.get_estado_cuenta_unidad(db, unidad_id, current_user.empresa_id)

@router.post("/pagos/registrar")
def registrar_pago(
    payload: PagoRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Registra un pago y retorna:
    {
        "documento": {...},
        "sugerir_recalculo": bool,
        "facturas_futuras_count": int
    }
    """
    return pago_service.registrar_pago_unidad(
        db,
        unidad_id=payload.unidad_id,
        empresa_id=current_user.empresa_id,
        usuario_id=current_user.id,
        monto=payload.monto,
        fecha_pago=payload.fecha,
        forma_pago_id=payload.forma_pago_id
    )

@router.get("/pagos/historial/{unidad_id}")
def get_historial_cuenta(
    unidad_id: int,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return pago_service.get_historial_cuenta_unidad(
        db, 
        unidad_id, 
        current_user.empresa_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )

@router.get("/pagos/historial-propietario/{propietario_id}")
def get_historial_cuenta_propietario_route(
    propietario_id: int,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return pago_service.get_historial_cuenta_unidad(
        db, 
        unidad_id=None, 
        empresa_id=current_user.empresa_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        propietario_id=propietario_id
    )



@router.get("/pagos/estado-cuenta-propietario/{propietario_id}")
def get_estado_cuenta_propietario(
    propietario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return pago_service.get_estado_cuenta_propietario(db, propietario_id, current_user.empresa_id)

@router.get("/pagos/cartera-pendiente")
def get_cartera_pendiente(
    unidad_id: Optional[int] = None,
    propietario_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return pago_service.get_cartera_ph_pendientes(
        db, 
        empresa_id=current_user.empresa_id,
        unidad_id=unidad_id,
        propietario_id=propietario_id
    )

@router.get("/pagos/estado-cuenta/{id}/pdf")
def get_estado_cuenta_pdf(
    id: int,
    mode: str = 'UNIT', # 'UNIT' | 'OWNER'
    view: str = 'PENDING', # 'PENDING' | 'HISTORY'
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Genera el PDF del Estado de Cuenta (Relación de Cobro o Histórico Detallado).
    """
    unidad_id = id if mode == 'UNIT' else None
    propietario_id = id if mode == 'OWNER' else None
    
    pdf_content = pago_service.generar_pdf_estado_cuenta(
        db, 
        empresa_id=current_user.empresa_id,
        unidad_id=unidad_id,
        propietario_id=propietario_id,
        view_mode=view,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )
    
    filename = f"EstadoCuenta_{mode}_{id}_{view}_{date.today()}.pdf"
    
    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"'
    }
    return Response(content=pdf_content, media_type="application/pdf", headers=headers)

# --- REPORTES ---
@router.post("/reportes/movimientos")
def get_reporte_movimientos(
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    unidad_id: Optional[int] = None,
    propietario_id: Optional[int] = None,
    tipo_documento_id: Optional[int] = None,
    concepto_id: Optional[int] = None,
    numero_doc: Optional[str] = None,
    tipo_movimiento: Optional[str] = None, # Nuevo filtro
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return reportes_service.get_movimientos_ph_report(
        db,
        empresa_id=current_user.empresa_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        unidad_id=unidad_id,
        propietario_id=propietario_id,
        tipo_documento_id=tipo_documento_id,
        concepto_id=concepto_id,
        numero_doc=numero_doc,
        tipo_movimiento=tipo_movimiento
    )
