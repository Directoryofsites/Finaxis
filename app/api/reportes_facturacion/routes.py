# app/api/reportes_facturacion/routes.py (Versión con ENDPOINTS RESTAURADOS)

from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy.orm import Session
import io
import json # Necesario para json.loads() y json.dumps()
from typing import List, Optional
from datetime import date
from fastapi.responses import StreamingResponse
import traceback 

from app.core.database import get_db
# Importaciones de security (Se asume que estas funciones ya están en app.core.security)
from app.core.security import (
    has_permission, 
    get_current_user, 
    create_pdf_jwt, 
    decode_pdf_jwt
)
from app.models import Usuario as models_usuario 
# Servicios
from app.services import reportes_facturacion as service 
# Schemas
from app.schemas import reportes_facturacion as schemas_reportes_fact
from app.schemas import reporte_rentabilidad as schemas_rentabilidad
from app.schemas import reporte_ventas_cliente as schemas_ventas_cliente

router = APIRouter()

# =================================================================================
# === 1. ENDPOINT PRINCIPAL (DATOS JSON) ===
# =================================================================================

# --- 1.1 Endpoint Reporte Detallado ---
@router.post(
    "/",
    response_model=schemas_reportes_fact.ReporteFacturacionResponse,
    summary="Genera el reporte detallado de facturación para ventas o compras."
)
def generar_reporte_facturacion(
    filtros: schemas_reportes_fact.ReporteFacturacionFiltros,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(has_permission("reportes:ver_facturacion_detallado"))
):
    """
    Obtiene los datos del explorador de transacciones para la tabla.
    """
    return service.get_reporte_facturacion_data( 
        db=db,
        empresa_id=current_user.empresa_id,
        filtros=filtros
    )

# --- 1.2 Endpoint Rentabilidad por Producto/Grupo (JSON) ---
@router.post(
    "/rentabilidad-producto",
    response_model=schemas_rentabilidad.RentabilidadProductoResponse, # Retorna un objeto con items y totales
    summary="Genera el reporte de rentabilidad agrupado por Producto/Grupo."
)
def generar_reporte_rentabilidad_producto_route(
    filtros: schemas_rentabilidad.RentabilidadProductoFiltros, 
    db: Session = Depends(get_db),
    # Permiso que debe existir en el seeder
    current_user: models_usuario = Depends(has_permission("reportes:rentabilidad_producto")) 
):
    """
    Obtiene el reporte de rentabilidad para la interfaz del usuario.
    """
    # FIX CLAVE: Llama a la función correcta en el servicio
    return service.get_rentabilidad_por_grupo( 
        db=db,
        empresa_id=current_user.empresa_id,
        filtros=filtros
    )

# --- 1.3 ENDPOINT RESTAURADO: Rentabilidad por Documento (JSON) ---
@router.post(
    "/rentabilidad-documento",
    response_model=schemas_reportes_fact.ReporteRentabilidadDocumentoResponse, 
    summary="Calcula la rentabilidad línea por línea para un documento específico (Factura)."
)
def generar_rentabilidad_por_documento_route(
    filtros: schemas_reportes_fact.ReporteRentabilidadDocumentoFiltros, 
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(has_permission("reportes:rentabilidad_producto")) # Mismo permiso que el reporte de rentabilidad general
):
    """
    Obtiene la rentabilidad de cada ítem en una factura específica.
    """
    # Llama a la función del servicio
    return service.get_rentabilidad_por_documento( 
        db=db,
        empresa_id=current_user.empresa_id,
        filtros=filtros
    )


# =================================================================================
# === 2. ENDPOINTS DE GENERACIÓN DE PDF (DIRECTO) ===
# =================================================================================

# --- 2.1 PDF Rentabilidad (Generación Directa) ---
@router.post(
    "/rentabilidad-producto/generar-pdf",
    summary="Genera y devuelve el PDF del reporte de rentabilidad directamente.",
)
def generar_pdf_rentabilidad_directo(
    filtros: schemas_rentabilidad.RentabilidadProductoFiltros,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(has_permission("reportes:rentabilidad_producto"))
):
    """
    Genera el PDF del análisis de rentabilidad y lo devuelve como StreamingResponse.
    """
    try:
        pdf_bytes = service.generar_pdf_rentabilidad_producto(
            db=db,
            empresa_id=current_user.empresa_id,
            filtros=filtros
        )
        headers = {
            'Content-Disposition': f'attachment; filename=\"rentabilidad_{filtros.fecha_inicio}_a_{filtros.fecha_fin}.pdf\"'
        }
        return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers=headers)

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error en generar_pdf_rentabilidad_directo: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al generar el PDF del Reporte de Rentabilidad."
        )

# --- 2.2 PDF Detallado de Facturación (Generación Directa) ---
@router.post(
    "/generar-pdf-detallado",
    summary="Genera y devuelve el PDF del reporte detallado de facturación directamente.",
)
def generar_pdf_facturacion_detallado_directo(
    filtros: schemas_reportes_fact.ReporteFacturacionFiltros,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(has_permission("reportes:ver_facturacion_detallado"))
):
    """
    Genera el PDF del reporte de facturación (ventas/compras) y lo devuelve como StreamingResponse.
    """
    try:
        pdf_bytes = service.generar_pdf_reporte_facturacion(
            db=db,
            empresa_id=current_user.empresa_id,
            filtros=filtros
        )
        tipo = "ventas" if filtros.tipo_reporte == 'ventas' else "compras"
        filename = f"reporte_{tipo}_{filtros.fecha_inicio}_a_{filtros.fecha_fin}.pdf"
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
        return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers=headers)

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error en generar_pdf_facturacion_detallado_directo: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al generar el PDF del Reporte Detallado de Facturación."
        )

