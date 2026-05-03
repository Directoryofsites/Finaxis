from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from pydantic import BaseModel
from fastapi import UploadFile, File, Form

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Usuario
from app.schemas.propiedad_horizontal import unidad as schemas
from app.schemas.propiedad_horizontal import configuracion as config_schemas
from app.schemas.propiedad_horizontal import modulo_contribucion as modulo_schemas
from app.schemas.propiedad_horizontal import recaudos as recaudo_schemas
from app.schemas.propiedad_horizontal import presupuesto as presupuesto_schemas
from app.schemas.propiedad_horizontal import recaudo_masivo as rm_schemas
from app.services.propiedad_horizontal import unidad_service, configuracion_service, facturacion_service, pago_service, reportes as reportes_service, modulo_service, presupuesto_service, recaudo_masivo_service

from . import conceptos

router = APIRouter()
router.include_router(conceptos.router)

# --- CAMPOS PERSONALIZADOS (MOTOR DINÁMICO) ---
from app.models.propiedad_horizontal.campo_personalizado import PHCampoPersonalizado

class PHCampoPersonalizadoSchema(BaseModel):
    id: Optional[int] = None
    entidad: str
    etiqueta: str
    llave_json: str
    tipo: str = "text"
    activo: bool = True

    class Config:
        from_attributes = True

