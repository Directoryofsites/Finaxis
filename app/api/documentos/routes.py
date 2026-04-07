# app/api/documentos/routes.py (Versión 100% CORREGIDA: Problemas de Indentación/Sintaxis)

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

# === Importaciones de Seguridad ===
from app.core.security import decode_print_token, get_current_user, has_permission 
# ==================================

from app.services import documento as service
from app.services import cartera as cartera_service
from app.services import plantilla as services_plantilla
from app.schemas import documento as schemas
from app.schemas import plantilla as schemas_plantilla
from app.core.database import get_db
from app.models import Usuario as models_usuario
from app.models import movimiento_contable as models_mov

router = APIRouter()

# --- FUNCIÓN DE TRANSFORMACIÓN ---
def transformar_a_detalle_vendido(movimientos: List[models_mov.MovimientoContable]) -> List[schemas.DetalleProductoVendido]:
    detalles_agrupados = {}

    movimientos_de_ingreso = [
        m for m in movimientos 
        if m.producto_id is not None and m.credito > 0 and hasattr(m, 'cuenta') and m.cuenta.es_cuenta_de_ingresos
    ]

    for mov in movimientos_de_ingreso:
        if mov.cantidad and mov.cantidad > 0:
            precio_unitario = float(mov.credito) / float(mov.cantidad)
            total_linea = float(mov.credito)

            detalle = schemas.DetalleProductoVendido(
                producto_id=mov.producto_id,
                nombre_producto=mov.producto.nombre if mov.producto else "N/A",
                cantidad=mov.cantidad,
                vrUnitario=precio_unitario,
                totalLinea=total_linea,
            )
            detalles_agrupados[mov.producto_id] = detalle
            
    return list(detalles_agrupados.values())
# --- FIN: FUNCIÓN DE TRANSFORMACIÓN ---


@router.post("/", response_model=schemas.Documento, status_code=status.HTTP_201_CREATED)
def create_documento(
    documento: schemas.DocumentoCreate,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(has_permission("contabilidad:crear_documento"))
):
    documento.empresa_id = current_user.empresa_id
    try:
        db_documento = service.create_documento(db=db, documento=documento, user_id=current_user.id)      
        return db_documento
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado al crear el documento: {str(e)}")


@router.get("/", response_model=schemas.ListaDocumentosResponse)
def read_documentos(
    filtros: schemas.DocumentoFiltros = Depends(),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(has_permission("contabilidad:explorador"))
):
    filtros_dict = filtros.model_dump(exclude_none=True)
    return service.get_documentos(
        db=db,
        empresa_id=current_user.empresa_id,
        filtros=filtros_dict,
        skip=skip,
        limit=limit
    )


@router.post("/buscar-para-gestion", response_model=List[schemas.DocumentoGestionResult])
def buscar_para_gestion(
    filtros_payload: schemas.DocumentoGestionFiltros,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(has_permission("contabilidad:explorador"))
):
    try:
        resultados = service.buscar_documentos_para_gestion(
            db=db, 
            filtros=filtros_payload, 
            empresa_id=current_user.empresa_id
        )
        return resultados
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/anulados-para-gestion", response_model=List[schemas.DocumentoAnuladoResult])
def get_anulados_para_gestion(
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    try:
        resultados = service.get_documentos_anulados_para_gestion(
            db=db,
            empresa_id=current_user.empresa_id
        )
        return resultados
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al obtener documentos anulados: {str(e)}"
        )