# --- 2.3 ENDPOINT RESTAURADO: PDF Rentabilidad por Documento (Generación Directa) ---
@router.post(
    "/rentabilidad-documento/generar-pdf",
    summary="Genera y devuelve el PDF del reporte de rentabilidad por documento directamente.",
)
def generar_pdf_rentabilidad_documento_directo(
    filtros: schemas_reportes_fact.ReporteRentabilidadDocumentoFiltros,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(has_permission("reportes:rentabilidad_producto"))
):
    """
    Genera el PDF del análisis de rentabilidad por documento y lo devuelve como StreamingResponse.
    """
    try:
        pdf_bytes = service.generar_pdf_rentabilidad_documento(
            db=db,
            empresa_id=current_user.empresa_id,
            filtros=filtros
        )
        
        # El nombre del archivo se construye con el tipo y número de documento
        ref_documento = f"doc_{filtros.tipo_documento_codigo}_{filtros.numero_documento}"
        filename = f"rentabilidad_{ref_documento}.pdf"
        
        headers = {
            'Content-Disposition': f'attachment; filename=\"{filename}\"'
        }
        return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers=headers)

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error en generar_pdf_rentabilidad_documento_directo: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al generar el PDF del Reporte de Rentabilidad por Documento."
        )


# =================================================================================
# === 3. ENDPOINTS DE JWT LEGACY (Mantenidos por referencia, pero no usados) ===
# =================================================================================

# --- 3.1 SOLICITAR JWT (POST LEGACY) ---
# Se asume que estos endpoints de token legacy serán removidos si se usa el patrón directo.
# Si son necesarios, asegúrate de que create_pdf_jwt y decode_pdf_jwt existen.
@router.post("/solicitar-pdf", response_model=schemas_reportes_fact.PDFTokenResponse)
def solicitar_url_pdf_reporte_facturacion_legacy_route(
    filtros: schemas_reportes_fact.ReporteFacturacionFiltros,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(get_current_user)
):
    try:
        filtros_json_string = filtros.model_dump_json() 
        payload = {
            "emp_id": current_user.empresa_id,
            "filtros": filtros_json_string, 
        }
        # Asegúrate de que create_pdf_jwt exista en app.core.security
        # jwt_token = create_pdf_jwt(payload) 
        jwt_token = "LEGACY_TOKEN" # Reemplazar con lógica real si se usa
        
        return schemas_reportes_fact.PDFTokenResponse(
            url_pdf=f"/api/reportes-facturacion/imprimir-pdf/{jwt_token}"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error en ruta legacy.")

# --- 3.2 IMPRIMIR PDF (GET con JWT LEGACY) ---
@router.get(
    "/imprimir-pdf/{token_jwt}", 
    summary="LEGACY: Genera y devuelve el PDF del Reporte de Facturación usando un token JWT."
)
def imprimir_pdf_reporte_facturacion_legacy_route(
    token_jwt: str,
    db: Session = Depends(get_db)
):
    # Lógica de decodificación y generación de PDF aquí si se necesita el legacy flow
    # Lógica de decodificación y generación de PDF aquí si se necesita el legacy flow
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ruta legacy no implementada.")

# =================================================================================
# === 4. NUEVOS ENDPOINTS: ANÁLISIS INTEGRAL DE VENTAS POR CLIENTE ===
# =================================================================================

@router.post(
    "/ventas-cliente",
    response_model=schemas_ventas_cliente.ReporteVentasClienteResponse,
    summary="Reporte integral de ventas agrupado por cliente con drill-down."
)
def generar_reporte_ventas_cliente(
    filtros: schemas_ventas_cliente.ReporteVentasClienteFiltros,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(has_permission("reportes:ver_facturacion_detallado")) 
):
    """
    Obtiene el reporte integral de ventas por cliente, incluyendo productos y documentos.
    Calcula la rentabilidad por cliente.
    """
    return service.get_analisis_ventas_por_cliente(
        db=db,
        empresa_id=current_user.empresa_id,
        filtros=filtros
    )

@router.post(
    "/ventas-cliente/pdf",
    summary="Genera el PDF del Reporte Integral de Ventas por Cliente."
)
def generar_pdf_ventas_cliente(
    filtros: schemas_ventas_cliente.ReporteVentasClienteFiltros,
    db: Session = Depends(get_db),
    current_user: models_usuario = Depends(has_permission("reportes:ver_facturacion_detallado"))
):
    try:
        pdf_bytes = service.generar_pdf_ventas_cliente(db, current_user.empresa_id, filtros)
        
        headers = {'Content-Disposition': f'attachment; filename="ventas_clientes.pdf"'}
        return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers=headers)

    except HTTPException as h: raise h
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))