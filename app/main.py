# app/main.py (Versión con FIX en importación de seguridad)

# --- INICIO DE LA CORRECCIÓN DEFINITIVA ---
# Se importa la librería 'os' para interactuar con el sistema operativo.
import os
# Se establece la variable de entorno ANTES de que cualquier otra librería
# (especialmente WeasyPrint/GTK+) sea importada. Esto silencia las advertencias
# de GLib-GIO de forma robusta e inmune al problema del "--reload".
os.environ['GIO_USE_VOLUME_MONITOR'] = 'dummy'
# --- FIN DE LA CORRECCIÓN DEFINITIVA ---

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# --- INICIO: LÓGICA DE AUTO-CREACIÓN DE BASE DE DATOS ---
from app.core.database import engine, Base
from app.models import (
    Usuario, Empresa, Tercero, PlanCuenta, TipoDocumento, CentroCosto,
    PlantillaMaestra, PlantillaDetalle, ConceptoFavorito, Documento, 
    DocumentoEliminado, MovimientoContable, MovimientoEliminado,
    LogOperacion, PeriodoContableCerrado, FormatoImpresion, AplicacionPago,
    Remision, RemisionDetalle, ConfiguracionReporte, nomina 
)
Base.metadata.create_all(bind=engine)
# --- FIN: LÓGICA DE AUTO-CREACIÓN ---

# --- INICIO: LÓGICA DE SEMBRADO AUTOMÁTICO ---
from app.core.seeder import seed_database
seed_database()
# --- FIN: LÓGICA DE SEMBRADO AUTOMÁTICO ---



# Se importan los routers de la API
from app.core.database import get_db
from app.api.auth import routes as auth_router
from app.api.centros_costo import routes as centros_costo_router


from app.api.conceptos_favoritos import routes as conceptos_favoritos_router # <--- AÑADIR ESTA LÍNEA

from app.api.documentos import routes as documentos_router
from app.api.empresas import routes as empresas_router
from app.api.formatos_impresion import routes as formatos_impresion_router
from app.api.papelera import routes as papelera_router
from app.api.periodos import routes as periodos_router

from app.api.plan_cuentas.routes import router as plan_cuentas_router

from app.api.plantillas import routes as plantillas_router
from app.api.terceros import routes as terceros_router
from app.api.tipos_documento import routes as tipos_documento_router

# --- MODULO IMPUESTOS ---
from app.api.impuestos import routes as impuestos_router
# app.include_router se mueve abajo


from app.api.utilidades import routes as utilidades_router
from app.api.reports import routes as reports_router
from app.api.cartera import routes as cartera_router
from app.api.proveedores import routes as proveedores_router
from app.api.usuarios import routes as usuarios_router
from app.api.auditoria.routes import router as auditoria_router
from app.api.roles import routes as roles_routes
from app.api.soporte import routes as soporte_router
from app.api.inventario import routes as inventario_routes
from app.api.facturacion import routes as facturacion_routes
from app.api.compras import routes as compras_routes
from app.api.reportes_inventario import routes as reportes_inventario_routes
from app.api.reportes_financieros_inventario import routes as reportes_financieros_inv_routes
from app.api.gestion_ventas import routes as gestion_ventas_routes

from app.api.reportes_facturacion import routes as reportes_facturacion_routes
from app.api.bodegas import routes as bodegas_router
from app.api.ajuste_inventario import routes as ajuste_inventario_router
from app.api.reportes_inventario import routes as reportes_inventario_router
from app.api.listas_precio import routes as listas_precio_router 
from app.api.traslados_inventario import routes as traslados_inventario_router

# Ubica donde importas otros routers como inventario_routes, bodegas_router, etc.
from app.api.listas_precio import routes as listas_precio_router # Esta maneja Listas y Reglas de Precio
from app.api.caracteristicas import routes as caracteristicas_router # Esta maneja Definiciones de Características
from app.api.favoritos import routes as favoritos_router  # <--- NUEVA IMPORTACIÓN
# ... otras importaciones
from app.api.dashboard import routes as dashboard_router # <--- NUEVA IMPORTACIÓN
from app.api.manual import routes as manual_router # <--- ROUTER MANUAL

# ...


# --- INICIO: SONDA DE DIAGNÓSTICO DE CONEXIÓN ---
from app.core.config import settings
print("="*50)
print("VERIFICANDO CONEXIÓN DE LA APLICACIÓN...")
print(f"La aplicación se está conectando a: {settings.DATABASE_URL}")
print("="*50)
# --- FIN: SONDA DE DIAGNÓSTICO ---

app = FastAPI(
    title="API del Sistema Finaxis",
    description="Backend para la gestión contable, construido con FastAPI y Python.",
    version="1.0.0"
)

# --- INICIO: SCHEDULER DE COPIAS (AUTO-BACKUP) ---
from app.services.scheduler_backup import start_scheduler
@app.on_event("startup")
def startup_event():
    start_scheduler()
# --- FIN: SCHEDULER ---

origins = [
    "http://localhost:3000",
    "http://localhost:3002",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- INICIO: BYPASS DE EMERGENCIA PARA IMPRESIÓN SEGURA (EXISTENTE) ---
import io
import json
from fastapi import Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

# CORRECCIÓN CLAVE: Se usa decode_print_token que existe en security.py
from app.core.security import decode_print_token, validate_signed_token
from app.services import documento as service_documento

@app.get("/api/documentos/imprimir-rentabilidad-firmado", tags=["Documentos"])
def imprimir_rentabilidad_firmado_bypass(
    token: str,
    db: Session = Depends(get_db)
):
    payload = decode_print_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de impresión inválido o expirado.")
    documento_id = payload.get("doc_id")
    empresa_id = payload.get("emp_id")
    try:
        pdf_bytes = service_documento.generar_pdf_rentabilidad_factura(db=db, documento_id=documento_id, empresa_id=empresa_id)
        pdf_stream = io.BytesIO(pdf_bytes)
        file_name = f"rentabilidad_factura_{documento_id}.pdf"
        return StreamingResponse(pdf_stream, media_type="application/pdf", headers={"Content-Disposition": f"inline; filename={file_name}"})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al generar el PDF de rentabilidad: {str(e)}")
# --- FIN: BYPASS DE EMERGENCIA (EXISTENTE) ---


# --- INICIO: NUEVO BYPASS PARA REPORTE GESTIÓN DE VENTAS (CÓDIGO CORREGIDO) ---
from app.services import gestion_ventas as service_gestion_ventas
from app.schemas import gestion_ventas as schemas_ventas

# EN app/main.py (Busca la sección de BYPASS y agrega esto):

@app.get("/api/documentos/imprimir-firmado", tags=["Documentos"])
def imprimir_documento_firmado_bypass(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Endpoint PÚBLICO de bypass para imprimir el documento estándar.
    Define la ruta directamente en main.py para evitar bloqueos de seguridad del router.
    """
    payload = decode_print_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token de impresión inválido o expirado."
        )
    
    documento_id = payload.get("doc_id")
    empresa_id = payload.get("emp_id")
    
    try:
        # Llamamos directamente al servicio
        pdf_bytes, file_name = service_documento.generar_pdf_documento(
            db=db, 
            documento_id=documento_id, 
            empresa_id=empresa_id
        )
        pdf_stream = io.BytesIO(pdf_bytes)
        return StreamingResponse(
            pdf_stream, 
            media_type="application/pdf", 
            headers={"Content-Disposition": f"inline; filename={file_name}"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error al generar el PDF: {str(e)}"
        )
    
    

@app.get("/api/gestion-ventas/imprimir-reporte-firmado", tags=["Gestión de Ventas"])
def imprimir_reporte_gestion_ventas_firmado(
    token: str,
    db: Session = Depends(get_db)
):
    """Endpoint PÚBLICO de bypass para imprimir el reporte de Gestión de Ventas."""
    datos_como_string = validate_signed_token(token=token, salt="report_print", max_age=300)
    
    if not datos_como_string:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de impresión inválido o expirado."
        )

    try:
        payload_dict = json.loads(datos_como_string)
        payload = schemas_ventas.GestionVentasPDFPayload.model_validate(payload_dict)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El contenido del token es inválido: {e}"
        )

    try:
        pdf_bytes = service_gestion_ventas.generar_pdf_reporte_gestion_ventas(
            db=db,
            payload=payload
        )
        pdf_stream = io.BytesIO(pdf_bytes)
        file_name = "reporte_gestion_ventas.pdf"
        return StreamingResponse(
            pdf_stream,
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename={file_name}"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar el PDF del reporte: {str(e)}"
        )
# --- FIN: NUEVO BYPASS (CÓDIGO CORREGIDO) ---




@app.get("/")
def read_root():
    return {"status": "ok", "message": "Bienvenido a la API del Sistema Contable"}

# Inclusión de todos los routers
app.include_router(auth_router.router, prefix="/api/auth", tags=["Autenticación"])
app.include_router(terceros_router.router, prefix="/api/terceros", tags=["Terceros"])

app.include_router(plan_cuentas_router, prefix="/api/plan-cuentas", tags=["Plan de Cuentas"])

app.include_router(tipos_documento_router.router, prefix="/api/tipos-documento", tags=["Tipos de Documento"])
app.include_router(centros_costo_router.router, prefix="/api/centros-costo", tags=["Centros de Costo"])
app.include_router(plantillas_router.router, prefix="/api/plantillas", tags=["Plantillas"])


app.include_router(conceptos_favoritos_router.router, prefix="/api", tags=["Conceptos Favoritos"]) # <--- AÑADIR ESTA LÍNEA

app.include_router(documentos_router.router, prefix="/api/documentos", tags=["Documentos"])

app.include_router(empresas_router.router, prefix="/api/empresas", tags=["Empresas (Soporte)"])
app.include_router(papelera_router.router, prefix="/api/papelera", tags=["Papelera"])
app.include_router(utilidades_router.router, prefix="/api/utilidades", tags=["Utilidades"])
app.include_router(periodos_router.router, prefix="/api/periodos", tags=["Períodos"])
app.include_router(formatos_impresion_router.router, prefix="/api/formatos-impresion", tags=["Plantillas de Impresión"])
app.include_router(reports_router.router, prefix="/api/reports", tags=["Reportes"])
app.include_router(cartera_router.router, prefix="/api/cartera", tags=["Cartera"])
app.include_router(proveedores_router.router, prefix="/api/proveedores", tags=["Proveedores"])
app.include_router(usuarios_router.router, prefix="/api/usuarios", tags=["Usuarios"])
app.include_router(auditoria_router, prefix="/api/auditoria", tags=["Auditoría"])
app.include_router(roles_routes.router, prefix="/api")
app.include_router(soporte_router.router, prefix="/api/soporte", tags=["Panel de Soporte"])
app.include_router(inventario_routes.router, prefix="/api/inventario", tags=["Inventario"])
app.include_router(facturacion_routes.router, prefix="/api/facturacion", tags=["Facturación"])
app.include_router(compras_routes.router, prefix="/api/compras", tags=["Compras"])
app.include_router(reportes_inventario_routes.router, prefix="/api/reportes-inventario", tags=["Reportes de Inventario"])
app.include_router(reportes_financieros_inv_routes.router, prefix="/api/reportes-financieros-inventario", tags=["Reportes Financieros Inventario"])
app.include_router(gestion_ventas_routes.router, prefix="/api/gestion-ventas", tags=["Gestión de Ventas"])

app.include_router(reportes_facturacion_routes.router, prefix="/api/reportes-facturacion", tags=["Reportes de Facturación"])
app.include_router(bodegas_router.router, prefix="/api/bodegas", tags=["Bodegas"])
app.include_router(ajuste_inventario_router.router, prefix="/api/ajuste-inventario", tags=["Ajuste de Inventario"])
app.include_router(reportes_inventario_router.router, prefix="/api/reportes-inventario", tags=["Reportes de Inventario"])

app.include_router(listas_precio_router.router, prefix="/api", tags=["Listas de Precios"]) # <--- NUEVO ROUTER INCLUIDO
app.include_router(traslados_inventario_router.router, prefix="/api/traslados-inventario", tags=["Traslados de Inventario"])

# Ubica donde incluyes otros routers como inventario_routes.router, bodegas_router.router, etc.
# Incluimos el router que ahora maneja tanto Listas de Precios como Reglas de Precio por Grupo
app.include_router(listas_precio_router.router, prefix="/api", tags=["Listas de Precios y Reglas"])

# Incluimos el nuevo router para gestionar las Definiciones de Características por Grupo
app.include_router(caracteristicas_router.router, prefix="/api", tags=["Características de Inventario"])

# El router de favoritos ya tiene el '/favoritos' dentro de su archivo,
# así que aquí solo necesitamos el prefijo raíz '/api'
app.include_router(favoritos_router.router, prefix="/api", tags=["Favoritos"])

# app/main.py (Sección de include_router)
app.include_router(dashboard_router.router, prefix="/api", tags=["Dashboard"])
app.include_router(manual_router.router, prefix="/api/manual", tags=["Manual de Usuario"])

# --- MODULO IMPUESTOS (Movido al final para evitar errores de orden) ---
app.include_router(impuestos_router.router, prefix="/api/impuestos", tags=["Impuestos"])


# --- MODULO REMISIONES ---
from app.api.remisiones import routes as remisiones_router
app.include_router(remisiones_router.router, prefix="/api/remisiones", tags=["Remisiones"])

# --- MODULO COTIZACIONES ---
from app.api.cotizaciones import routes as cotizaciones_router
app.include_router(cotizaciones_router.router, prefix="/api/cotizaciones", tags=["Cotizaciones"])

# --- MODULO ACTIVOS FIJOS ---
from app.api.activos_fijos import routes as activos_fijos_router
app.include_router(activos_fijos_router.router, prefix="/api/activos", tags=["Activos Fijos"])

# --- MODULO PROPIEDAD HORIZONTAL ---
from app.api.propiedad_horizontal import routes as ph_routes
app.include_router(ph_routes.router, prefix="/api/ph", tags=["Propiedad Horizontal"])

# --- MODULO NOMINA (BETA) ---
from app.api.nomina import routes as router_nomina
app.include_router(router_nomina.router, prefix="/api", tags=["Nómina"])

# --- MODULO PRODUCCION ---
from app.api.endpoints import produccion as produccion_router
app.include_router(produccion_router.router, prefix="/api/produccion", tags=["Producción"])

# --- MODULO SMART SEARCH (BÚSQUEDA INTELIGENTE) ---
from app.api.endpoints import search as search_router
app.include_router(search_router.router, prefix="/api/search", tags=["Búsqueda Inteligente"])

# --- MODULO CONCILIACION BANCARIA ---
from app.api.conciliacion_bancaria import routes as conciliacion_bancaria_router
app.include_router(conciliacion_bancaria_router.router, prefix="/api", tags=["Conciliación Bancaria"])

# Los permisos de conciliación bancaria ahora se crean automáticamente en el seeder

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

# FORCE RELOAD TRIGGER - PH MODULE UPDATE