@router.get("/campos-personalizados", response_model=List[PHCampoPersonalizadoSchema])
def get_campos_personalizados(
    entidad: str = "unidades",
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    campos = db.query(PHCampoPersonalizado).filter(
        PHCampoPersonalizado.empresa_id == current_user.empresa_id,
        PHCampoPersonalizado.entidad == entidad,
        PHCampoPersonalizado.activo == True
    ).all()
    return campos

@router.post("/campos-personalizados", response_model=PHCampoPersonalizadoSchema)
def crear_campo_personalizado(
    payload: PHCampoPersonalizadoSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    nuevo_campo = PHCampoPersonalizado(
        empresa_id=current_user.empresa_id,
        entidad=payload.entidad,
        etiqueta=payload.etiqueta,
        llave_json=payload.llave_json,
        tipo=payload.tipo,
        activo=payload.activo
    )
    db.add(nuevo_campo)
    db.commit()
    db.refresh(nuevo_campo)
    return nuevo_campo

@router.put("/campos-personalizados/{id}", response_model=PHCampoPersonalizadoSchema)
def actualizar_campo_personalizado(
    id: int,
    payload: PHCampoPersonalizadoSchema,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    campo = db.query(PHCampoPersonalizado).filter(
        PHCampoPersonalizado.id == id,
        PHCampoPersonalizado.empresa_id == current_user.empresa_id
    ).first()
    if not campo:
        raise HTTPException(status_code=404, detail="Campo personalizado no encontrado")
    
    campo.etiqueta = payload.etiqueta
    campo.llave_json = payload.llave_json
    campo.tipo = payload.tipo
    campo.activo = payload.activo
    
    db.commit()
    db.refresh(campo)
    return campo

@router.delete("/campos-personalizados/{id}")
def eliminar_campo_personalizado(
    id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    campo = db.query(PHCampoPersonalizado).filter(
        PHCampoPersonalizado.id == id,
        PHCampoPersonalizado.empresa_id == current_user.empresa_id
    ).first()
    if not campo:
        raise HTTPException(status_code=404, detail="Campo personalizado no encontrado")
    
    db.delete(campo)
    db.commit()
    return {"status": "ok"}


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

class PagoDetalle(BaseModel):
    concepto_id: int
    monto: float

class PagoRequest(BaseModel):
    unidad_id: int
    monto: float
    fecha: date
    forma_pago_id: int = None
    cuenta_caja_id: Optional[int] = None # Cuenta de destino (Caja/Banco)
    detalles: Optional[List[PagoDetalle]] = None
    observaciones: Optional[str] = None

class PagoMasivoRequest(BaseModel):
    unidades_ids: List[int]
    fecha: date
    forma_pago_id: Optional[int] = None
    monto_fijo: Optional[float] = None # Si se provee, todas pagan este valor
    pagar_saldo_total: bool = False # Si es True, cada una paga su deuda completa
    observaciones: Optional[str] = None

# --- TORRES ---
@router.get("/torres", response_model=List[schemas.PHTorre])
def listar_torres(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return unidad_service.get_torres(db, current_user.empresa_id)

@router.post("/torres", response_model=schemas.PHTorre)
def crear_torre(
    torre: schemas.PHTorreCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return unidad_service.create_torre(db, torre, current_user.empresa_id)

@router.put("/torres/{id}", response_model=schemas.PHTorre)
def actualizar_torre(
    id: int,
    torre: schemas.PHTorreCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    updated = unidad_service.update_torre(db, id, torre, current_user.empresa_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Torre no encontrada")
    return updated

@router.delete("/torres/{id}")
def eliminar_torre(
    id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    success = unidad_service.delete_torre(db, id, current_user.empresa_id)
    if not success:
         raise HTTPException(status_code=404, detail="Torre no encontrada")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# --- MASS ACTIONS ---
@router.post("/unidades/masivo/modulos")
def mass_update_modules(
    payload: schemas.PHUnidadMassUpdateModules,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    count = unidad_service.masive_update_modules(db, mass_update=payload, empresa_id=current_user.empresa_id)
    return {"message": "Actualización masiva completada", "updated_count": count}

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
    torre_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Permitir hasta 1000 para recaudos masivos de torres grandes
    limit = min(limit, 1000)
    return unidad_service.get_unidades(db, empresa_id=current_user.empresa_id, skip=skip, limit=limit, torre_id=torre_id)

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
    try:
        return configuracion_service.get_configuracion(db, current_user.empresa_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener configuración: {str(e)}")

# --- PAGOS CONSOLIDADOS ---
@router.post("/pagos/consolidado", response_model=recaudo_schemas.PagoConsolidadoResponse)
def registrar_pago_consolidado(
    payload: recaudo_schemas.PagoConsolidadoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Registra un pago único distribuido entre las unidades de un propietario.
    """
    return pago_service.registrar_pago_consolidado(
        db, 
        propietario_id=payload.propietario_id,
        monto_total=payload.monto_total,
        fecha=payload.fecha,
        empresa_id=current_user.empresa_id,
        usuario_id=current_user.id,
        forma_pago_id=payload.forma_pago_id,
        cuenta_caja_id=payload.cuenta_caja_id, # Nueva cuenta flexible
        observaciones=payload.observaciones
    )

@router.put("/configuracion", response_model=config_schemas.PHConfiguracionResponse)
def update_configuracion(
    config: config_schemas.PHConfiguracionUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        print(f"DEBUG: update_configuracion called by user {current_user.id}. Payload: {config.dict()}")
        return configuracion_service.update_configuracion(db, current_user.empresa_id, config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar configuración: {str(e)}")


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
    try:
        return pago_service.get_estado_cuenta_unidad(db, unidad_id, current_user.empresa_id)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error Crítico Backend: {str(e)}")

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
        forma_pago_id=payload.forma_pago_id,
        cuenta_caja_id=payload.cuenta_caja_id, # Nueva cuenta flexible
        detalles=payload.detalles,
        observaciones=payload.observaciones
    )

@router.post("/pagos/masivo")
def registrar_pago_masivo(
    pago: PagoMasivoRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Endpoint para procesar el pago de múltiples unidades en lote (Torre/Bloque).
    """
    return pago_service.registrar_pago_masivo(
        db,
        current_user.empresa_id,
        current_user.id,
        pago.unidades_ids,
        pago.fecha,
        pago.forma_pago_id,
        monto_fijo=pago.monto_fijo,
        pagar_saldo_total=pago.pagar_saldo_total,
        observaciones=pago.observaciones
    )

# --- RECAUDO MASIVO POR ARCHIVOS PLANOS ---
@router.post("/recaudos-masivos/upload", response_model=rm_schemas.RecaudoPreviewResult)
def upload_recaudos_masivos(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        content = file.file.read()
        filas = recaudo_masivo_service.parse_recaudo_file(content, file.filename)
        return recaudo_masivo_service.generar_preview(db, current_user.empresa_id, filas)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado procesando archivo: {str(e)}")

@router.post("/recaudos-masivos/process", response_model=rm_schemas.RecaudoProcessResponse)
def process_recaudos_masivos(
    request: rm_schemas.RecaudoProcessRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return recaudo_masivo_service.procesar_lote_pagos(db, current_user.empresa_id, request, current_user.id)

@router.get("/recaudos-masivos/generate-test")
def generate_asobancaria_test_file(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Genera un archivo plano Asobancaria de prueba con la deuda actual de todas las unidades.
    """
    try:
        content = recaudo_masivo_service.generar_archivo_asobancaria_test(db, current_user.empresa_id)
        filename = f"PRUEBA_ASOBANCARIA_{date.today()}.txt"
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
        return Response(content=content, media_type="text/plain", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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

@router.get("/pagos/cartera-detallada/{unidad_id}")
def get_cartera_detallada(
    unidad_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Retorna la cartera pendiente desagregada por conceptos (Intereses, Multas, Capital).
    Aplica prelación de pagos virtual.
    """
    return pago_service.get_cartera_ph_pendientes_detallada(db, current_user.empresa_id, unidad_id)

@router.get("/pagos/cartera-detallada/{unidad_id}/pdf")
def get_cartera_detallada_pdf(
    unidad_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Descarga PDF de la cartera detallada.
    """
    pdf_content = pago_service.generar_pdf_cartera_detallada(db, current_user.empresa_id, unidad_id)
    
    filename = f"DetalleCartera_{unidad_id}_{date.today()}.pdf"
    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"'
    }
    return Response(content=pdf_content, media_type="application/pdf", headers=headers)

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
    filtro_metadato_llave: Optional[str] = None,
    filtro_metadato_valor: Optional[str] = None,
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
        tipo_movimiento=tipo_movimiento,
        filtro_metadato_llave=filtro_metadato_llave,
        filtro_metadato_valor=filtro_metadato_valor
    )

@router.get("/reportes/cartera-edades", response_model=recaudo_schemas.CarteraEdadesResponse)
def get_reporte_cartera_edades(
    fecha_corte: Optional[date] = None,
    filtro_metadato_llave: Optional[str] = None,
    filtro_metadato_valor: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Reporte de cartera clasificada por edades: 0-30, 31-60, 61-90, >90
    Soporta fecha de corte histórica.
    """
    return reportes_service.get_cartera_edades(
        db, 
        current_user.empresa_id, 
        fecha_corte=fecha_corte,
        filtro_metadato_llave=filtro_metadato_llave,
        filtro_metadato_valor=filtro_metadato_valor
    )

@router.get("/reportes/saldos", response_model=recaudo_schemas.ReporteSaldoResponse)
def get_reporte_saldos(
    fecha_corte: Optional[date] = None,
    unidad_id: Optional[int] = None,
    propietario_id: Optional[int] = None,
    torre_id: Optional[int] = None,
    concepto_busqueda: Optional[str] = None,
    modulo_id: Optional[int] = None,
    operador_monto: Optional[str] = None,
    valor_monto: Optional[float] = None,
    agrupar_por_propietario: bool = False,
    filtro_metadato_llave: Optional[str] = None,
    filtro_metadato_valor: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Reporte de Saldos (Balance General) detallado.
    Permite filtrar por Torre, Unidad, Prop, Concepto y Metadatos Dinámicos.
    """
    return reportes_service.get_reporte_saldos(
        db, 
        current_user.empresa_id, 
        fecha_corte=fecha_corte,
        unidad_id=unidad_id,
        propietario_id=propietario_id,
        torre_id=torre_id,
        concepto_busqueda=concepto_busqueda,
        modulo_id=modulo_id,
        operador_monto=operador_monto,
        valor_monto=valor_monto,
        agrupar_por_propietario=agrupar_por_propietario,
        filtro_metadato_llave=filtro_metadato_llave,
        filtro_metadato_valor=filtro_metadato_valor
    )

# --- PRESUPUESTOS ---
@router.get("/presupuestos/{anio}", response_model=List[presupuesto_schemas.PHPresupuestoResponse])
def get_presupuestos(
    anio: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return presupuesto_service.get_presupuestos(db, current_user.empresa_id, anio)

@router.post("/presupuestos/masivo")
def save_presupuestos(
    payload: presupuesto_schemas.PHPresupuestoMasivo,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Guarda o actualiza multiples rubros presupuestales
    """
    return presupuesto_service.save_presupuestos_masivo(db, current_user.empresa_id, payload)

@router.get("/reportes/ejecucion-presupuestal", response_model=presupuesto_schemas.EjecucionPresupuestalResponse)
def get_ejecucion_presupuestal(
    anio: Optional[int] = None,
    mes_corte: Optional[int] = None,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Retorna la ejecución presupuestal.
    Modos:
    1. Por Defecto (anio + mes_corte): Acumulado desde Ene 1 hasta fin del mes_corte.
    2. Por Rango (fecha_inicio + fecha_fin): Acumulado exacto en el rango.
    """
    return presupuesto_service.get_ejecucion_presupuestal(db, current_user.empresa_id, anio, mes_corte, fecha_inicio, fecha_fin)

