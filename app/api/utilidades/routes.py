from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.services import (
    usuario as usuario_service,
    documento as documento_service,
    recodificacion as recodificacion_service,
    migracion as migracion_service,
    diagnostico as diagnostico_service,
    auditoria as auditoria_service
)
from app.schemas import (
    usuario as usuario_schema,
    documento as schemas_doc,
    diagnostico as diagnostico_schemas,
    recodificacion as recodificacion_schemas,
    migracion as migracion_schemas,
    auditoria as auditoria_schemas,
    tipo_documento as tipo_documento_schema
)
from app.core.database import get_db
from app.core import security
from app.core.security import get_current_user, has_permission
from app.models import usuario as models_usuario

router = APIRouter()

# ===============================================================
# SECCIÓN DE UTILIDADES PARA SOPORTE (MODERNIZADA)
# ===============================================================

@router.post("/iniciar-reseteo-password")
def iniciar_reseteo_password(
    request: usuario_schema.PasswordResetRequest,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("utilidades:usar_herramientas"))
):
    usuario = usuario_service.get_user_by_email(db, email=request.email)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontró un usuario con ese correo electrónico.")
    
    password_reset_token = security.create_password_reset_token(email=usuario.email)
    reset_url = f"http://localhost:3000/reset-password?token={password_reset_token}"
    
    return {
        "msg": "Proceso de reseteo iniciado. Copie el siguiente token o URL para continuar.",
        "reset_token": password_reset_token,
        "reset_url_ejemplo": reset_url
    }

@router.post("/inspeccionar-entidades", response_model=List[diagnostico_schemas.EntidadInspeccionada])
def inspeccionar_entidades(
    request: diagnostico_schemas.InspeccionRequest,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("utilidades:usar_herramientas"))
):
    return diagnostico_service.inspeccionar_entidades(db=db, request=request)

@router.post("/erradicar-entidades-maestras")
def erradicar_entidades_maestras(
    request: diagnostico_schemas.ErradicacionMaestrosRequest,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("utilidades:usar_herramientas"))
):
    return diagnostico_service.erradicar_entidades_maestras(db=db, request=request)

@router.post("/erradicar-universal")
def erradicar_universal(
    request: diagnostico_schemas.ErradicacionUniversalRequest,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("utilidades:usar_herramientas"))
):
    return diagnostico_service.erradicar_universal(db=db, request=request)

@router.post("/buscar-id-por-llave-natural", response_model=diagnostico_schemas.BusquedaInversaResponse)
def buscar_id_por_llave_natural(
    request: diagnostico_schemas.BusquedaInversaRequest,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("utilidades:usar_herramientas"))
):
    return diagnostico_service.buscar_id_por_llave_natural(db=db, request=request)

@router.post("/inspector-universal-id", response_model=List[diagnostico_schemas.InspectorUniversalResult])
def inspector_universal_id(
    request: diagnostico_schemas.InspectorUniversalRequest,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("utilidades:usar_herramientas"))
):
    return diagnostico_service.inspector_universal_id(db=db, id_to_inspect=request.idToInspect)

@router.get("/conteo-registros", response_model=List[diagnostico_schemas.ConteoResult])
def contar_registros(
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("utilidades:usar_herramientas"))
):
    return diagnostico_service.contar_registros_por_empresa(db=db)

@router.post("/get-tipos-documento", response_model=List[tipo_documento_schema.TipoDocumento])
def get_tipos_documento_soporte(
    request: diagnostico_schemas.TiposDocumentoRequest,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("utilidades:usar_herramientas"))
):
    return diagnostico_service.get_tipos_documento_por_empresa(db=db, empresa_id=request.empresaId)

@router.post("/ultimas-operaciones", response_model=List[auditoria_schemas.UltimasOperacionesResponse])
def get_ultimas_operaciones(
    request: auditoria_schemas.UltimasOperacionesRequest,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("utilidades:usar_herramientas"))
):
    return auditoria_service.get_ultimas_operaciones_global(db=db, request=request)

@router.post("/buscar-documento-universal", response_model=List[diagnostico_schemas.BusquedaUniversalResult])
def buscar_documento_universal(
    request: diagnostico_schemas.BusquedaUniversalFiltros,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("utilidades:usar_herramientas"))
):
    return diagnostico_service.buscar_documento_universal(db=db, filtros=request)

@router.post("/erradicar-documento")
def erradicar_documento(
    request: diagnostico_schemas.ErradicacionRequest,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("utilidades:usar_herramientas"))
):
    return diagnostico_service.erradicar_documentos_por_ids(db=db, request=request)

@router.get("/soporte/maestros", response_model=diagnostico_schemas.MaestrosSoporteResponse)
def get_maestros_soporte(
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("utilidades:usar_herramientas"))
):
    return diagnostico_service.get_maestros_para_soporte(db=db)

@router.post("/analizar-erradicacion", response_model=diagnostico_schemas.PlanDeEjecucionResponse)
def analizar_erradicacion_endpoint(
    request: diagnostico_schemas.AnalisisErradicacionRequest,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("utilidades:usar_herramientas"))
):
    return diagnostico_service.analizar_erradicacion(db=db, request=request)

@router.get("/auditoria/consecutivos/{empresa_id}/{tipo_documento_id}", response_model=schemas_doc.AuditoriaConsecutivosResponse)
def get_auditoria_consecutivos_soporte(
    empresa_id: int, tipo_documento_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("utilidades:usar_herramientas"))
):
    return auditoria_service.get_auditoria_consecutivos(db=db, empresa_id=empresa_id, tipo_documento_id=tipo_documento_id)

@router.post("/tipos-documento-por-empresa", response_model=List[tipo_documento_schema.TipoDocumento])
def get_tipos_documento_por_empresa_soporte(
    request: diagnostico_schemas.TiposDocumentoRequest,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("utilidades:usar_herramientas"))
):
    return diagnostico_service.get_tipos_documento_por_empresa(db=db, empresa_id=request.empresaId)

# ===============================================================
# SECCIÓN DE UTILIDADES PARA USUARIOS NORMALES
# ===============================================================

@router.post("/resetear-password")
def resetear_password(payload: usuario_schema.PasswordResetPayload, db: Session = Depends(get_db)):
    email = security.verify_password_reset_token(payload.token)
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El token de reseteo es inválido o ha expirado.")
    usuario = usuario_service.get_user_by_email(db, email=email)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El usuario asociado a este token ya no existe.")
    usuario_service.update_password(db, user=usuario, new_password=payload.nueva_password)
    return {"msg": "¡Contraseña actualizada exitosamente!"}

@router.post("/exportar-datos")
def exportar_datos(export_request: migracion_schemas.ExportRequest, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(has_permission("utilidades:migracion"))): # <-- CAMBIO AQUÍ
    return migracion_service.exportar_datos(db=db, export_request=export_request, empresa_id=current_user.empresa_id)

@router.post("/backup-rapido")
def backup_rapido(current_user: models_usuario.Usuario = Depends(has_permission("utilidades:migracion")), db: Session = Depends(get_db)):
    """Genera un backup completo inmediato (para uso por comandos de voz/AI)"""
    return migracion_service.generar_backup_json(db=db, empresa_id=current_user.empresa_id, filtros=None)


# --- RUTAS PARA COPIA AUTOMÁTICA ---
from app.services import scheduler_backup

@router.get("/backup-auto-config", response_model=migracion_schemas.AutoBackupConfig)
def get_backup_config(current_user: models_usuario.Usuario = Depends(has_permission("utilidades:migracion"))):
    return scheduler_backup.load_config()

@router.post("/backup-auto-config")
def update_backup_config(config: migracion_schemas.AutoBackupConfig, current_user: models_usuario.Usuario = Depends(has_permission("utilidades:migracion"))):
    scheduler_backup.save_config(config.dict())
    return {"msg": "Configuración de copia automática actualizada correctamente."}

@router.post("/analizar-backup", response_model=migracion_schemas.AnalysisReport)
def analizar_backup(analysis_request: migracion_schemas.AnalysisRequest, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(has_permission("utilidades:migracion"))): # <-- CAMBIO AQUÍ
    return migracion_service.analizar_backup(db=db, analysis_request=analysis_request)

@router.post("/ejecutar-restauracion")
def ejecutar_restauracion(request: migracion_schemas.AnalysisRequest, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(has_permission("utilidades:migracion"))): # <-- CAMBIO AQUÍ
    return migracion_service.ejecutar_restauracion(db=db, request=request, user_id=current_user.id)

# --- MEJORA PROACTIVA: Se restaura la llamada a su versión original, más robusta y legible ---
@router.post("/recodificar-cuenta")
def recodificar_cuenta(request_data: recodificacion_schemas.RecodificacionRequest, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    return recodificacion_service.recodificar_datos(db=db, campo_afectado='cuenta_id', tabla_afectada='movimientos_contables', request_data=request_data, empresa_id=current_user.empresa_id)

@router.post("/recodificar-tercero")
def recodificar_tercero(request_data: recodificacion_schemas.RecodificacionRequest, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    return recodificacion_service.recodificar_datos(db=db, campo_afectado='beneficiario_id', tabla_afectada='documentos', request_data=request_data, empresa_id=current_user.empresa_id)

@router.post("/recodificar-centro-costo")
def recodificar_centro_costo(request_data: recodificacion_schemas.RecodificacionRequest, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    return recodificacion_service.recodificar_datos(db=db, campo_afectado='centro_costo_id', tabla_afectada='movimientos_contables', request_data=request_data, empresa_id=current_user.empresa_id)

@router.get("/papelera", response_model=List[schemas_doc.PapeleraItem])
def get_papelera_items(db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    return documento_service.get_documentos_papelera(db=db, empresa_id=current_user.empresa_id)

@router.post("/auditoria-consecutivos", response_model=List[diagnostico_schemas.ConsecutivoInfo])
def get_auditoria_consecutivos(request: diagnostico_schemas.AuditoriaConsecutivosRequest, db: Session = Depends(get_db), current_user: models_usuario.Usuario = Depends(get_current_user)):
    return diagnostico_service.get_auditoria_consecutivos(db=db, user=current_user, request=request)