# app/api/soporte/routes.py
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import soporte as services_soporte
from app.services import scheduler_backup
from app.services import cartera as cartera_service
from app.schemas import soporte as schemas_soporte
from app.schemas import usuario as schemas_usuario # NUEVO IMPORT
from app.core.security import has_permission
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    # CORRECCIÓN: Se elimina el prefijo duplicado. 
    # main.py ahora tiene el control total de la ruta.
    tags=["Panel de Soporte"]
)

@router.get(
    "/dashboard-data", 
    response_model=schemas_soporte.DashboardData,
    dependencies=[Depends(has_permission("soporte:acceder_panel"))]
)
def get_dashboard_data_route(db: Session = Depends(get_db)):
    """
    Endpoint "Todo en Uno": Devuelve toda la información necesaria para
    el Panel de Mando de Soporte en una sola llamada.
    """
    return services_soporte.get_dashboard_data(db=db)

@router.get(
    "/users/accountants",
    response_model=list[schemas_usuario.UserBasic], # CORRECTED SCHEMA
    dependencies=[Depends(has_permission("soporte:acceder_panel"))]
)
def get_accountant_users_route(db: Session = Depends(get_db)):
    """
    Obtiene lista de usuarios con rol Contador.
    """
    return services_soporte.get_accountant_users(db)

@router.get(
    "/empresas/search",
    response_model=schemas_soporte.EmpresaSearchResponse,
    dependencies=[Depends(has_permission("soporte:acceder_panel"))]
)
def search_empresas_route(
    q: str = None,
    role_filter: str = 'ADMIN', # ADMIN | CONTADOR
    type_filter: str = 'REAL',  # REAL | PLANTILLA
    owner_id: int = None,       # NUEVO PARAM
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db)
):
    return services_soporte.search_empresas(
        db, q=q, role_filter=role_filter, type_filter=type_filter, owner_id=owner_id, page=page, size=size
    )

@router.post(
    "/empresas/from-template",
    response_model=schemas_soporte.EmpresaConUsuarios, # Reusamos el schema de respuesta
    dependencies=[Depends(has_permission("soporte:acceder_panel"))]
)
def create_empresa_from_template_route(
    data: schemas_soporte.EmpresaCreateFromTemplate,
    db: Session = Depends(get_db)
):
    """
    Crea una nueva empresa basada en una plantilla existente (copia PUC, Impuestos, Documentos).
    """
    return services_soporte.create_empresa_from_template(db, data)

@router.post(
    "/empresas/{empresa_id}/convert-to-template",
    response_model=schemas_soporte.EmpresaConUsuarios, # Uses common schema
    dependencies=[Depends(has_permission("soporte:acceder_panel"))]
)
def convert_empresa_to_template_route(
    empresa_id: int,
    data: schemas_soporte.TemplateConversionRequest,
    db: Session = Depends(get_db)
):
    """
    Crea una PLANTILLA a partir de una empresa existente (Clonación).
    La empresa original permanece intacta.
    """
    # Import service function directly from empresa service where it was implemented
    from app.services import empresa as empresa_service
    return empresa_service.create_template_from_existing(
        db, 
        source_empresa_id=empresa_id, 
        template_category=data.template_category
    )

@router.get(
    "/backups/global",
    response_model=schemas_soporte.GlobalBackupConfig,
    dependencies=[Depends(has_permission("soporte:acceder_panel"))]
)
def get_global_backup_config_route():
    """
    Obtiene la configuración global de backups automáticos.
    """
    return scheduler_backup.load_config(empresa_id="global")

@router.post(
    "/backups/global",
    response_model=schemas_soporte.GlobalBackupConfig,
    dependencies=[Depends(has_permission("soporte:acceder_panel"))]
)
def save_global_backup_config_route(data: schemas_soporte.GlobalBackupConfig):
    """
    Guarda y actualiza la configuración global de backups automáticos.
    """
    scheduler_backup.save_global_config(data.model_dump())
    return scheduler_backup.load_config(empresa_id="global")

@router.post(
    "/backups/global/run",
    dependencies=[Depends(has_permission("soporte:acceder_panel"))]
)
def run_global_backup_manually_route(background_tasks: BackgroundTasks):
    """
    Inicia manualmente la creación de un backup global en segundo plano.
    Evita timeouts en el servidor al no esperar el procesamiento de todas las empresas.
    """
    try:
        background_tasks.add_task(scheduler_backup.run_global_backup)
        return {
            "ok": True, 
            "message": "Proceso de backup global iniciado en segundo plano. Podrá visualizar y descargar el archivo en la lista inferior una vez finalice."
        }
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"No se pudo iniciar el proceso de backup: {str(e)}")

# --- Explorador de Archivos Nube ---

@router.get(
    "/backups/global/list",
    dependencies=[Depends(has_permission("soporte:acceder_panel"))]
)
def list_global_backup_files_route():
    """Retorna un listado de los backup .zip disponibles en el disco duro de la nube."""
    return scheduler_backup.get_global_backup_files()


