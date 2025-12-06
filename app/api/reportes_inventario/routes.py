# app/api/reportes_inventario/routes.py (VERSIÓN FINAL COMPLETA E INTACTA)

from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional, List, Tuple

from app.core.database import get_db
from app.core import security
from app.models import usuario as models_usuario
from app.schemas import reportes_inventario as schemas_reportes

# Servicios (Motores de Lógica)
from app.services import reportes_inventario as service_reportes

router = APIRouter()

# ==============================================================================
# === RUTAS DE KARDEX (RESTABLECIDAS - FIX CRÍTICO DE SCHEMA) ===
# ==============================================================================

@router.get(
    "/kardex/{producto_id}",
    # La respuesta es el schema KardexResponse
    response_model=schemas_reportes.KardexResponse, 
    summary="Obtiene el Kardex detallado de un producto (Ruta de la UI)."
)
def get_kardex_por_producto_route(
    producto_id: int,
    fecha_inicio: date = Query(..., description="Fecha de inicio del periodo."),
    fecha_fin: date = Query(..., description="Fecha de fin del periodo."),
    bodega: Optional[int] = Query(None, description="ID de bodega para filtrar o consolidar."),
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(security.get_current_user)
):
    """
    Ruta que alimenta la tabla del Kardex en la UI.
    """
    # FIX CRÍTICO: Usar el schema KardexFiltrosPDF que sí existe.
    filtros = schemas_reportes.KardexFiltrosPDF(
        producto_id=producto_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        bodega_id=bodega # Usamos bodega_id en lugar de bodega para mayor coherencia con el schema
    )
    return service_reportes.get_kardex_por_producto(
        db=db,
        empresa_id=current_user.empresa_id,
        filtros=filtros
    )


@router.post(
    "/kardex/token-pdf", 
    response_model=schemas_reportes.PDFTokenResponse, 
    summary="Genera un token firmado para la descarga segura del PDF de Kardex."
)
def crear_token_kardex_pdf_route(
    filtros: schemas_reportes.KardexFiltrosPDF,
    current_user: models_usuario.Usuario = Depends(security.get_current_user)
):
    """
    Genera un token que se utiliza en la URL para descargar el PDF de Kardex.
    """
    token = service_reportes.crear_token_kardex_pdf(filtros)
    return {"token": token}


@router.get(
    "/kardex/pdf/{token}",
    status_code=status.HTTP_200_OK,
    summary="Descarga el PDF del Kardex usando un token firmado (Ruta pública/no autenticada)."
)
def generar_kardex_pdf_token_route(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Valida el token y devuelve el PDF en bytes.
    """
    pdf_bytes, filename = service_reportes.generar_kardex_pdf_por_token(db=db, token=token)
    
    from fastapi.responses import Response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ==============================================================================
# === RUTAS DE TOPES DE INVENTARIO (ESTABLES) ===
# ==============================================================================

@router.post(
    "/topes/token-pdf", 
    response_model=schemas_reportes.PDFTokenResponse, 
    summary="Genera un token firmado para la descarga segura del PDF de Reporte de Topes."
)
def crear_token_topes_pdf_route(
    filtros: schemas_reportes.ReporteTopesFiltros,
    current_user: models_usuario.Usuario = Depends(security.get_current_user)
):
    try:
        token_payload_str = filtros.model_dump_json()
        token = security.create_signed_token(token_payload_str, salt='pdf-topes-v1', max_age=600) 
        return {"token": token}
    except Exception as e:
        print(f"Error al crear token JWT para Topes: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Fallo en el motor de firma de tokens.")


@router.get(
    "/topes/pdf/{token}",
    status_code=status.HTTP_200_OK,
    summary="Descarga el PDF del Reporte de Topes usando un token firmado (Ruta pública/no autenticada)."
)
def generar_reporte_topes_pdf_token_route(
    token: str,
    db: Session = Depends(get_db)
):
    try:
        payload_str = security.validate_signed_token(token, salt='pdf-topes-v1', max_age=600)
        if not payload_str:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de descarga inválido o expirado. Vuelva a solicitar el PDF.")

        filtros = schemas_reportes.ReporteTopesFiltros.model_validate_json(payload_str)
        # Nota: Asumimos que existe una función generar_pdf_reporte_topes_por_token o similar. 
        # Si no existe, usar la lógica directa. Aquí mantenemos la estructura original del archivo enviado.
        if hasattr(service_reportes, 'generar_pdf_reporte_topes_por_token'):
             pdf_bytes, filename = service_reportes.generar_pdf_reporte_topes_por_token(db=db, filtros=filtros)
        else:
             # Fallback a lógica directa si la función específica de token no está exportada
             raise HTTPException(status_code=501, detail="Función de generación de PDF por token no implementada en servicio.")
        
        from fastapi.responses import Response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        print(f"Error en ruta /topes/pdf/{{token}}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error en el motor de descarga del reporte.")


@router.get(
    "/topes",
    response_model=schemas_reportes.ReporteTopesResponse,
    summary="Obtiene el reporte de productos bajo stock mínimo o sobre stock máximo (UI)."
)
def get_reporte_topes_route(
    fecha_corte: date = Query(..., description="Fecha hasta la cual se calcula el saldo."),
    tipo_alerta: str = Query("MINIMO", description="Filtro de alerta: MINIMO, MAXIMO, o TODOS."),
    bodega_ids: Optional[List[int]] = Query(None, description="Lista de IDs de bodega."),
    grupo_ids: Optional[List[int]] = Query(None, description="Lista de IDs de grupo."),
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(security.get_current_user)
):
    filtros = schemas_reportes.ReporteTopesFiltros(
        fecha_corte=fecha_corte,
        tipo_alerta=tipo_alerta,
        bodega_ids=bodega_ids,
        grupo_ids=grupo_ids
    )
    return service_reportes.get_reporte_topes_inventario(
        db=db, 
        empresa_id=current_user.empresa_id, 
        filtros=filtros
    )

# ==============================================================================
# === RUTAS DE REPORTES ANALÍTICOS Y SUPER INFORME (ESTABLES) ===
# ==============================================================================

@router.post(
    "/movimiento-analitico",
    response_model=schemas_reportes.ReporteAnaliticoResponse,
    summary="Obtiene el reporte analítico de movimientos de inventario (UI - POST para filtros)."
)
def get_reporte_analitico_route(
    filtros: schemas_reportes.SuperInformeFiltros, # <--- FIX CRÍTICO: Usamos el esquema Multi-ID
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(security.get_current_user)
):
    """
    FIX: Usamos el esquema más robusto (SuperInformeFiltros) para evitar el error de atributo
    cuando el servicio busca los campos plurales.
    """
    return service_reportes.get_reporte_analitico_movimientos(
        db=db,
        empresa_id=current_user.empresa_id,
        filtros=filtros
    )

# ---------------------------------------------------------------------------
# [NUEVA RUTA] Generar PDF Movimiento Analítico
# Esta es la inserción solicitada para arreglar el error 404.
# ---------------------------------------------------------------------------
@router.post(
    "/movimiento-analitico/pdf",
    status_code=status.HTTP_200_OK,
    summary="Genera el PDF del reporte analítico de movimientos (Ruta de descarga)."
)
def generar_pdf_movimiento_analitico_route(
    filtros: schemas_reportes.SuperInformeFiltros,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(security.get_current_user)
):
    pdf_bytes, filename = service_reportes.generar_pdf_movimiento_analitico(
        db=db,
        empresa_id=current_user.empresa_id,
        filtros=filtros
    )
    from fastapi.responses import Response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
# ---------------------------------------------------------------------------


@router.post(
    "/super-informe-inventarios",
    response_model=schemas_reportes.SuperInformeResponse,
    summary="Obtiene el Super Informe de Inventarios con filtros y paginación (UI - POST para filtros)."
)
def get_super_informe_inventarios_route(
    filtros: schemas_reportes.SuperInformeFiltros,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(security.get_current_user)
):
    return service_reportes.get_super_informe_inventarios(
        db=db,
        empresa_id=current_user.empresa_id,
        filtros=filtros
    )


@router.post(
    "/super-informe-inventarios/generar-pdf-directo",
    status_code=status.HTTP_200_OK,
    summary="Genera el PDF del Super Informe de Inventario directamente (Ruta de descarga)."
)
def generar_pdf_super_informe_directo_route(
    filtros: schemas_reportes.SuperInformeFiltros,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(security.get_current_user)
):
    """
    Ruta que genera el PDF del Super Informe. Faltaba y causaba el 404 en el botón de descarga.
    """
    pdf_bytes, filename = service_reportes.generar_pdf_super_informe(
        db=db,
        empresa_id=current_user.empresa_id,
        filtros=filtros
    )
    from fastapi.responses import Response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ==============================================================================
# === RUTAS DE REPORTES GENERALES (ESTABLES) ===
# ==============================================================================

@router.get(
    "/estado-general",
    response_model=schemas_reportes.ReporteInventarioResponse,
    summary="Obtiene el estado general de inventario."
)
def get_estado_general_route(
    fecha_inicio: date = Query(..., description="Fecha de inicio del periodo."),
    fecha_fin: date = Query(..., description="Fecha de fin del periodo."),
    bodega_id: Optional[int] = Query(None, description="ID de bodega."),
    grupo_id: Optional[int] = Query(None, description="ID de grupo."),
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(security.get_current_user)
):
    filtros = schemas_reportes.ReporteInventarioFiltros(
        fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, bodega_id=bodega_id, grupo_id=grupo_id
    )
    return service_reportes.get_reporte_estado_general(
        db=db, empresa_id=current_user.empresa_id, filtros=filtros
    )