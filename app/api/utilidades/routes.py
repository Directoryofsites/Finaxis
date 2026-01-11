from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.services import (
    usuario as usuario_service,
    documento as documento_service,
    recodificacion as recodificacion_service,
    migracion as migracion_service,
    diagnostico as diagnostico_service,
    auditoria as auditoria_service,
    consumo_service
)
from app.schemas import (
    usuario as usuario_schema,
    documento as schemas_doc,
    consumo as consumo_schemas,
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
    current_user: models_usuario.Usuario = Depends(has_permission("empresa:gestionar"))
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
    current_user: models_usuario.Usuario = Depends(has_permission("empresa:gestionar"))
):
    return diagnostico_service.get_maestros_para_soporte(db=db)

@router.post("/analizar-erradicacion", response_model=diagnostico_schemas.PlanDeEjecucionResponse)
def analizar_erradicacion_endpoint(
    request: diagnostico_schemas.AnalisisErradicacionRequest,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("utilidades:usar_herramientas"))
):
    return diagnostico_service.analizar_erradicacion(db=db, request=request)

# ===============================================================
# GESTIÓN DE RECARGAS EXTRAORDINARIAS (SOPORTE)
# ===============================================================

@router.get("/recargas-empresa/{empresa_id}", response_model=List[consumo_schemas.RecargaItemRead])
def get_recargas_empresa(
    empresa_id: int,
    mes: int,
    anio: int,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("utilidades:usar_herramientas"))
):
    """Obtiene las recargas compradas por una empresa en un mes/año específico."""
    from app.models.consumo_registros import RecargaAdicional
    recargas = db.query(RecargaAdicional).filter(
        RecargaAdicional.empresa_id == empresa_id,
        RecargaAdicional.mes == mes,
        RecargaAdicional.anio == anio
    ).all()
    return recargas

@router.delete("/recargas-empresa/{recarga_id}")
def delete_recarga_empresa(
    recarga_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("utilidades:usar_herramientas"))
):
    """Elimina una recarga específica (Soporte)."""
    from app.models.consumo_registros import RecargaAdicional
    recarga = db.query(RecargaAdicional).filter(RecargaAdicional.id == recarga_id).first()
    if not recarga:
        raise HTTPException(status_code=404, detail="Recarga no encontrada")
    
    db.delete(recarga)
    db.commit()
    return {"msg": "Recarga eliminada exitosamente"}

# ===============================================================
# GESTIÓN DE PAQUETES DE RECARGA (ADMIN)
# ===============================================================
@router.get("/paquetes-recarga", response_model=List[consumo_schemas.PaqueteRecargaRead])
def get_paquetes_recarga(
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("utilidades:usar_herramientas"))
):
    return consumo_service.get_all_paquetes(db)

@router.post("/paquetes-recarga", response_model=consumo_schemas.PaqueteRecargaRead)
def create_paquete_recarga(
    paquete: consumo_schemas.PaqueteRecargaCreate,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("utilidades:usar_herramientas"))
):
    return consumo_service.create_paquete(db, **paquete.dict())

@router.put("/paquetes-recarga/{paquete_id}", response_model=consumo_schemas.PaqueteRecargaRead)
def update_paquete_recarga(
    paquete_id: int,
    paquete: consumo_schemas.PaqueteRecargaUpdate,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("utilidades:usar_herramientas"))
):
    updated = consumo_service.update_paquete(db, paquete_id, **paquete.dict())
    if not updated:
        raise HTTPException(status_code=404, detail="Paquete no encontrado")
    return updated