@router.get(
    "/backups/global/download/{filename}",
    dependencies=[Depends(has_permission("soporte:acceder_panel"))]
)
def download_specific_backup_route(filename: str):
    """Descarga un .zip específico validado por nombre."""
    from fastapi.responses import FileResponse
    from fastapi import HTTPException
    
    file_path = scheduler_backup.get_global_backup_file_path(filename)
    if not file_path:
        raise HTTPException(status_code=404, detail="Archivo no encontrado o inválido.")
        
    return FileResponse(
        path=file_path,
        media_type="application/zip",
        filename=filename
    )


@router.delete(
    "/backups/global/delete/{filename}",
    dependencies=[Depends(has_permission("soporte:acceder_panel"))]
)
def delete_specific_backup_route(filename: str):
    """Elimina físicamente un backup viejo para liberar espacio."""
    from fastapi import HTTPException
    success = scheduler_backup.delete_global_backup_file(filename)
    if not success:
        raise HTTPException(status_code=404, detail="Archivo no encontrado o no pudo ser eliminado.")
    return {"message": f"Archivo {filename} eliminado correctamente"}


# ==========================================
# PORTAL DE SOPORTE INTEGRADO (NUEVO)
# ==========================================
from pydantic import BaseModel, EmailStr
from sqlalchemy import func
from app.models import documento as models_doc
from app.models import tercero as models_tercero
from app.models import empresa as models_empresa
from app.models import soporte_ticket as models_soporte # NUEVO
from app.core.security import create_tercero_token, get_current_tercero, get_current_user
from datetime import datetime
from fastapi import HTTPException

# Schemas locales para PQR y Estado de Cuenta (Portal de cliente)
class PortalLoginRequest(BaseModel):
    empresa_slug: str # El NIT o ID que viene de la URL de la empresa
    documento: str    # NIT o Cedula del Tercero
    email: EmailStr

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: dict

@router.post("/portal-login", response_model=TokenResponse)
def login_portal_terceros(data: PortalLoginRequest, db: Session = Depends(get_db)):
    """
    Login exclusivo para Terceros (Clientes de las empresas).
    Verifica que la empresa exista y tenga un Tercero con coincidencia de documento/NIT y email.
    """
    # 1. Buscar la empresa (idealmente por un "slug" único, aquí usamos NIT como slug)
    empresa = db.query(models_empresa.Empresa).filter(
        (models_empresa.Empresa.nit == data.empresa_slug) | (models_empresa.Empresa.id == data.empresa_slug if data.empresa_slug.isdigit() else False)
    ).first()
    
    if not empresa:
        raise HTTPException(status_code=404, detail="Portal empresarial no encontrado.")

    # 2. Buscar el Tercero exacto en esta Empresa (Validando documento y email)
    tercero = db.query(models_tercero.Tercero).filter(
        models_tercero.Tercero.empresa_id == empresa.id,
        models_tercero.Tercero.nit == data.documento,
        models_tercero.Tercero.email == data.email
    ).first()

    if not tercero:
        raise HTTPException(
            status_code=401, 
            detail="Credenciales incorrectas. Verifique su documento y correo registrado o comuníquese con el administrador."
        )

    # 3. Generar token especial de Tercero
    token_temporal = create_tercero_token(tercero_id=tercero.id, empresa_id=empresa.id)

    return {
        "access_token": token_temporal,
        "token_type": "bearer",
        "usuario": {
            "id": tercero.id,
            "nombre": tercero.razon_social or tercero.nombre_comercial,
            "email": tercero.email,
            "documento": tercero.nit,
            "rol": "Cliente (Portal)"
        }
    }

class PQRSubmit(BaseModel):
    asunto: str
    tipo: str
    mensaje: str

class EstadoCuentaPortal(BaseModel):
    total_adeudado: float
    proxima_fecha_pago: str | None
    mensajes_no_leidos: int
    ultimas_facturas: list[dict]

class TicketAdminResponse(BaseModel):
    id: int
    asunto: str
    tipo: str
    mensaje: str
    estado: str
    fecha_creacion: datetime
    tercero_nombre: str | None = None
    empresa_razon_social: str | None = None

class TicketUpdate(BaseModel):
    estado: str | None = None
    respuesta_soporte: str | None = None

@router.get(
    "/cuenta/estado",
    response_model=EstadoCuentaPortal,
    dependencies=[Depends(get_current_tercero)] # SOLO ACCESO TERCEROS
)
def get_cuenta_estado_portal(
    db: Session = Depends(get_db), 
    current_tercero: models_tercero.Tercero = Depends(get_current_tercero)
):
    """
    Retorna el estado de cuenta simplificado para el portal de soporte.
    Lee directamente las facturas reales del Tercero autenticado usando el servicio de cartera.
    """
    # 1. Obtener facturas pendientes usando el servicio oficial de cartera
    facturas_pendientes = cartera_service.get_facturas_pendientes_por_tercero(
        db=db,
        tercero_id=current_tercero.id,
        empresa_id=current_tercero.empresa_id
    )

    # 2. Calcular el total adeudado sumando los saldos pendientes
    saldo_total = sum(f["saldo_pendiente"] for f in facturas_pendientes)

    # 3. Formatear para el frontend
    facturas_formateadas = []
    proxima_fecha = None
    
    # Tomamos todas las facturas pendientes
    for f in facturas_pendientes:
        estado = "Pendiente" # Si está en facturas_pendientes, es porque tiene saldo
        
        # Encontrar la fecha de vencimiento más cercana (próxima fecha de pago)
        if f.get("fecha_vencimiento"):
            fecha_v = datetime.strptime(f["fecha_vencimiento"], "%Y-%m-%d").date()
            if proxima_fecha is None or fecha_v < proxima_fecha:
                proxima_fecha = fecha_v
                
        facturas_formateadas.append({
             "id": f["id"], 
             "fecha": f["fecha"], 
             "monto": f["saldo_pendiente"], # Mostramos el saldo que falta por pagar
             "estado": estado, 
             "referencia": f.get("numero", f"INV-{f['id']}")
        })

    return {
         "total_adeudado": float(saldo_total),
         "proxima_fecha_pago": proxima_fecha.strftime("%Y-%m-%d") if proxima_fecha else None,
         "mensajes_no_leidos": 0,
         "ultimas_facturas": facturas_formateadas
    }

@router.post(
    "/pqr",
    dependencies=[Depends(get_current_tercero)]
)
def submit_pqr_portal(data: PQRSubmit, db: Session = Depends(get_db), current_tercero: models_tercero.Tercero = Depends(get_current_tercero)):
    """
    Recibe un caso de soporte desde el portal del tercero y lo asocia a su empresa real.
    """
    # 1. Crear el ticket en la base de datos real
    nuevo_ticket = models_soporte.SoporteTicket(
        empresa_id=current_tercero.empresa_id,
        tercero_id=current_tercero.id,
        asunto=data.asunto,
        tipo=data.tipo,
        mensaje=data.mensaje,
        estado="ABIERTO"
    )
    
    db.add(nuevo_ticket)
    db.commit()
    db.refresh(nuevo_ticket)

    return {
        "ok": True, 
        "mensaje": f"Su caso de tipo '{data.tipo.upper()}' ha sido radicado con éxito en nombre de {current_tercero.razon_social}. Ticket #TKT-{nuevo_ticket.id}",
        "ticket_id": nuevo_ticket.id
    }

# --- ENDPOINTS PARA ADMINISTRACIÓN (ERP) ---

@router.get(
    "/tickets/admin",
    response_model=list[TicketAdminResponse],
    dependencies=[Depends(has_permission("administracion:acceso"))]
)
def get_tickets_admin(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Lista los PQRs/Tickets para que la empresa los gestione.
    Si el usuario es admin global ve todos, si es de empresa solo los suyos.
    """
    # 1. Identificar la empresa del contexto actual
    target_empresa_id = current_user.empresa_id
    es_soporte = any(rol.nombre == 'soporte' for rol in current_user.roles)
    
    logger.info(f"PQR_DEBUG: User={current_user.email}, CompanyID={target_empresa_id}, IsSupport={es_soporte}")
    
    query = db.query(models_soporte.SoporteTicket)
    
    # 2. Aplicar filtros de seguridad
    if not es_soporte:
        if target_empresa_id:
            query = query.filter(models_soporte.SoporteTicket.empresa_id == target_empresa_id)
        else:
            logger.warning(f"PQR_DEBUG: Admin {current_user.email} without company ID. Blocked.")
            return []
    else:
        if target_empresa_id:
            query = query.filter(models_soporte.SoporteTicket.empresa_id == target_empresa_id)
            logger.info(f"PQR_DEBUG: Support filtering by company {target_empresa_id}")
        else:
            logger.info("PQR_DEBUG: Support viewing global (all) tickets")
    
    tickets = query.order_by(models_soporte.SoporteTicket.fecha_creacion.desc()).all()
    logger.info(f"PQR_DEBUG: Returning {len(tickets)} tickets")
    
    # Enriquecer con nombres de terceros para la vista admin
    resultado = []
    for t in tickets:
        tercero = db.query(models_tercero.Tercero).filter(models_tercero.Tercero.id == t.tercero_id).first()
        resultado.append({
            "id": t.id,
            "asunto": t.asunto,
            "tipo": t.tipo,
            "mensaje": t.mensaje,
            "estado": t.estado,
            "fecha_creacion": t.fecha_creacion,
            "tercero_nombre": tercero.razon_social if tercero else "Desconocido"
        })
    return resultado

@router.patch(
    "/tickets/admin/{ticket_id}",
    dependencies=[Depends(has_permission("administracion:acceso"))]
)
def update_ticket_admin(ticket_id: int, data: TicketUpdate, db: Session = Depends(get_db)):
    """
    Actualiza el estado o respuesta de un ticket.
    """
    ticket = db.query(models_soporte.SoporteTicket).filter(models_soporte.SoporteTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
        
    if data.estado:
        ticket.estado = data.estado
    if data.respuesta_soporte:
        ticket.respuesta_soporte = data.respuesta_soporte
        
    db.commit()
    return {"ok": True, "mensaje": "Ticket actualizado correctamente"}

