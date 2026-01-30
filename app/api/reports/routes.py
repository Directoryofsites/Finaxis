from typing import List, Dict, Any, Optional
from app.services import super_informe as super_informe_service
from app.schemas import documento as schemas_doc
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from datetime import date, datetime

from app.core.database import get_db

from app.core.security import get_current_user
from app.schemas import usuario as usuario_schema

# --- INICIO: MODIFICACIÓN ARQUITECTÓNICA ---
# Se elimina la dependencia directa de documento_service para el Libro Diario
# y se añade la nueva dependencia a nuestro servicio centralizado.
from app.services import documento as documento_service
from app.services import reports as reports_service 
from app.services import cartera as services_cartera
from app.services import libros_oficiales as libros_oficiales_service
from app.services import analisis_financiero as analisis_financiero_service # <-- NUEVA IMPORTACIÓN # <-- NUEVA IMPORTACIÓN

# Se añade el servicio de períodos para la lógica de cierre
from app.services import periodo as periodo_service
from app.services.email_service import email_service # <-- NUEVO SERVICIO EMAIL

# --- FIN: MODIFICACIÓN ARQUITECTÓNICA ---

# Se importan los schemas de los reportes
from app.schemas import reporte_balance_prueba as schemas_bce
from app.schemas import reporte_balance_prueba_cc as schemas_bce_cc
from pydantic import BaseModel, EmailStr

# --- SCHEMAS PARA EMAIL ---
class EmailDispatchRequest(BaseModel):
    report_type: str  # 'auxiliar_cuenta', 'balance_prueba', 'balance_general', 'estado_resultados', 'tercero_cuenta'
    email_to: EmailStr
    filtros: Dict[str, Any]

router = APIRouter()