@router.post("/anulacion-masiva")
def anular_documentos_masivamente(
    payload: schemas.DocumentoAccionMasivaPayload,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    try:
        resultado = service.anular_documentos_masivamente(
            db=db,
            payload=payload,
            empresa_id=current_user.empresa_id,
            user_id=current_user.id,
            user_email=current_user.email
        )
        return resultado
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado en la anulación masiva: {str(e)}")


@router.post("/eliminacion-masiva")
def eliminar_documentos_masivamente(
    payload: schemas.DocumentoAccionMasivaPayload,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    try:
        resultado = service.eliminar_documentos_masivamente(
            db=db,
            payload=payload,
            empresa_id=current_user.empresa_id,
            user_id=current_user.id
        )
        return resultado
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado en la eliminación masiva: {str(e)}")


@router.get("/{documento_id}", response_model=schemas.Documento)
def read_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    print(f"\n--- SONDA 1: INICIANDO BÚSQUEDA PARA DOCUMENTO ID: {documento_id} ---")
    
    db_documento = service.get_documento_by_id(db, documento_id=documento_id, empresa_id=current_user.empresa_id)
    if db_documento is None:
        print(f"--- SONDA FALLIDA: No se encontró el documento ID: {documento_id} ---")
        raise HTTPException(status_code=404, detail="Documento no encontrado o no pertenece a la empresa.")

    print(f"--- SONDA 2: Documento principal encontrado (Número: {db_documento.numero}). Llamando al nuevo servicio... ---")

    detalle_comercial = service.get_detalle_comercial_por_documento(
        db=db, 
        documento_id=documento_id, 
        empresa_id=current_user.empresa_id
    )
    
    print("--- SONDA 3: Resultado recibido del servicio get_detalle_comercial_por_documento ---")
    print(f"VALOR DE 'detalle_comercial': {detalle_comercial}")
    
    db_documento.detalle_productos = detalle_comercial
    
    return db_documento

@router.put("/{documento_id}", response_model=schemas.Documento)
def update_documento_endpoint(
    documento_id: int,
    documento_update: schemas.DocumentoUpdate,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(has_permission("contabilidad:editar_documento"))
):
    try:
        db_documento = service.update_documento(
            db=db,
            documento_id=documento_id,
            documento_update=documento_update,
            empresa_id=current_user.empresa_id,
            user_id=current_user.id
        )
        return db_documento
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{documento_id}/anular", response_model=schemas.Documento)
def anular_documento(
    documento_id: int,
    anulacion_data: schemas.DocumentoAnulacion,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(has_permission("contabilidad:crear_documento"))
):
    try:
        db_documento = service.anular_documento(
            db=db,
            documento_id=documento_id,
            empresa_id=current_user.empresa_id,
            user_id=current_user.id,
            user_email=current_user.email,
            razon=anulacion_data.razon
        )
        return db_documento
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado al anular el documento: {str(e)}")


@router.put("/{documento_id}/reactivar", response_model=schemas.Documento)
def reactivar_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    try:
        db_documento = service.reactivar_documento(
            db=db,
            documento_id=documento_id,
            empresa_id=current_user.empresa_id
        )
        return db_documento
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado al reactivar el documento: {str(e)}")


@router.delete("/{documento_id}")
def eliminar_documento(
    documento_id: int,
    eliminacion_data: schemas.DocumentoAnulacion,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(has_permission("contabilidad:crear_documento"))
):
    try:
        resultado = service.eliminar_documento(
            db=db,
            documento_id=documento_id,
            empresa_id=current_user.empresa_id,
            user_id=current_user.id,
            razon=eliminacion_data.razon
        )
        return resultado
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado al eliminar el documento: {str(e)}")


@router.get("/{documento_id}/pdf")
def generar_pdf_documento_directo(
    documento_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    """
    Genera y devuelve directamente el PDF de un documento
    """
    try:
        # Generar el PDF usando el servicio
        pdf_bytes, file_name = service.generar_pdf_documento(
            db=db,
            documento_id=documento_id,
            empresa_id=current_user.empresa_id
        )
        
        # Devolver el PDF como StreamingResponse
        pdf_stream = io.BytesIO(pdf_bytes)
        return StreamingResponse(
            pdf_stream,
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename={file_name}"}
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar el PDF del documento: {str(e)}"
        )

@router.post("/{documento_id}/solicitar-impresion")
def solicitar_url_impresion(
    documento_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    try:
        url = service.generar_url_firmada_impresion(
            db=db,
            documento_id=documento_id,
            empresa_id=current_user.empresa_id
        )
        return {"signed_url": url}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar la URL firmada: {str(e)}"
        )


# ==============================================================================
# 🖨️ ZONA DE IMPRESIÓN PÚBLICA (TOKEN FIRMADO)
# ==============================================================================
# Estas rutas NO tienen 'Depends(get_current_user)' porque el navegador 
# no envía credenciales al abrir el PDF en una pestaña nueva.

@router.get("/imprimir-firmado")
def imprimir_documento_firmado(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Endpoint público para imprimir documentos individuales usando un token firmado.
    """
    # 1. Validamos el token temporal que viene en la URL
    payload = decode_print_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de impresión inválido o expirado."
        )

    documento_id = payload.get("doc_id")
    empresa_id = payload.get("emp_id")

    # 2. Generamos el PDF usando el servicio
    try:
        pdf_bytes, file_name = service.generar_pdf_documento(
            db=db,
            documento_id=documento_id,
            empresa_id=empresa_id
        )
        
        # 3. Devolvemos el archivo al navegador
        pdf_stream = io.BytesIO(pdf_bytes)
        return StreamingResponse(
            pdf_stream,
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename={file_name}"}
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error generando PDF: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al generar el archivo PDF."
        )

@router.post(
    "/{documento_id}/crear-plantilla",
    response_model=schemas_plantilla.PlantillaMaestra,
    status_code=status.HTTP_201_CREATED,
    summary="Crea una plantilla a partir de un documento existente"
)
def create_template_from_document_endpoint(
    documento_id: int,
    payload: schemas_plantilla.TemplateCreateFromDocument,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(has_permission("plantilla:crear"))
):
    try:
        new_template = services_plantilla.create_template_from_document(
            db=db,
            documento_id=documento_id,
            nombre_plantilla=payload.nombre_plantilla,
            user_id=current_user.id
        )
        return new_template
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocurrió un error inesperado en el servidor: {str(e)}"
        )

# --- INICIO: NUEVOS ENDPOINTS PARA PDF DE RENTABILIDAD ---

@router.post("/{documento_id}/solicitar-impresion-rentabilidad")
def solicitar_url_impresion_rentabilidad(
    documento_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    """Endpoint seguro para que el frontend solicite la URL firmada."""
    try:
        url = service.generar_url_firmada_rentabilidad(
            db=db,
            documento_id=documento_id,
            empresa_id=current_user.empresa_id
        )
        return {"signed_url": url}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar la URL de rentabilidad: {str(e)}"
        )


@router.get("/imprimir-rentabilidad-firmado")
def imprimir_rentabilidad_firmado(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Endpoint público para imprimir el reporte de rentabilidad de una factura usando un token firmado.
    """
    # 1. Validamos el token temporal
    payload = decode_print_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de impresión inválido o expirado."
        )

    documento_id = payload.get("doc_id")
    empresa_id = payload.get("emp_id")

    # 2. Generamos el PDF de rentabilidad
    try:
        pdf_bytes = service.generar_pdf_rentabilidad_factura(
            db=db,
            documento_id=documento_id,
            empresa_id=empresa_id
        )
        
        file_name = f"rentabilidad_factura_{documento_id}.pdf"
        
        # 3. Devolvemos el archivo al navegador
        pdf_stream = io.BytesIO(pdf_bytes)
        return StreamingResponse(
            pdf_stream,
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename={file_name}"}
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error generando PDF de rentabilidad: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al generar la rentabilidad: {str(e)}"
        )