@router.delete("/paquetes-recarga/{paquete_id}")
def delete_paquete_recarga(
    paquete_id: int,
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("utilidades:usar_herramientas"))
):
    if not consumo_service.delete_paquete(db, paquete_id):
        raise HTTPException(status_code=404, detail="Paquete no encontrado")
    return {"msg": "Paquete eliminado exitosamente"}

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
    current_user: models_usuario.Usuario = Depends(has_permission("empresa:gestionar"))
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
    # 1. Obtener Data
    data = migracion_service.exportar_datos(db=db, export_request=export_request, empresa_id=current_user.empresa_id)
    
    # 2. Obtener Nombre Empresa
    from app.models.empresa import Empresa
    from fastapi.responses import JSONResponse, Response
    from datetime import datetime
    import re

    empresa = db.query(Empresa).filter(Empresa.id == current_user.empresa_id).first()
    nombre_empresa = empresa.razon_social if empresa else "Empresa"
    
    # 3. Sanitizar nombre de archivo
    # Reemplazar caracteres ilegales y espacios. Asegurar que no haya saltos de línea.
    safe_name = nombre_empresa.strip()
    safe_name = re.sub(r'[\r\n\t]', '', safe_name) # Eliminar control chars
    safe_name = re.sub(r'[\\/*?:"<>|]', "", safe_name) # Eliminar prohibidos OS
    nombre_clean = safe_name.replace(" ", "_")
    
    # 4. Construir Filename
    fecha_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"backup_contable_{nombre_clean}_{fecha_str}.json"
    
    # 5. Retornar como Stream Binario (Fuerza descarga correcta)
    import json
    json_content = json.dumps(data)
    
    return Response(
        content=json_content,
        media_type="application/octet-stream", # Forza al navegador a guardar como archivo
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.post("/backup-rapido")
def backup_rapido(current_user: models_usuario.Usuario = Depends(has_permission("utilidades:migracion")), db: Session = Depends(get_db)):
    """Genera un backup completo inmediato (para uso por comandos de voz/AI)"""
    return migracion_service.generar_backup_json(db=db, empresa_id=current_user.empresa_id, filtros=None)


# --- RUTAS PARA COPIA AUTOMÁTICA ---
from app.services import scheduler_backup

@router.get("/backup-auto-config", response_model=migracion_schemas.AutoBackupConfig)
def get_backup_config(current_user: models_usuario.Usuario = Depends(has_permission("utilidades:migracion"))):
    return scheduler_backup.load_config(empresa_id=current_user.empresa_id)

@router.post("/backup-auto-config")
def update_backup_config(config: migracion_schemas.AutoBackupConfig, current_user: models_usuario.Usuario = Depends(has_permission("utilidades:migracion"))):
    scheduler_backup.save_config(config.dict(), empresa_id=current_user.empresa_id)
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

# --- LEGACY IMPORT ENDPOINT ---
from fastapi import UploadFile, File, Form
from app.services import legacy_import_service
from datetime import datetime

@router.post("/importar-legacy")
async def importar_legacy(
    empresa_id: int = Form(...),
    periodo_fecha: str = Form(...), # YYYY-MM-DD
    default_tercero_id: Optional[int] = Form(None),
    file_coma: UploadFile = File(None),
    file_coni: UploadFile = File(None),
    file_cotr: UploadFile = File(None),
    file_txt: UploadFile = File(None), # Nuevo soporte TXT
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("utilidades:migracion"))
):
    try:
        content_coma = await file_coma.read() if file_coma else None
        content_coni = await file_coni.read() if file_coni else None
        content_cotr = await file_cotr.read() if file_cotr else None
        content_txt = await file_txt.read() if file_txt else None
        
        p_date = datetime.strptime(periodo_fecha, "%Y-%m-%d").date()
        
        return legacy_import_service.import_legacy_data(
            db=db,
            empresa_id=empresa_id,
            period_date=p_date,
            default_tercero_id=default_tercero_id,
            file_coma=content_coma,
            file_coni=content_coni,
            file_cotr=content_cotr,
            file_txt=content_txt
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en importación legacy: {str(e)}")

# --- UNIVERSAL EXCEL IMPORT ENDPOINT ---
from app.services.universal_import_service import UniversalImportService

@router.post("/importar-universal")
async def importar_universal(
    empresa_id: int = Form(...),
    default_tercero_id: Optional[int] = Form(None),
    template_id: Optional[int] = Form(None), # Nuevo soporte de plantillas
    file_excel: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: models_usuario.Usuario = Depends(has_permission("utilidades:migracion"))
):
    """
    Importa Movimientos Contables desde el 'Formato Universal ContaPY' (Excel).
    Soporta plantillas personalizadas si se envía template_id.
    """
    try:
        content = await file_excel.read()
        
        return UniversalImportService.process_import(
            db=db,
            empresa_id=empresa_id,
            file_content=content,
            default_tercero_id=default_tercero_id,
            template_id=template_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en importación universal: {str(e)}")

@router.delete("/limpiar-legacy")
def limpiar_legacy(db: Session = Depends(get_db)):
    from sqlalchemy import text
    try:
        # Delete Documents
        docs = db.execute(text("SELECT id FROM documentos WHERE tipo_documento_id IN (SELECT id FROM tipos_documento WHERE codigo IN ('CD-L', 'CD-LEGACY'))")).fetchall()
        ids = [str(r[0]) for r in docs]
        
        if ids:
            ids_str = ",".join(ids)
            db.execute(text(f"DELETE FROM movimientos_contables WHERE documento_id IN ({ids_str})"))
            db.execute(text(f"DELETE FROM documentos WHERE id IN ({ids_str})"))
            
        # Delete Garbage Accounts
        db.execute(text("DELETE FROM plan_cuentas WHERE nombre LIKE '%ÿ%'"))
        
        # Delete Garbage Third Parties
        db.execute(text("DELETE FROM terceros WHERE razon_social LIKE '%ÿ%'"))
        
        db.commit()
        return {"message": "Limpieza completada con exito"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/purgar-tipo-documento/{tipo_id}")
def purgar_tipo_documento(
    tipo_id: int, 
    db: Session = Depends(get_db), 
    current_user: models_usuario.Usuario = Depends(get_current_user)
):
    """
    ELIMINACIÓN FUERTE de un Tipo de Documento y toda su basura asociada (Documentos Eliminados/Anulados).
    Solo se permite si NO hay documentos ACTIVOS usando este tipo.
    """
    from app.models import Documento, DocumentoEliminado, TipoDocumento, MovimientoEliminado
    from sqlalchemy import text
    
    # 1. Verificar existencia
    tipo = db.query(TipoDocumento).filter_by(id=tipo_id).first()
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de documento no encontrado.")
        
    # 2. Verificar Documentos ACTIVOS (Bloqueante)
    active_docs = db.query(Documento).filter(
        Documento.tipo_documento_id == tipo_id,
        Documento.estado != 'ANULADO' # Si está anulado, asumimos que es "basura" erradicable según solicitud
    ).count()
    
    if active_docs > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"No se puede purgar: Existen {active_docs} documentos ACTIVOS de este tipo. Debes anularlos o eliminarlos primero."
        )
        
    try:
        # 3. Eliminar Documentos "Papelera" (Hard Delete)
        # Buscar IDs de DocEliminados
        deleted_docs_query = db.query(DocumentoEliminado.id).filter_by(tipo_documento_id=tipo_id)
        deleted_ids = [d[0] for d in deleted_docs_query.all()]
        
        if deleted_ids:
            # Delete MovimientosEliminados
            db.query(MovimientoEliminado).filter(MovimientoEliminado.documento_eliminado_id.in_(deleted_ids)).delete(synchronize_session=False)
            # Delete DocumentosEliminados
            db.query(DocumentoEliminado).filter(DocumentoEliminado.id.in_(deleted_ids)).delete(synchronize_session=False)
            
        # 4. Eliminar Documentos ANULADOS (Hard Delete) - "Basura" en tabla principal
        # Anulados siguen en tabla Documento, pero si el usuario quiere purgar el TIPO, deben irse.
        anulados_query = db.query(Documento).filter_by(tipo_documento_id=tipo_id)
        anulados_ids = [d.id for d in anulados_query.all()]
        
        if anulados_ids:
             # Delete Movimietos (Cascade should handle, but manual to be safe if no cascade)
             db.execute(text(f"DELETE FROM movimientos_contables WHERE documento_id IN ({','.join(map(str, anulados_ids))})"))
             db.query(Documento).filter(Documento.id.in_(anulados_ids)).delete(synchronize_session=False)
             
        # 5. Eliminar el Tipo Documento
        db.delete(tipo)
        
        db.commit()
        return {"msg": f"Tipo '{tipo.nombre}' y todos sus rastros han sido purgados exitosamente."}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al purgar: {str(e)}")

# ===============================================================
# CONFIGURACIÓN DEL SISTEMA (Relacionado con Consumo/Precios)
# ===============================================================
@router.get("/config/precio-registro")
def get_precio_registro(db: Session = Depends(get_db)):
    """Obtiene el precio por registro configurado en el sistema."""
    from app.models.configuracion_sistema import ConfiguracionSistema
    from sqlalchemy import inspect
    
    if not inspect(db.get_bind()).has_table("configuracion_sistema"):
        return {"precio": 150}

    config = db.query(ConfiguracionSistema).filter_by(clave="PRECIO_POR_REGISTRO").first()
    return {"precio": int(config.valor) if config else 150}

# Rutas de precio por empresa MOVIDAS a app/api/empresas/routes.py

@router.post("/config/precio-registro")
def set_precio_registro(
    data: dict, 
    db: Session = Depends(get_db), 
    current_user: models_usuario.Usuario = Depends(has_permission("utilidades:usar_herramientas"))
):
    """Actualiza el precio por registro (Solo Soporte)."""
    from app.models.configuracion_sistema import ConfiguracionSistema
    from sqlalchemy import inspect
    
    if not inspect(db.get_bind()).has_table("configuracion_sistema"):
        ConfiguracionSistema.__table__.create(db.get_bind())

    nuevo_precio = str(data.get("precio", 150))
    
    config = db.query(ConfiguracionSistema).filter_by(clave="PRECIO_POR_REGISTRO").first()
    if config:
        config.valor = nuevo_precio
    else:
        new_config = ConfiguracionSistema(clave="PRECIO_POR_REGISTRO", valor=nuevo_precio)
        db.add(new_config)
    
    db.commit()
    return {"msg": "Precio actualizado correctamente", "precio": int(nuevo_precio)}


    db.commit()
    return {"msg": "Precio actualizado correctamente", "precio": int(nuevo_precio)}