# --- NUEVO ENDPOINT CENTRALIZADO PARA ENVÍO DE CORREOS ---
@router.post("/dispatch-email")
def dispatch_report_email(
    payload: EmailDispatchRequest,
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera el PDF del reporte solicitado y lo envía por correo electrónico.
    """
    try:
        pdf_content = None
        filename = "Reporte.pdf"
        subject = "Reporte Contable - Finaxis"

        # --- LOGICA UNIFICADA (REGISTRY PATTERN) ---
        from app.core.reporting_registry import ReportRegistry
        
        # 1. Buscar en el registro
        report_service = ReportRegistry.get(payload.report_type)
        
        if report_service:
            # Polimorfismo: El reporte sabe cómo generarse
            pdf_content, filename_generated = report_service.generate_pdf(db, current_user.empresa_id, payload.filtros)
            filename = filename_generated
            # TODO: Add subject generation to BaseReport interface or keep generic
            subject = f"Reporte {payload.report_type} - {date.today()}"
            
        else:
            # --- FALLBACK A LOGICA LEGADO (MANTENEMOS POR COMPATIBILIDAD DURANTE MIGRACION) ---
            
            # 1. BALANCE DE PRUEBA
            if payload.report_type == 'balance_prueba':
                filtros = schemas_bce.FiltrosBalancePrueba(**payload.filtros)
                pdf_content = reports_service.generate_balance_de_prueba_pdf(db, current_user.empresa_id, filtros)
                filename = f"Balance_Prueba_{filtros.fecha_inicio}_{filtros.fecha_fin}.pdf"
                subject = f"Balance de Prueba ({filtros.fecha_inicio} al {filtros.fecha_fin})"
    
            # 2. BALANCE GENERAL
            elif payload.report_type == 'balance_general':
                fecha_corte = date.fromisoformat(payload.filtros['fecha_corte'])
                pdf_content = documento_service.generate_balance_sheet_report_pdf(db, current_user.empresa_id, fecha_corte)
                filename = f"Balance_General_{fecha_corte}.pdf"
                subject = f"Balance General a {fecha_corte}"
    
            # 3. ESTADO DE RESULTADOS
            elif payload.report_type == 'estado_resultados':
                fecha_inicio = date.fromisoformat(payload.filtros['fecha_inicio'])
                fecha_fin = date.fromisoformat(payload.filtros['fecha_fin'])
                pdf_content = documento_service.generate_income_statement_report_pdf(db, current_user.empresa_id, fecha_inicio, fecha_fin)
                filename = f"Estado_Resultados_{fecha_inicio}_{fecha_fin}.pdf"
                subject = f"Estado de Resultados ({fecha_inicio} al {fecha_fin})"
    
            # 4. AUXILIAR POR CUENTA
            elif payload.report_type == 'auxiliar_cuenta':
                cuenta_id = int(payload.filtros['cuenta_id'])
                fecha_inicio = date.fromisoformat(payload.filtros['fecha_inicio'])
                fecha_fin = date.fromisoformat(payload.filtros['fecha_fin'])
                pdf_content = documento_service.generate_account_ledger_report_pdf(db, current_user.empresa_id, cuenta_id, fecha_inicio, fecha_fin)
                filename = f"Auxiliar_Cuenta_{cuenta_id}.pdf"
                subject = f"Auxiliar Contable ({fecha_inicio} al {fecha_fin})"
    
            # 5. AUXILIAR POR TERCERO
            elif payload.report_type == 'tercero_cuenta':
                tercero_id = int(payload.filtros['tercero_id'])
                fecha_inicio = date.fromisoformat(payload.filtros['fecha_inicio'])
                fecha_fin = date.fromisoformat(payload.filtros['fecha_fin'])
                cuenta_ids = payload.filtros.get('cuenta_ids') # "1,2,3" or None
                parsed_ids = [int(id) for id in cuenta_ids.split(',')] if cuenta_ids else None
                
                pdf_content = documento_service.generate_tercero_account_ledger_report_pdf(
                    db=db,
                    empresa_id=current_user.empresa_id,
                    tercero_id=tercero_id,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    cuenta_ids=parsed_ids
                )
                filename = f"Auxiliar_Tercero_{tercero_id}.pdf"
                subject = f"Auxiliar Tercero ({fecha_inicio} al {fecha_fin})"
    
            # 6. SUPER INFORME INVENTARIOS (Interceptado por Registry si ya se migró, sino aquí)
            # Como ya migramos InventoryReportService, el registry.get lo atrapará arriba.
            
            else:
                 raise HTTPException(status_code=400, detail=f"Tipo de reporte '{payload.report_type}' no soportado para envío por correo.")

        # --- FIN LOGICA UNIFICADA ---
         
        # ENVIAR CORREO
        if pdf_content:
            body = f"Hola,\n\nAdjunto encontrarás el reporte solicitado: {subject}.\n\nGenerado por Finaxis AI."
            success, msg = email_service.send_email_with_pdf(payload.email_to, subject, body, pdf_content, filename, empresa_id=current_user.empresa_id)
            
            if not success:
                raise HTTPException(status_code=500, detail=msg)
            
            return {"message": "Correo enviado exitosamente"}
        
        raise HTTPException(status_code=500, detail="No se pudo generar el PDF por razones desconocidas.")

    except Exception as e:
        print(f"Error dispatching email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# --- RUTAS PARA EL BALANCE DE PRUEBA POR CUENTAS (Sin cambios) ---
@router.post("/balance-de-prueba", response_model=schemas_bce.ReporteBalancePruebaResponse)
def get_balance_de_prueba_report(
    filtros: schemas_bce.FiltrosBalancePrueba,
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """ Genera los datos para el reporte de Balance de Prueba. """
    return reports_service.generate_balance_de_prueba_report(db, current_user.empresa_id, filtros)

@router.post("/balance-de-prueba/get-signed-url", response_model=Dict[str, str])
def get_signed_balance_de_prueba_url(
    filtros: schemas_bce.FiltrosBalancePrueba,
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """ Genera una URL firmada para la descarga del PDF del Balance de Prueba. """
    pdf_endpoint = "/api/reports/balance-de-prueba/imprimir"
    filtros_dict = filtros.model_dump(mode='json')
    
    signed_token = reports_service.generate_signed_report_url(
        endpoint=pdf_endpoint,
        expiration_seconds=60,
        empresa_id=current_user.empresa_id,
        filtros=filtros_dict
    )
    return {"signed_url_token": signed_token}

@router.get("/balance-de-prueba/imprimir")
def get_balance_de_prueba_pdf(
    signed_token: str = Query(..., description="Token de URL firmada"),
    db: Session = Depends(get_db)
):
    """ Sirve el PDF del Balance de Prueba después de verificar la URL firmada. """
    verified_params = reports_service.verify_signed_report_url(signed_token, "/api/reports/balance-de-prueba/imprimir")
    if not verified_params:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="URL inválida o expirada.")

    empresa_id = verified_params["empresa_id"]
    filtros = schemas_bce.FiltrosBalancePrueba(**verified_params["filtros"])
    
    return reports_service.generate_balance_de_prueba_pdf(db, empresa_id, filtros)

# --- RUTAS PARA EL BALANCE DE PRUEBA POR CENTROS DE COSTO (Sin cambios) ---
@router.post("/balance-de-prueba-cc", response_model=schemas_bce_cc.ReporteBalancePruebaCCResponse)
def get_balance_de_prueba_cc_report(
    filtros: schemas_bce_cc.FiltrosBalancePruebaCC,
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """ Genera los datos para el reporte de Balance de Prueba por Centro de Costo. """
    return reports_service.generate_balance_de_prueba_cc_report(db, current_user.empresa_id, filtros)

@router.post("/balance-de-prueba-cc/get-signed-url", response_model=Dict[str, str])
def get_signed_balance_de_prueba_cc_url(
    filtros: schemas_bce_cc.FiltrosBalancePruebaCC,
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """ Genera una URL firmada para la descarga del PDF del Balance de Prueba por CC. """
    pdf_endpoint = "/api/reports/balance-de-prueba-cc/imprimir"
    filtros_dict = filtros.model_dump(mode='json')
    
    signed_token = reports_service.generate_signed_report_url(
        endpoint=pdf_endpoint,
        expiration_seconds=60,
        empresa_id=current_user.empresa_id,
        filtros=filtros_dict
    )
    return {"signed_url_token": signed_token}

@router.get("/balance-de-prueba-cc/imprimir")
def get_balance_de_prueba_cc_pdf(
    signed_token: str = Query(..., description="Token de URL firmada"),
    db: Session = Depends(get_db)
):
    """ Sirve el PDF del Balance de Prueba por CC después de verificar la URL firmada. """
    verified_params = reports_service.verify_signed_report_url(signed_token, "/api/reports/balance-de-prueba-cc/imprimir")
    if not verified_params:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="URL inválida o expirada.")

    empresa_id = verified_params["empresa_id"]
    filtros = schemas_bce_cc.FiltrosBalancePruebaCC(**verified_params["filtros"])
    
    return reports_service.generate_balance_de_prueba_cc_pdf(db, empresa_id, filtros)


# --- INICIO: RUTAS DEL LIBRO DIARIO RECONECTADAS ---
@router.get("/journal", response_model=List[Dict[str, Any]])
def get_journal_report(
    fecha_inicio: date = Query(..., description="Fecha de inicio del reporte (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha de fin del reporte (YYYY-MM-DD)"),
    tipos_documento_ids: Optional[List[int]] = Query(None, description="Lista de IDs de tipos de documento"),
    cuenta_filtro: Optional[str] = Query(None, description="Filtro por código o nombre de cuenta"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera los datos para el reporte del Libro Diario (para la tabla en frontend).
    """
    # MODIFICACIÓN: Ahora llama a nuestro nuevo servicio centralizado
    report_data = libros_oficiales_service.get_data_for_libro_diario(
        db=db,
        empresa_id=current_user.empresa_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        tipos_documento_ids=tipos_documento_ids,
        cuenta_filtro=cuenta_filtro
    )
    return report_data

@router.get("/journal/get-signed-url", response_model=Dict[str, str])
def get_signed_journal_report_url(
    fecha_inicio: date = Query(..., description="Fecha de inicio del reporte (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha de fin del reporte (YYYY-MM-DD)"),
    tipos_documento_ids: Optional[List[int]] = Query(None, description="Lista de IDs de tipos de documento"),
    cuenta_filtro: Optional[str] = Query(None, description="Filtro por código o nombre de cuenta"),
    modo: Optional[str] = Query(None, description="Modo de generación: 'oficial' para cerrar el período"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera una URL firmada y temporal para la descarga del reporte del Libro Diario en PDF.
    Si modo='oficial', intenta cerrar el período antes de generar la URL.
    """
    # Validación: Para cerrar un período, las fechas deben corresponder a un único mes.
    if fecha_inicio.year != fecha_fin.year or fecha_inicio.month != fecha_fin.month:
        if modo == 'oficial':
            raise HTTPException(status_code=400, detail="El Libro Diario Oficial solo puede generarse para un único mes.")

    # Lógica Crítica: Si el modo es 'oficial', intentamos cerrar el período.
    if modo == 'oficial':
        try:
            # El servicio 'cerrar_periodo' ya contiene todas las validaciones (ej. que el anterior esté cerrado).
            # Si alguna validación falla, lanzará una HTTPException que detendrá el proceso aquí.

            periodo_service.cerrar_periodo(db, current_user.empresa_id, fecha_inicio.year, fecha_inicio.month, user_id=current_user.id)
        except HTTPException as e:
            # Re-lanzamos la excepción específica del servicio para que el frontend la muestre.
            raise e
            
    # Si el cierre fue exitoso (o no se requirió), procedemos a generar la URL.
    pdf_endpoint = "/api/reports/journal/imprimir" 
    signed_token = reports_service.generate_signed_report_url(
        endpoint=pdf_endpoint,
        expiration_seconds=60, # Aumentamos la validez
        fecha_inicio=fecha_inicio.isoformat(),
        fecha_fin=fecha_fin.isoformat(),
        empresa_id=current_user.empresa_id,
        tipos_documento_ids=tipos_documento_ids,
        cuenta_filtro=cuenta_filtro
    )
    return {"signed_url_token": signed_token}

@router.get("/journal/imprimir")
def get_journal_report_pdf(
    signed_token: str = Query(..., description="Token de URL firmada para el reporte"),
    db: Session = Depends(get_db)
):
    """
    Sirve el reporte del Libro Diario en formato PDF después de verificar la URL firmada.
    """
    pdf_endpoint = "/api/reports/journal/imprimir"

    verified_params = reports_service.verify_signed_report_url(
        signed_token=signed_token,
        expected_endpoint=pdf_endpoint,
        max_age_seconds=60
    )

    if not verified_params:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="URL de descarga inválida o expirada.")

    fecha_inicio = date.fromisoformat(verified_params["fecha_inicio"])
    fecha_fin = date.fromisoformat(verified_params["fecha_fin"])
    empresa_id = verified_params["empresa_id"]
    tipos_documento_ids = verified_params.get("tipos_documento_ids") # Use .get() as it might be missing in old tokens (though not relevant here) or None values
    cuenta_filtro = verified_params.get("cuenta_filtro")

    # MODIFICACIÓN: Ahora llama a nuestro nuevo servicio centralizado
    pdf_content = libros_oficiales_service.generate_libro_diario_pdf(
        db=db,
        empresa_id=empresa_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        tipos_documento_ids=tipos_documento_ids,
        cuenta_filtro=cuenta_filtro
    )
    from fastapi.responses import Response
    return Response(content=pdf_content, media_type="application/pdf")
# --- FIN: RUTAS DEL LIBRO DIARIO RECONECTADAS ---

# --- INICIO: RUTAS DEL LIBRO DIARIO RESUMEN ---
@router.get("/journal-summary", response_model=List[Dict[str, Any]])
def get_journal_summary_report(
    fecha_inicio: date = Query(..., description="Fecha de inicio (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha de fin (YYYY-MM-DD)"),
    tipos_documento_ids: Optional[str] = Query(None, description="IDs de tipos de documento separados por coma (ej: 1,2,3)"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera los datos para el Libro Diario Resumido (Agrupado por Tipo de Doc).
    """
    parsed_ids = [int(x) for x in tipos_documento_ids.split(',')] if tipos_documento_ids else None
    
    return libros_oficiales_service.get_data_for_libro_diario_resumen(
        db=db,
        empresa_id=current_user.empresa_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        tipos_documento_ids=parsed_ids
    )

@router.get("/journal-summary/get-signed-url", response_model=Dict[str, str])
def get_signed_journal_summary_url(
    fecha_inicio: date = Query(..., description="Fecha de inicio (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha de fin (YYYY-MM-DD)"),
    tipos_documento_ids: Optional[str] = Query(None, description="IDs de tipos de documento separados por coma"),
    modo: Optional[str] = Query(None, description="Modo: 'oficial' para cierre"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera URL firmada para descarga de PDF del Libro Diario Resumido (Oficial).
    """
    if modo == 'oficial':
        # Validar que sea un mes completo o al menos dentro del mismo mes para cierre
        if fecha_inicio.month != fecha_fin.month or fecha_inicio.year != fecha_fin.year:
             raise HTTPException(status_code=400, detail="El Libro Oficial debe generarse para un mes específico para realizar el cierre.")
        
        periodo_service.cerrar_periodo(db, current_user.empresa_id, fecha_inicio.year, fecha_inicio.month, user_id=current_user.id)

    pdf_endpoint = "/api/reports/journal-summary/imprimir"
    
    # Preparamos los parámetros para el token
    params_token = {
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat(),
        "empresa_id": current_user.empresa_id,
        "tipos_documento_ids": tipos_documento_ids # Guardamos string original '1,2,3' o None
    }
    
    signed_token = reports_service.generate_signed_report_url(
        endpoint=pdf_endpoint,
        expiration_seconds=60,
        **params_token
    )
    return {"signed_url_token": signed_token}

@router.get("/journal-summary/imprimir")
def get_journal_summary_pdf(
    signed_token: str = Query(..., description="Token de URL firmada"),
    db: Session = Depends(get_db)
):
    """
    Sirve el PDF del Libro Diario Resumido.
    """
    pdf_endpoint = "/api/reports/journal-summary/imprimir"
    verified_params = reports_service.verify_signed_report_url(signed_token, pdf_endpoint)
    
    if not verified_params:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="URL inválida o expirada.")

    fecha_inicio = date.fromisoformat(verified_params["fecha_inicio"])
    fecha_fin = date.fromisoformat(verified_params["fecha_fin"])
    empresa_id = verified_params["empresa_id"]
    tipos_str = verified_params.get("tipos_documento_ids")
    parsed_ids = [int(x) for x in tipos_str.split(',')] if tipos_str else None

    pdf_content = libros_oficiales_service.generate_libro_diario_resumen_pdf(
        db=db,
        empresa_id=empresa_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        tipos_documento_ids=parsed_ids
    )
    
    from fastapi.responses import Response
    headers = {
        "Content-Disposition": f"inline; filename=Libro_Diario_Resumen_{fecha_inicio}_{fecha_fin}.pdf"
    }
    return Response(content=pdf_content, media_type="application/pdf", headers=headers)
# --- FIN: RUTAS DEL LIBRO DIARIO RESUMEN ---

# --- INICIO: NUEVAS RUTAS PARA LIBRO MAYOR Y BALANCES ---
@router.get("/mayor-y-balances", response_model=Dict[str, Any])
def get_mayor_y_balances_report(
    fecha_inicio: date = Query(..., description="Fecha de inicio del reporte (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha de fin del reporte (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """ Genera los datos para el reporte de Libro Mayor y Balances. """
    return libros_oficiales_service.get_data_for_libro_mayor_y_balances(
        db=db, empresa_id=current_user.empresa_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )

@router.get("/mayor-y-balances/get-signed-url", response_model=Dict[str, str])
def get_signed_mayor_y_balances_url(
    fecha_inicio: date = Query(..., description="Fecha de inicio del reporte (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha de fin del reporte (YYYY-MM-DD)"),
    modo: Optional[str] = Query(None, description="Modo de generación: 'oficial' para cerrar el período"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """ Genera la URL firmada para el Libro Mayor, con lógica de cierre opcional. """
    if fecha_inicio.year != fecha_fin.year or fecha_inicio.month != fecha_fin.month:
        if modo == 'oficial':
            raise HTTPException(status_code=400, detail="El Libro Mayor Oficial solo puede generarse para un único mes.")

    if modo == 'oficial':

        periodo_service.cerrar_periodo(db, current_user.empresa_id, fecha_inicio.year, fecha_inicio.month, user_id=current_user.id)

    pdf_endpoint = "/api/reports/mayor-y-balances/imprimir"
    signed_token = reports_service.generate_signed_report_url(
        endpoint=pdf_endpoint, expiration_seconds=60, fecha_inicio=fecha_inicio.isoformat(),
        fecha_fin=fecha_fin.isoformat(), empresa_id=current_user.empresa_id
    )
    return {"signed_url_token": signed_token}

@router.get("/mayor-y-balances/imprimir")
def get_mayor_y_balances_pdf(
    signed_token: str = Query(..., description="Token de URL firmada"),
    db: Session = Depends(get_db)
):
    """ Sirve el PDF del Libro Mayor y Balances. """
    pdf_endpoint = "/api/reports/mayor-y-balances/imprimir"
    verified_params = reports_service.verify_signed_report_url(signed_token, pdf_endpoint)
    if not verified_params:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="URL de descarga inválida o expirada.")

    # Ahora llamamos a nuestra nueva función de generación de PDF
    pdf_content = libros_oficiales_service.generate_libro_mayor_y_balances_pdf(
        db=db,
        empresa_id=verified_params["empresa_id"],
        fecha_inicio=date.fromisoformat(verified_params["fecha_inicio"]),
        fecha_fin=date.fromisoformat(verified_params["fecha_fin"])
    )
    
    from fastapi.responses import Response
    return Response(content=pdf_content, media_type="application/pdf")

# --- FIN: NUEVAS RUTAS PARA LIBRO MAYOR Y BALANCES ---


# --- INICIO: NUEVAS RUTAS PARA LIBRO DE INVENTARIOS Y BALANCES ---
@router.get("/inventarios-y-balances", response_model=Dict[str, Any])
def get_inventarios_y_balances_report(
    fecha_corte: date = Query(..., description="Fecha de corte del reporte (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """ Genera los datos para el reporte de Libro de Inventarios y Balances. """
    return libros_oficiales_service.get_data_for_inventarios_y_balances(
        db=db, empresa_id=current_user.empresa_id, fecha_corte=fecha_corte
    )

@router.get("/inventarios-y-balances/get-signed-url", response_model=Dict[str, str])
def get_signed_inventarios_y_balances_url(
    fecha_corte: date = Query(..., description="Fecha de corte del reporte (YYYY-MM-DD)"),
    modo: Optional[str] = Query(None, description="Modo de generación: 'oficial' para cerrar el período"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """ Genera la URL firmada para el Libro de Inventarios, con lógica de cierre opcional. """
    if modo == 'oficial':

        periodo_service.cerrar_periodo(db, current_user.empresa_id, fecha_corte.year, fecha_corte.month, user_id=current_user.id)

    pdf_endpoint = "/api/reports/inventarios-y-balances/imprimir"
    signed_token = reports_service.generate_signed_report_url(
        endpoint=pdf_endpoint, expiration_seconds=60, fecha_corte=fecha_corte.isoformat(),
        empresa_id=current_user.empresa_id
    )
    return {"signed_url_token": signed_token}

@router.get("/inventarios-y-balances/imprimir")
def get_inventarios_y_balances_pdf(
    signed_token: str = Query(..., description="Token de URL firmada"),
    db: Session = Depends(get_db)
):
    """ Sirve el PDF del Libro de Inventarios y Balances. """
    pdf_endpoint = "/api/reports/inventarios-y-balances/imprimir"
    verified_params = reports_service.verify_signed_report_url(signed_token, pdf_endpoint)
    if not verified_params:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="URL de descarga inválida o expirada.")

    # Llamamos a la función final de generación de PDF
    pdf_content = libros_oficiales_service.generate_inventarios_y_balances_pdf(
        db=db,
        empresa_id=verified_params["empresa_id"],
        fecha_corte=date.fromisoformat(verified_params["fecha_corte"])
    )
    
    from fastapi.responses import Response
    return Response(content=pdf_content, media_type="application/pdf")
    
# --- FIN: NUEVAS RUTAS PARA LIBRO DE INVENTARIOS Y BALANCES ---

# --- RUTAS PARA REPORTE AUXILIAR POR CUENTA (Sin cambios) ---
@router.get("/account-ledger", response_model=Dict[str, Any])
def get_account_ledger_report(
    cuenta_id: int = Query(..., description="ID de la cuenta para el reporte"),
    fecha_inicio: date = Query(..., description="Fecha de inicio del reporte (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha de fin del reporte (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera el reporte Auxiliar por Cuenta.
    """
    report_data = documento_service.generate_account_ledger_report(
        db=db,
        empresa_id=current_user.empresa_id,
        cuenta_id=cuenta_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )
    return report_data

@router.get("/account-ledger/get-signed-url", response_model=Dict[str, str])
def get_signed_account_ledger_report_url(
    cuenta_id: int = Query(..., description="ID de la cuenta para el reporte"),
    fecha_inicio: date = Query(..., description="Fecha de inicio del reporte (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha de fin del reporte (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera una URL firmada y temporal para la descarga del reporte Auxiliar por Cuenta en PDF.
    """
    pdf_endpoint = "/api/reports/account-ledger/imprimir" 

    signed_token = reports_service.generate_signed_report_url(
        endpoint=pdf_endpoint,
        expiration_seconds=15, 
        fecha_inicio=fecha_inicio.isoformat(),
        fecha_fin=fecha_fin.isoformat(),
        empresa_id=current_user.empresa_id,
        cuenta_id=cuenta_id
    )
    return {"signed_url_token": signed_token}

@router.get("/account-ledger/imprimir")
def get_account_ledger_report_pdf(
    signed_token: str = Query(..., description="Token de URL firmada para el reporte"),
    db: Session = Depends(get_db)
):
    """
    Sirve el reporte Auxiliar por Cuenta en formato PDF después de verificar la URL firmada.
    """
    pdf_endpoint = "/api/reports/account-ledger/imprimir"

    verified_params = reports_service.verify_signed_report_url(
        signed_token=signed_token,
        expected_endpoint=pdf_endpoint,
        max_age_seconds=60 
    )

    if not verified_params:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="URL de descarga inválida o expirada.")

    fecha_inicio = date.fromisoformat(verified_params["fecha_inicio"])
    fecha_fin = date.fromisoformat(verified_params["fecha_fin"])
    empresa_id = verified_params["empresa_id"]
    cuenta_id = verified_params["cuenta_id"]

    pdf_content = documento_service.generate_account_ledger_report_pdf(
        db=db,
        empresa_id=empresa_id,
        cuenta_id=cuenta_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )
    from fastapi.responses import Response
    headers = {
        "Content-Disposition": f"attachment; filename=Auxiliar_Cuenta_{cuenta_id}_{fecha_inicio}_{fecha_fin}.pdf"
    }
    return Response(content=pdf_content, media_type="application/pdf", headers=headers)

# --- RUTAS PARA REPORTES RESTANTES (Sin cambios) ---
# ... (el resto del archivo permanece igual) ...
# --- COPIADO HASTA EL FINAL ---
   # --- RUTAS PARA REPORTE AUXILIAR POR TERCERO Y CUENTA ---
@router.get("/tercero-cuenta", response_model=Dict[str, Any])
def get_tercero_cuenta_report(
    tercero_id: int = Query(..., description="ID del tercero para el reporte"),
    fecha_inicio: date = Query(..., description="Fecha de inicio del reporte (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha de fin del reporte (YYYY-MM-DD)"),
    cuenta_ids: Optional[str] = Query(None, description="IDs de las cuentas a filtrar, separadas por coma"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera el reporte Auxiliar por Tercero y Cuenta.
    """
    parsed_cuenta_ids = [int(id) for id in cuenta_ids.split(',')] if cuenta_ids else None

    report_data = documento_service.generate_tercero_account_ledger_report( # <-- Esta función debe existir en services/documento.py
        db=db,
        empresa_id=current_user.empresa_id,
        tercero_id=tercero_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        cuenta_ids=parsed_cuenta_ids
    )
    return report_data

@router.get("/tercero-cuenta/get-signed-url", response_model=Dict[str, str])
def get_signed_tercero_cuenta_report_url(
    tercero_id: int = Query(..., description="ID del tercero para el reporte"),
    fecha_inicio: date = Query(..., description="Fecha de inicio del reporte (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha de fin del reporte (YYYY-MM-DD)"),
    cuenta_ids: Optional[str] = Query(None, description="IDs de las cuentas a filtrar, separadas por coma"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera una URL firmada y temporal para la descarga del reporte Auxiliar por Tercero en PDF.
    """
    pdf_endpoint = "/api/reports/tercero-cuenta/imprimir"

    parsed_cuenta_ids = [int(id) for id in cuenta_ids.split(',')] if cuenta_ids else None

    signed_token = reports_service.generate_signed_report_url(
        endpoint=pdf_endpoint,
        expiration_seconds=15, # La URL será válida por 15 segundos
        fecha_inicio=fecha_inicio.isoformat(),
        fecha_fin=fecha_fin.isoformat(),
        empresa_id=current_user.empresa_id,
        tercero_id=tercero_id,
        cuenta_ids=parsed_cuenta_ids # Pasar como lista de IDs o None
    )
    return {"signed_url_token": signed_token}

@router.get("/tercero-cuenta/imprimir")
def get_tercero_cuenta_report_pdf(
    signed_token: str = Query(..., description="Token de URL firmada para el reporte"),
    db: Session = Depends(get_db)
):
    """
    Sirve el reporte Auxiliar por Tercero y Cuenta en formato PDF después de verificar la URL firmada.
    """
    pdf_endpoint = "/api/reports/tercero-cuenta/imprimir"
    verified_params = reports_service.verify_signed_report_url(
        signed_token=signed_token,
        expected_endpoint=pdf_endpoint,
        max_age_seconds=60
    )
    if not verified_params:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="URL de descarga inválida o expirada.")

    # Extraer parámetros verificados del token
    fecha_inicio = date.fromisoformat(verified_params["fecha_inicio"])
    fecha_fin = date.fromisoformat(verified_params["fecha_fin"])
    empresa_id = verified_params["empresa_id"]
    tercero_id = verified_params["tercero_id"]
    cuenta_ids = verified_params.get("cuenta_ids") # Puede ser None o lista de IDs

    pdf_content = documento_service.generate_tercero_account_ledger_report_pdf( # <-- Esta función debe existir en services/documento.py
        db=db,
        empresa_id=empresa_id,
        tercero_id=tercero_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        cuenta_ids=cuenta_ids
    )
    from fastapi.responses import Response
    headers = {
        "Content-Disposition": f"attachment; filename=Auxiliar_Tercero_{tercero_id}_{fecha_inicio}_{fecha_fin}.pdf"
    }
    return Response(content=pdf_content, media_type="application/pdf", headers=headers)

    # --- RUTAS PARA REPORTE ESTADO DE RESULTADOS ---
@router.get("/income-statement", response_model=Dict[str, Any])
def get_income_statement_report(
    fecha_inicio: date = Query(..., description="Fecha de inicio del reporte (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha de fin del reporte (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera los datos para el reporte de Estado de Resultados.
    """
    report_data = documento_service.generate_income_statement_report( # <-- Esta función debe existir en services/documento.py
        db=db,
        empresa_id=current_user.empresa_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )
    return report_data

@router.get("/income-statement/get-signed-url", response_model=Dict[str, str])
def get_signed_income_statement_report_url(
    fecha_inicio: date = Query(..., description="Fecha de inicio del reporte (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha de fin del reporte (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera una URL firmada y temporal para la descarga del reporte de Estado de Resultados en PDF.
    """
    pdf_endpoint = "/api/reports/income-statement/imprimir" 

    signed_token = reports_service.generate_signed_report_url(
        endpoint=pdf_endpoint,
        expiration_seconds=15, # La URL será válida por 15 segundos
        fecha_inicio=fecha_inicio.isoformat(),
        fecha_fin=fecha_fin.isoformat(),
        empresa_id=current_user.empresa_id
    )
    return {"signed_url_token": signed_token}

@router.get("/income-statement/imprimir")
def get_income_statement_report_pdf(
    signed_token: str = Query(..., description="Token de URL firmada para el reporte"),
    db: Session = Depends(get_db)
):
    """
    Sirve el reporte de Estado de Resultados en formato PDF después de verificar la URL firmada.
    """
    pdf_endpoint = "/api/reports/income-statement/imprimir"
    verified_params = reports_service.verify_signed_report_url(
        signed_token=signed_token,
        expected_endpoint=pdf_endpoint,
        max_age_seconds=60 
    )
    if not verified_params:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="URL de descarga inválida o expirada.")

    # Extraer parámetros verificados del token
    fecha_inicio = date.fromisoformat(verified_params["fecha_inicio"])
    fecha_fin = date.fromisoformat(verified_params["fecha_fin"])
    empresa_id = verified_params["empresa_id"]

    pdf_content = documento_service.generate_income_statement_report_pdf( # <-- Esta función debe existir en services/documento.py
        db=db,
        empresa_id=empresa_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )
    from fastapi.responses import Response
    return Response(content=pdf_content, media_type="application/pdf")


# --- NUEVO: REPORTE RELACIÓN DE SALDOS (CUENTA Y TERCEROS) ---
@router.get("/relacion-saldos", response_model=List[Dict[str, Any]])
def get_relacion_saldos_report(
    fecha_inicio: date = Query(..., description="Fecha Inicio"),
    fecha_fin: date = Query(..., description="Fecha Fin"),
    cuenta_ids: Optional[str] = Query(None, description="IDs Cuentas (separados por coma)"),
    tercero_ids: Optional[str] = Query(None, description="IDs Terceros (separados por coma)"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    filtros = {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "cuenta_ids": [int(x) for x in cuenta_ids.split(',')] if cuenta_ids else None,
        "tercero_ids": [int(x) for x in tercero_ids.split(',')] if tercero_ids else None
    }
    return reports_service.generate_relacion_saldos_report(db, current_user.empresa_id, filtros)

@router.get("/relacion-saldos/get-signed-url", response_model=Dict[str, str])
def get_signed_relacion_saldos_url(
    fecha_inicio: date = Query(..., description="Fecha Inicio"),
    fecha_fin: date = Query(..., description="Fecha Fin"),
    cuenta_ids: Optional[str] = Query(None, description="IDs Cuentas"),
    tercero_ids: Optional[str] = Query(None, description="IDs Terceros"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    pdf_endpoint = "/api/reports/relacion-saldos/imprimir"
    params = {
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat(),
        "cuenta_ids": [int(x) for x in cuenta_ids.split(',')] if cuenta_ids else None,
        "tercero_ids": [int(x) for x in tercero_ids.split(',')] if tercero_ids else None,
        "empresa_id": current_user.empresa_id
    }
    signed_token = reports_service.generate_signed_report_url(
        endpoint=pdf_endpoint,
        expiration_seconds=60,
        **params
    )
    return {"signed_url_token": signed_token}

@router.get("/relacion-saldos/imprimir")
def print_relacion_saldos_pdf(
    signed_token: str = Query(...),
    db: Session = Depends(get_db)
):
    try:
        decoded_data = reports_service.decode_signed_report_token(signed_token)
        # Parse params back
        filtros = {
            "fecha_inicio": datetime.fromisoformat(decoded_data["fecha_inicio"]).date(),
            "fecha_fin": datetime.fromisoformat(decoded_data["fecha_fin"]).date(),
            "cuenta_ids": decoded_data.get("cuenta_ids"),
            "tercero_ids": decoded_data.get("tercero_ids")
        }
        
        pdf_content = reports_service.generate_relacion_saldos_pdf(db, decoded_data["empresa_id"], filtros)
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=Relacion_Saldos_{filtros['fecha_fin']}.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- NUEVO: AUXILIAR INVERSO (Cuenta -> Terceros) ---
# Se usa para la vista "Por Cuenta" del Auxiliar de Terceros
@router.get("/auxiliar-inverso", response_model=Dict[str, Any])
def get_auxiliar_inverso_report(
    cuenta_id: int = Query(..., description="Cuenta Principal"),
    fecha_inicio: date = Query(..., description="Fecha Inicio"),
    fecha_fin: date = Query(..., description="Fecha Fin"),
    tercero_ids: Optional[str] = Query(None, description="IDs Terceros a filtrar (opcional)"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    filtros = {
        "cuenta_id": cuenta_id,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "tercero_ids": [int(x) for x in tercero_ids.split(',')] if tercero_ids else None
    }
    return reports_service.generate_auxiliar_inverso_report(db, current_user.empresa_id, filtros)

@router.get("/auxiliar-inverso/get-signed-url", response_model=Dict[str, str])
def get_signed_auxiliar_inverso_url(
    cuenta_id: int = Query(..., description="Cuenta Principal"),
    fecha_inicio: date = Query(..., description="Fecha Inicio"),
    fecha_fin: date = Query(..., description="Fecha Fin"),
    tercero_ids: Optional[str] = Query(None, description="IDs Terceros"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    pdf_endpoint = "/api/reports/auxiliar-inverso/imprimir"
    params = {
        "cuenta_id": cuenta_id,
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat(),
        "tercero_ids": [int(x) for x in tercero_ids.split(',')] if tercero_ids else None,
        "empresa_id": current_user.empresa_id
    }
    signed_token = reports_service.generate_signed_report_url(
        endpoint=pdf_endpoint,
        expiration_seconds=60,
        **params
    )
    return {"signed_url_token": signed_token}

@router.get("/auxiliar-inverso/imprimir")
def get_auxiliar_inverso_pdf(
    signed_token: str = Query(..., description="Token"),
    db: Session = Depends(get_db)
):
    pdf_endpoint = "/api/reports/auxiliar-inverso/imprimir"
    verified_params = reports_service.verify_signed_report_url(signed_token, pdf_endpoint)
    if not verified_params:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="URL inválida.")
        
    fecha_inicio = date.fromisoformat(verified_params["fecha_inicio"])
    fecha_fin = date.fromisoformat(verified_params["fecha_fin"])
    empresa_id = verified_params["empresa_id"]
    cuenta_id = verified_params["cuenta_id"]
    tercero_ids = verified_params.get("tercero_ids")
    
    filtros = {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "cuenta_id": cuenta_id,
        "tercero_ids": tercero_ids
    }
    
    pdf_content = reports_service.generate_auxiliar_inverso_pdf(db, empresa_id, filtros)
    return Response(content=pdf_content, media_type="application/pdf")


# --- RUTAS PARA REPORTE ESTADO DE RESULTADOS POR CENTRO DE COSTO ---
@router.get("/income-statement-cc", response_model=Dict[str, Any])
def get_income_statement_cc_report(
    fecha_inicio: date = Query(..., description="Fecha de inicio del reporte (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha de fin del reporte (YYYY-MM-DD)"),
    centro_costo_id: Optional[int] = Query(None, description="ID del Centro de Costo para filtrar"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera los datos para el reporte de Estado de Resultados por Centro de Costo.
    """
    report_data = documento_service.generate_income_statement_cc_report( # <-- Esta función debe existir en services/documento.py
        db=db,
        empresa_id=current_user.empresa_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        centro_costo_id=centro_costo_id
    )
    return report_data

@router.get("/income-statement-cc/get-signed-url", response_model=Dict[str, str])
def get_signed_income_statement_cc_report_url(
    fecha_inicio: date = Query(..., description="Fecha de inicio del reporte (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha de fin del reporte (YYYY-MM-DD)"),
    centro_costo_id: Optional[int] = Query(None, description="ID del Centro de Costo para filtrar"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera una URL firmada y temporal para la descarga del reporte de Estado de Resultados por Centro de Costo en PDF.
    """
    pdf_endpoint = "/api/reports/income-statement-cc/imprimir"
    signed_token = reports_service.generate_signed_report_url(
        endpoint=pdf_endpoint,
        expiration_seconds=15, # La URL será válida por 15 segundos
        # Los parámetros del reporte que irán dentro del token firmado
        fecha_inicio=fecha_inicio.isoformat(),
        fecha_fin=fecha_fin.isoformat(),
        empresa_id=current_user.empresa_id, # <-- empresa_id SEGURO, del token JWT
        centro_costo_id=centro_costo_id
    )
    return {"signed_url_token": signed_token}

@router.get("/income-statement-cc/imprimir")
def get_income_statement_cc_report_pdf(
    signed_token: str = Query(..., description="Token de URL firmada para el reporte"),
    db: Session = Depends(get_db)
):
    """
    Sirve el reporte de Estado de Resultados por Centro de Costo en formato PDF después de verificar la URL firmada.
    """
    pdf_endpoint = "/api/reports/income-statement-cc/imprimir"
    verified_params = reports_service.verify_signed_report_url(
        signed_token=signed_token,
        expected_endpoint=pdf_endpoint,
        max_age_seconds=60 # El token es válido por hasta 60 segundos para verificación
    )

    if not verified_params:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="URL de descarga inválida o expirada.")

    # Extraer parámetros verificados del token
    fecha_inicio = date.fromisoformat(verified_params["fecha_inicio"])
    fecha_fin = date.fromisoformat(verified_params["fecha_fin"])
    empresa_id = verified_params["empresa_id"] # <-- empresa_id SEGURO, extraído del token firmado
    centro_costo_id = verified_params["centro_costo_id"]

    pdf_content = documento_service.generate_income_statement_cc_report_pdf( # <-- Esta función debe existir en services/documento.py
        db=db,
        empresa_id=empresa_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        centro_costo_id=centro_costo_id
    )
    from fastapi.responses import Response
    return Response(content=pdf_content, media_type="application/pdf")

    # --- RUTAS PARA REPORTE AUXILIAR POR CENTRO DE COSTO Y CUENTA ---

@router.get("/auxiliar-cc-cuenta", response_model=Dict[str, Any]) # <--- CAMBIADO A Dict[str, Any]
def get_auxiliar_cc_cuenta_report(
    centro_costo_id: int = Query(..., description="ID del Centro de Costo para filtrar"),
    fecha_inicio: date = Query(..., description="Fecha de inicio del reporte (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha de fin del reporte (YYYY-MM-DD)"),
    cuenta_id: Optional[int] = Query(None, description="ID de la Cuenta Contable para filtrar"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera los datos para el reporte Auxiliar por Centro de Costo y Cuenta.
    """
    report_data = documento_service.generate_auxiliar_cc_cuenta_report( # <-- Esta función debe existir en services/documento.py
        db=db,
        empresa_id=current_user.empresa_id,
        centro_costo_id=centro_costo_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        cuenta_id=cuenta_id
    )
    return report_data

@router.get("/auxiliar-cc-cuenta/get-signed-url", response_model=Dict[str, str])
def get_signed_auxiliar_cc_cuenta_report_url(
    centro_costo_id: int = Query(..., description="ID del Centro de Costo para filtrar"),
    fecha_inicio: date = Query(..., description="Fecha de inicio del reporte (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha de fin del reporte (YYYY-MM-DD)"),
    cuenta_id: Optional[int] = Query(None, description="ID de la Cuenta Contable para filtrar"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera una URL firmada y temporal para la descarga del reporte Auxiliar por Centro de Costo y Cuenta en PDF.
    """
    pdf_endpoint = "/api/reports/auxiliar-cc-cuenta/imprimir"
    signed_token = reports_service.generate_signed_report_url(
        endpoint=pdf_endpoint,
        expiration_seconds=15, # La URL será válida por 15 segundos
        # Los parámetros del reporte que irán dentro del token firmado
        centro_costo_id=centro_costo_id,
        fecha_inicio=fecha_inicio.isoformat(),
        fecha_fin=fecha_fin.isoformat(),
        empresa_id=current_user.empresa_id, # <-- empresa_id SEGURO, del token JWT
        cuenta_id=cuenta_id
    )
    return {"signed_url_token": signed_token}

@router.get("/auxiliar-cc-cuenta/imprimir")
def get_auxiliar_cc_cuenta_report_pdf(
    signed_token: str = Query(..., description="Token de URL firmada para el reporte"),
    db: Session = Depends(get_db)
):
    """
    Sirve el reporte Auxiliar por Centro de Costo y Cuenta en formato PDF después de verificar la URL firmada.
    """
    pdf_endpoint = "/api/reports/auxiliar-cc-cuenta/imprimir"
    verified_params = reports_service.verify_signed_report_url(
        signed_token=signed_token,
        expected_endpoint=pdf_endpoint,
        max_age_seconds=60 # El token es válido por hasta 60 segundos para verificación
    )

    if not verified_params:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="URL de descarga inválida o expirada.")

    # Extraer parámetros verificados del token
    centro_costo_id = verified_params["centro_costo_id"]
    fecha_inicio = date.fromisoformat(verified_params["fecha_inicio"])
    fecha_fin = date.fromisoformat(verified_params["fecha_fin"])
    empresa_id = verified_params["empresa_id"] # <-- empresa_id SEGURO, extraído del token firmado
    cuenta_id = verified_params["cuenta_id"]

    pdf_content = documento_service.generate_auxiliar_cc_cuenta_report_pdf( # <-- Esta función debe existir en services/documento.py
        db=db,
        empresa_id=empresa_id,
        centro_costo_id=centro_costo_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        cuenta_id=cuenta_id
    )
    from fastapi.responses import Response
    return Response(content=pdf_content, media_type="application/pdf")

    # --- RUTAS PARA REPORTE BALANCE GENERAL ---

@router.get("/balance-sheet", response_model=Dict[str, Any])
def get_balance_sheet_report(
    fecha_corte: date = Query(..., description="Fecha de corte del reporte (YYYY-MM-DD)"),
    nivel: str = Query("auxiliar", description="Nivel de presentación: 'auxiliar', 'mayor', 'clasificado'"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera los datos para el reporte de Balance General (para la tabla en frontend).
    """
    # Esta función la crearemos en el siguiente lote en services/documento.py
    report_data = documento_service.generate_balance_sheet_report(
        db=db,
        empresa_id=current_user.empresa_id,
        fecha_corte=fecha_corte,
        nivel=nivel
    )
    return report_data

@router.get("/balance-sheet/get-signed-url", response_model=Dict[str, Any])
def get_signed_balance_sheet_report_url(
    fecha_corte: date = Query(..., description="Fecha de corte del reporte (YYYY-MM-DD)"),
    nivel: str = Query("auxiliar", description="Nivel de presentación: 'auxiliar', 'mayor', 'clasificado'"),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera una URL firmada y temporal para la descarga del reporte de Balance General en PDF.
    """
    pdf_endpoint = "/api/reports/balance-sheet/imprimir"
    
    signed_token = reports_service.generate_signed_report_url(
        endpoint=pdf_endpoint,
        expiration_seconds=60,
        fecha_corte=fecha_corte.isoformat(),
        empresa_id=current_user.empresa_id,
        nivel=nivel
    )
    return {"signed_url_token": signed_token}

@router.get("/balance-sheet/imprimir")
def get_balance_sheet_report_pdf(
    signed_token: str = Query(..., description="Token de URL firmada para el reporte"),
    db: Session = Depends(get_db)
):
    """
    Sirve el reporte de Balance General en formato PDF después de verificar la URL firmada.
    """
    pdf_endpoint = "/api/reports/balance-sheet/imprimir"

    verified_params = reports_service.verify_signed_report_url(
        signed_token=signed_token,
        expected_endpoint=pdf_endpoint,
        max_age_seconds=60
    )

    if not verified_params:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="URL de descarga inválida o expirada.")

    fecha_corte = date.fromisoformat(verified_params["fecha_corte"])
    empresa_id = verified_params["empresa_id"]
    nivel = verified_params.get("nivel", "auxiliar")

    # Esta función la crearemos en el siguiente lote en services/documento.py
    pdf_content = documento_service.generate_balance_sheet_report_pdf(
        db=db,
        empresa_id=empresa_id,
        fecha_corte=fecha_corte,
        nivel=nivel
    )
    from fastapi.responses import Response
    return Response(content=pdf_content, media_type="application/pdf")

# --- RUTAS PARA REPORTE BALANCE GENERAL POR CENTRO DE COSTO ---

@router.get("/balance-sheet-cc", response_model=Dict[str, Any])
def get_balance_sheet_cc_report(
    fecha_corte: date = Query(..., description="Fecha de corte del reporte (YYYY-MM-DD)"),
    centro_costo_id: Optional[int] = Query(None, description="ID del Centro de Costo para filtrar (opcional)"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera los datos para el reporte de Balance General por Centro de Costo.
    """
    report_data = documento_service.generate_balance_sheet_cc_report(
        db=db,
        empresa_id=current_user.empresa_id,
        fecha_corte=fecha_corte,
        centro_costo_id=centro_costo_id
    )
    return report_data

@router.get("/balance-sheet-cc/get-signed-url", response_model=Dict[str, str])
def get_signed_balance_sheet_cc_report_url(
    fecha_corte: date = Query(..., description="Fecha de corte del reporte (YYYY-MM-DD)"),
    centro_costo_id: Optional[int] = Query(None, description="ID del Centro de Costo para filtrar (opcional)"),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera una URL firmada para la descarga del PDF del Balance General por C. Costo.
    """
    pdf_endpoint = "/api/reports/balance-sheet-cc/imprimir"

    signed_token = reports_service.generate_signed_report_url(
        endpoint=pdf_endpoint,
        expiration_seconds=15,
        fecha_corte=fecha_corte.isoformat(),
        empresa_id=current_user.empresa_id,
        centro_costo_id=centro_costo_id
    )
    return {"signed_url_token": signed_token}

@router.get("/balance-sheet-cc/imprimir")
def get_balance_sheet_cc_report_pdf(
    signed_token: str = Query(..., description="Token de URL firmada para el reporte"),
    db: Session = Depends(get_db)
):
    """
    Sirve el PDF del Balance General por C. Costo después de verificar la URL firmada.
    """
    pdf_endpoint = "/api/reports/balance-sheet-cc/imprimir"

    verified_params = reports_service.verify_signed_report_url(
        signed_token=signed_token,
        expected_endpoint=pdf_endpoint,
        max_age_seconds=60
    )

    if not verified_params:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="URL de descarga inválida o expirada.")

    fecha_corte = date.fromisoformat(verified_params["fecha_corte"])
    empresa_id = verified_params["empresa_id"]
    centro_costo_id = verified_params.get("centro_costo_id") # .get() para manejar el caso de None

    pdf_content = documento_service.generate_balance_sheet_cc_report_pdf(
        db=db,
        empresa_id=empresa_id,
        fecha_corte=fecha_corte,
        centro_costo_id=centro_costo_id
    )
    from fastapi.responses import Response
    return Response(content=pdf_content, media_type="application/pdf")

# --- RUTA PARA NUEVO REPORTE AUXILIAR DE CARTERA (CON PERSPECTIVAS) ---

@router.get("/auxiliar-cartera", response_model=Dict[str, Any])
def get_auxiliar_cartera_report(
    tercero_id: int = Query(..., description="ID del tercero (cliente)"),
    fecha_inicio: date = Query(..., description="Fecha de inicio del reporte"),
    fecha_fin: date = Query(..., description="Fecha de fin del reporte"),
    perspective: str = Query("facturas", description="Perspectiva del reporte: 'facturas' o 'recibos'"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera los datos para el reporte de Auxiliar de Cartera Detallado,
    eligiendo la perspectiva entre facturas o recibos.
    """
    if perspective == 'facturas':
        report_data = documento_service.generate_auxiliar_por_facturas(
            db=db,
            empresa_id=current_user.empresa_id,
            tercero_id=tercero_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
    elif perspective == 'recibos':
        report_data = documento_service.generate_auxiliar_por_recibos(
            db=db,
            empresa_id=current_user.empresa_id,
            tercero_id=tercero_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
    else:
        raise HTTPException(status_code=400, detail="Perspectiva no válida. Debe ser 'facturas' or 'recibos'.")
    
    return report_data

@router.get("/auxiliar-cartera/get-signed-url", response_model=Dict[str, str])
def get_signed_auxiliar_cartera_report_url(
    tercero_id: int = Query(..., description="ID del tercero (cliente)"),
    fecha_inicio: date = Query(..., description="Fecha de inicio del reporte"),
    fecha_fin: date = Query(..., description="Fecha de fin del reporte"),
    perspective: str = Query("facturas", description="Perspectiva del reporte"),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera una URL firmada para la descarga del PDF del Auxiliar de Cartera.
    Ahora incluye la perspectiva en el token.
    """
    pdf_endpoint = "/api/reports/auxiliar-cartera/imprimir"
    
    signed_token = reports_service.generate_signed_report_url(
        endpoint=pdf_endpoint,
        expiration_seconds=60, # Aumentamos a 60 segundos
        tercero_id=tercero_id,
        fecha_inicio=fecha_inicio.isoformat(),
        fecha_fin=fecha_fin.isoformat(),
        empresa_id=current_user.empresa_id,
        perspective=perspective # <--- NUEVO: La perspectiva viaja en el token
    )
    return {"signed_url_token": signed_token}


@router.get("/auxiliar-cartera/imprimir")
def get_auxiliar_cartera_report_pdf(
    signed_token: str = Query(..., description="Token de URL firmada"),
    db: Session = Depends(get_db)
):
    """
    Sirve el PDF del Auxiliar de Cartera después de verificar la URL firmada.
    Ahora elige qué PDF generar basado en la perspectiva.
    """
    verified_params = reports_service.verify_signed_report_url(signed_token, "/api/reports/auxiliar-cartera/imprimir", 90)
    if not verified_params:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="URL de descarga inválida o expirada.")

    # Extraer parámetros del token
    tercero_id = verified_params["tercero_id"]
    fecha_inicio = date.fromisoformat(verified_params["fecha_inicio"])
    fecha_fin = date.fromisoformat(verified_params["fecha_fin"])
    empresa_id = verified_params["empresa_id"]
    perspective = verified_params.get("perspective", "facturas") # Extraer perspectiva

    # Lógica condicional para llamar al servicio de PDF correcto
    if perspective == 'facturas':
        pdf_content = documento_service.generate_auxiliar_por_facturas_pdf(
            db, empresa_id, tercero_id, fecha_inicio, fecha_fin
        )
    elif perspective == 'recibos':
        pdf_content = documento_service.generate_auxiliar_por_recibos_pdf(
            db, empresa_id, tercero_id, fecha_inicio, fecha_fin
        )
    else:
        # Esto es un caso de borde, no debería ocurrir si el token es válido
        raise HTTPException(status_code=400, detail="Perspectiva en token no válida.")

    from fastapi.responses import Response
    return Response(content=pdf_content, media_type="application/pdf")

# --- RUTAS PARA REPORTE AUXILIAR DE PROVEEDORES (CON PERSPECTIVAS) ---

@router.get("/auxiliar-proveedores", response_model=Dict[str, Any])
def get_auxiliar_proveedores_report(
    tercero_id: int = Query(..., description="ID del tercero (proveedor)"),
    fecha_inicio: date = Query(..., description="Fecha de inicio del reporte"),
    fecha_fin: date = Query(..., description="Fecha de fin del reporte"),
    perspective: str = Query("facturas", description="Perspectiva del reporte: 'facturas' o 'recibos'"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera los datos para el reporte de Auxiliar de Proveedores Detallado.
    """
    if perspective == 'facturas':
        report_data = documento_service.generate_auxiliar_proveedores_por_facturas(
            db, empresa_id=current_user.empresa_id, tercero_id=tercero_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
        )
    elif perspective == 'recibos':
        report_data = documento_service.generate_auxiliar_proveedores_por_recibos(
            db, empresa_id=current_user.empresa_id, tercero_id=tercero_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
        )
    else:
        raise HTTPException(status_code=400, detail="Perspectiva no válida.")
    
    return report_data


@router.get("/auxiliar-proveedores/get-signed-url", response_model=Dict[str, str])
def get_signed_auxiliar_proveedores_report_url(
    tercero_id: int = Query(..., description="ID del tercero (proveedor)"),
    fecha_inicio: date = Query(..., description="Fecha de inicio del reporte"),
    fecha_fin: date = Query(..., description="Fecha de fin del reporte"),
    perspective: str = Query("facturas", description="Perspectiva del reporte"),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera una URL firmada para la descarga del PDF del Auxiliar de Proveedores.
    """
    pdf_endpoint = "/api/reports/auxiliar-proveedores/imprimir"
    
    signed_token = reports_service.generate_signed_report_url(
        endpoint=pdf_endpoint,
        expiration_seconds=60,
        tercero_id=tercero_id,
        fecha_inicio=fecha_inicio.isoformat(),
        fecha_fin=fecha_fin.isoformat(),
        empresa_id=current_user.empresa_id,
        perspective=perspective
    )
    return {"signed_url_token": signed_token}


@router.get("/auxiliar-proveedores/imprimir")
def get_auxiliar_proveedores_report_pdf(
    signed_token: str = Query(..., description="Token de URL firmada"),
    db: Session = Depends(get_db)
):
    """
    Sirve el PDF del Auxiliar de Proveedores después de verificar la URL firmada.
    """
    verified_params = reports_service.verify_signed_report_url(signed_token, "/api/reports/auxiliar-proveedores/imprimir", 90)
    if not verified_params:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="URL de descarga inválida o expirada.")

    tercero_id = verified_params["tercero_id"]
    fecha_inicio = date.fromisoformat(verified_params["fecha_inicio"])
    fecha_fin = date.fromisoformat(verified_params["fecha_fin"])
    empresa_id = verified_params["empresa_id"]
    perspective = verified_params.get("perspective", "facturas")

    if perspective == 'facturas':
        pdf_content = documento_service.generate_auxiliar_proveedores_por_facturas_pdf(
            db, empresa_id, tercero_id, fecha_inicio, fecha_fin
        )
    elif perspective == 'recibos':
        pdf_content = documento_service.generate_auxiliar_proveedores_por_recibos_pdf(
            db, empresa_id, tercero_id, fecha_inicio, fecha_fin
        )
    else:
        raise HTTPException(status_code=400, detail="Perspectiva en token no válida.")

    from fastapi.responses import Response
    return Response(content=pdf_content, media_type="application/pdf")

# --- RUTAS PARA REPORTE ESTADO DE CUENTA POR CLIENTE ---

@router.get("/estado-cuenta-cliente", response_model=Dict[str, Any])
def get_estado_cuenta_cliente_report(
    tercero_id: int = Query(..., description="ID del tercero (cliente)"),
    fecha_fin: date = Query(..., description="Fecha de corte del reporte"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera los datos para el reporte de Estado de Cuenta por Cliente.
    """
    report_data = documento_service.generate_estado_cuenta_cliente_report(
        db=db,
        empresa_id=current_user.empresa_id,
        tercero_id=tercero_id,
        fecha_fin=fecha_fin
    )
    return report_data

@router.get("/estado-cuenta-cliente/get-signed-url", response_model=Dict[str, str])
def get_signed_estado_cuenta_cliente_report_url(
    tercero_id: int = Query(..., description="ID del tercero (cliente)"),
    fecha_fin: date = Query(..., description="Fecha de corte del reporte"),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera una URL firmada para la descarga del PDF del Estado de Cuenta.
    """
    pdf_endpoint = "/api/reports/estado-cuenta-cliente/imprimir"
    
    signed_token = reports_service.generate_signed_report_url(
        endpoint=pdf_endpoint,
        expiration_seconds=60,
        tercero_id=tercero_id,
        fecha_fin=fecha_fin.isoformat(),
        empresa_id=current_user.empresa_id
    )
    return {"signed_url_token": signed_token}

@router.get("/estado-cuenta-cliente/imprimir")
def get_estado_cuenta_cliente_report_pdf(
    signed_token: str = Query(..., description="Token de URL firmada"),
    db: Session = Depends(get_db)
):
    """
    Sirve el PDF del Estado de Cuenta después de verificar la URL firmada.
    """
    verified_params = reports_service.verify_signed_report_url(signed_token, "/api/reports/estado-cuenta-cliente/imprimir", 90)
    if not verified_params:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="URL de descarga inválida o expirada.")

    tercero_id = verified_params["tercero_id"]
    fecha_fin = date.fromisoformat(verified_params["fecha_fin"])
    empresa_id = verified_params["empresa_id"]

    pdf_content = documento_service.generate_estado_cuenta_cliente_report_pdf(
        db, empresa_id=empresa_id, tercero_id=tercero_id, fecha_fin=fecha_fin
    )
    from fastapi.responses import Response
    return Response(content=pdf_content, media_type="application/pdf")

# --- RUTAS PARA REPORTE ESTADO DE CUENTA POR PROVEEDOR ---

@router.get("/estado-cuenta-proveedor", response_model=Dict[str, Any])
def get_estado_cuenta_proveedor_report(
    tercero_id: int = Query(..., description="ID del tercero (proveedor)"),
    fecha_fin: date = Query(..., description="Fecha de corte del reporte"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera los datos para el reporte de Estado de Cuenta por Proveedor.
    """
    report_data = documento_service.generate_estado_cuenta_proveedor_report(
        db=db,
        empresa_id=current_user.empresa_id,
        tercero_id=tercero_id,
        fecha_fin=fecha_fin
    )
    return report_data

@router.get("/estado-cuenta-proveedor/get-signed-url", response_model=Dict[str, str])
def get_signed_estado_cuenta_proveedor_report_url(
    tercero_id: int = Query(..., description="ID del tercero (proveedor)"),
    fecha_fin: date = Query(..., description="Fecha de corte del reporte"),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera una URL firmada para la descarga del PDF del Estado de Cuenta de Proveedor.
    """
    pdf_endpoint = "/api/reports/estado-cuenta-proveedor/imprimir"
    
    signed_token = reports_service.generate_signed_report_url(
        endpoint=pdf_endpoint,
        expiration_seconds=60,
        tercero_id=tercero_id,
        fecha_fin=fecha_fin.isoformat(),
        empresa_id=current_user.empresa_id
    )
    return {"signed_url_token": signed_token}

@router.get("/estado-cuenta-proveedor/imprimir")
def get_estado_cuenta_proveedor_report_pdf(
    signed_token: str = Query(..., description="Token de URL firmada"),
    db: Session = Depends(get_db)
):
    """
    Sirve el PDF del Estado de Cuenta de Proveedor después de verificar la URL firmada.
    """
    verified_params = reports_service.verify_signed_report_url(signed_token, "/api/reports/estado-cuenta-proveedor/imprimir", 90)
    if not verified_params:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="URL de descarga inválida o expirada.")

    tercero_id = verified_params["tercero_id"]
    fecha_fin = date.fromisoformat(verified_params["fecha_fin"])
    empresa_id = verified_params["empresa_id"]

    pdf_content = documento_service.generate_estado_cuenta_proveedor_report_pdf(
        db, empresa_id=empresa_id, tercero_id=tercero_id, fecha_fin=fecha_fin
    )
    from fastapi.responses import Response
    return Response(content=pdf_content, media_type="application/pdf")

# --- RUTAS PARA SUPER INFORME ---

@router.post("/super-informe", response_model=schemas_doc.SuperInformeResponse)
def get_super_informe(
    filtros: schemas_doc.DocumentoGestionFiltros,
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Endpoint principal para el Super Informe. Recibe un cuerpo con múltiples
    filtros y devuelve una lista de resultados según la entidad consultada.
    """
    try:
        # Pasamos los filtros y el empresa_id del usuario autenticado al servicio
        resultados = super_informe_service.generate_super_informe(
            db=db,
            filtros=filtros,
            empresa_id=current_user.empresa_id
        )
        return resultados
    except HTTPException as e:
        # Re-lanzamos las excepciones HTTP que vienen del servicio (ej. 400 Bad Request)
        raise e
    except Exception as e:
        # Capturamos cualquier otro error inesperado del servidor
        print(f"Error inesperado en get_super_informe: {e}") # Log para depuración
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocurrió un error inesperado al procesar la solicitud: {e}"
        )
    
@router.post("/super-informe/get-signed-url", response_model=Dict[str, str])
def get_signed_super_informe_url(
    filtros: schemas_doc.DocumentoGestionFiltros,
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera una URL firmada para la descarga del PDF del Super Informe.
    """
    pdf_endpoint = "/api/reports/super-informe/imprimir"
    
    # Pydantic model to dict para incluirlo en el token
    filtros_dict = filtros.model_dump(mode='json')
    
    signed_token = reports_service.generate_signed_report_url(
        endpoint=pdf_endpoint,
        expiration_seconds=60,
        empresa_id=current_user.empresa_id,
        filtros=filtros_dict # Pasamos el diccionario de filtros
    )
    return {"signed_url_token": signed_token}




# ... (código anterior sin cambios)

@router.get("/super-informe/imprimir")
def get_super_informe_pdf(
    signed_token: str = Query(..., description="Token de URL firmada"),
    db: Session = Depends(get_db)
):
    """
    Sirve el PDF del Super Informe como DESCARGA DIRECTA (Attachment).
    """
    verified_params = reports_service.verify_signed_report_url(
        signed_token, "/api/reports/super-informe/imprimir", 90
    )
    if not verified_params:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="URL inválida o expirada.")

    empresa_id = verified_params["empresa_id"]
    filtros_dict = verified_params["filtros"]
    
    # Reconstruir el objeto de filtros Pydantic desde el diccionario
    filtros = schemas_doc.DocumentoGestionFiltros(**filtros_dict)
    
    pdf_content = super_informe_service.generate_super_informe_pdf(
        db, filtros=filtros, empresa_id=empresa_id
    )
    
    from fastapi.responses import Response
    
    # --- CAMBIO AQUÍ: Generamos un nombre de archivo dinámico y forzamos la descarga ---
    filename = f"Super_Informe_{date.today().strftime('%Y%m%d')}.pdf"
    
    return Response(
        content=pdf_content, 
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )



# --- INICIO: NUEVO ENDPOINT PARA RECÁLCULO MANUAL DE CARTERA/PROVEEDORES ---

@router.post("/recalcular-tercero/{tercero_id}", status_code=status.HTTP_200_OK)
def recalcular_saldos_tercero(
    tercero_id: int,
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Dispara manualmente el motor de recálculo de cruces de documentos
    para un tercero específico (cliente o proveedor).
    """
    try:
        # Reutilizamos el motor de recálculo que ya es robusto y está probado.
        services_cartera.recalcular_aplicaciones_tercero(
            db=db,
            tercero_id=tercero_id,
            empresa_id=current_user.empresa_id
        )
        return {"message": f"Los saldos y cruces para el tercero ID {tercero_id} han sido recalculados exitosamente."}
    except Exception as e:
        # Si algo falla en el motor, devolvemos un error claro.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocurrió un error durante el recálculo: {str(e)}"
        )

# --- FIN: NUEVO ENDPOINT ---


# -------------------------------------------------------------------------------------
# REPORTE: ANÁLISIS DE CUENTA POR DOCUMENTO
# -------------------------------------------------------------------------------------

@router.get("/account-analysis-doc", response_model=Dict[str, Any])
def get_analisis_cuenta_doc_report(
    fecha_inicio: date = Query(..., description="Fecha de inicio (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha de fin (YYYY-MM-DD)"),
    cuenta_filtro: Optional[str] = Query(None, description="Filtrar por código o nombre de cuenta"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Retorna los datos (JSON) para el reporte de Análisis de Cuenta por Documento.
    """
    return libros_oficiales_service.get_data_for_analisis_cuenta_por_documento(
        db, current_user.empresa_id, fecha_inicio, fecha_fin, cuenta_filtro
    )


@router.get("/account-analysis-doc/get-signed-url", response_model=Dict[str, str])
def get_signed_analisis_cuenta_doc_url(
    fecha_inicio: date = Query(..., description="Fecha de inicio (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha de fin (YYYY-MM-DD)"),
    cuenta_filtro: Optional[str] = Query(None, description="Filtro de cuenta"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera URL firmada para descarga de PDF del Análisis de Cuenta por Documento.
    """
    pdf_endpoint = "/api/reports/account-analysis-doc/imprimir"
    
    # Preparamos los parámetros para el token
    params_token = {
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat(),
        "empresa_id": current_user.empresa_id,
        "cuenta_filtro": cuenta_filtro
    }
    
    signed_token = reports_service.generate_signed_report_url(
        endpoint=pdf_endpoint,
        expiration_seconds=60,
        **params_token
    )
    return {"signed_url_token": signed_token}


@router.get("/account-analysis-doc/imprimir")
def get_analisis_cuenta_doc_pdf(
    token: str = Query(..., description="Token firmado generado por get-signed-url"),
    db: Session = Depends(get_db)
):
    """
    Genera y descarga el PDF del Análisis de Cuenta por Documento (Validando Token).
    """
    payload = reports_service.verify_signed_report_url(
        token, 
        expected_endpoint="/api/reports/account-analysis-doc/imprimir"
    )
    
    if not payload:
        raise HTTPException(status_code=403, detail="Token inválido o expirado.")

    # Extraer parámetros del payload
    empresa_id = payload.get("empresa_id")
    fecha_inicio_str = payload.get("fecha_inicio")
    fecha_fin_str = payload.get("fecha_fin")
    cuenta_filtro = payload.get("cuenta_filtro")

    # Convertir strings a date
    try:
        fecha_inicio = date.fromisoformat(fecha_inicio_str)
        fecha_fin = date.fromisoformat(fecha_fin_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido en token.")

    pdf_bytes = libros_oficiales_service.generate_analisis_cuenta_por_documento_pdf(
        db, empresa_id, fecha_inicio, fecha_fin, cuenta_filtro
    )
    
    filename = f"Analisis_Cuenta_Doc_{fecha_inicio_str}_{fecha_fin_str}.pdf"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )


# --- ESTADO DE FUENTES Y USOS (CAPITAL DE TRABAJO) ---

@router.get("/working-capital-analysis", response_model=Dict[str, Any])
def get_wc_analysis_report(
    fecha_inicio: date = Query(..., description="Fecha de inicio"),
    fecha_fin: date = Query(..., description="Fecha de fin"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Retorna datos del Estado de Fuentes y Usos (Capital de Trabajo).
    """
    return analisis_financiero_service.get_fuentes_usos_capital_trabajo(
        db, current_user.empresa_id, fecha_inicio, fecha_fin
    )

@router.get("/working-capital-analysis/get-signed-url", response_model=Dict[str, str])
def get_signed_wc_analysis_url(
    fecha_inicio: date = Query(..., description="Fecha de inicio"),
    fecha_fin: date = Query(..., description="Fecha de fin"),
    db: Session = Depends(get_db),
    current_user: usuario_schema.User = Depends(get_current_user)
):
    """
    Genera URL firmada para PDF de Fuentes y Usos.
    """
    pdf_endpoint = "/api/reports/working-capital-analysis/imprimir"
    
    params_token = {
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat(),
        "empresa_id": current_user.empresa_id
    }
    
    signed_token = reports_service.generate_signed_report_url(
        endpoint=pdf_endpoint,
        expiration_seconds=60,
        **params_token
    )
    return {"signed_url_token": signed_token}

@router.get("/working-capital-analysis/imprimir")
def get_wc_analysis_pdf(
    token: str = Query(..., description="Token firmado"),
    db: Session = Depends(get_db)
):
    """
    Genera PDF de Fuentes y Usos (Validando Token).
    """
    payload = reports_service.verify_signed_report_url(
        token, 
        expected_endpoint="/api/reports/working-capital-analysis/imprimir"
    )
    
    if not payload:
        raise HTTPException(status_code=403, detail="Token inválido o expirado.")
        
    empresa_id = payload.get("empresa_id")
    # Fechas
    try:
        fecha_inicio = date.fromisoformat(payload.get("fecha_inicio"))
        fecha_fin = date.fromisoformat(payload.get("fecha_fin"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido.")
        
    pdf_bytes = analisis_financiero_service.generate_fuentes_usos_pdf(
        db, empresa_id, fecha_inicio, fecha_fin
    )
    
    filename = f"Fuentes_Usos_{fecha_inicio}_{fecha_fin}.pdf"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )

