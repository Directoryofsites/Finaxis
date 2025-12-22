from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
import tempfile
import os

from ...core.database import get_db
from ...models.conciliacion_bancaria import ImportConfig, ImportSession, BankMovement
from ...schemas.conciliacion_bancaria import (
    ImportConfig as ImportConfigSchema,
    ImportConfigCreate,
    ImportConfigUpdate,
    ImportSession as ImportSessionSchema,
    BankMovement as BankMovementSchema,
    FileValidationResult,
    DuplicateReport
)
from ...services.conciliacion_bancaria import ImportEngine, ConfigurationManager, MatchingEngine, AuditService, SecurityService
from ...core.security import get_current_user, has_permission
from ...models.usuario import Usuario

router = APIRouter(prefix="/conciliacion-bancaria", tags=["Conciliación Bancaria"])


# ==================== CONFIGURACIONES DE IMPORTACIÓN ====================

@router.post("/import-configs", response_model=ImportConfigSchema)
async def create_import_config(
    config: ImportConfigCreate,
    current_user: Usuario = Depends(has_permission("conciliacion_bancaria:configurar")),
    db: Session = Depends(get_db)
):
    """Crear nueva configuración de importación"""
    try:
        db_config = ImportConfig(
            **config.dict(),
            empresa_id=current_user.empresa_id,
            created_by=current_user.id
        )
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        return db_config
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creando configuración: {str(e)}")


@router.get("/import-configs", response_model=List[ImportConfigSchema])
async def get_import_configs(
    bank_id: Optional[int] = None,
    current_user: Usuario = Depends(has_permission("conciliacion_bancaria:ver")),
    db: Session = Depends(get_db)
):
    """Obtener configuraciones de importación"""
    query = db.query(ImportConfig).filter(ImportConfig.empresa_id == current_user.empresa_id)
    
    if bank_id:
        query = query.filter(ImportConfig.bank_id == bank_id)
    
    return query.filter(ImportConfig.is_active == True).all()


@router.get("/import-configs/{config_id}", response_model=ImportConfigSchema)
async def get_import_config(
    config_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener configuración específica"""
    config = db.query(ImportConfig).filter(
        ImportConfig.id == config_id,
        ImportConfig.empresa_id == current_user.empresa_id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    
    return config


@router.put("/import-configs/{config_id}", response_model=ImportConfigSchema)
async def update_import_config(
    config_id: int,
    config_update: ImportConfigUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar configuración de importación"""
    config = db.query(ImportConfig).filter(
        ImportConfig.id == config_id,
        ImportConfig.empresa_id == current_user.empresa_id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    
    try:
        update_data = config_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)
        
        config.updated_by = current_user.id
        db.commit()
        db.refresh(config)
        return config
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error actualizando configuración: {str(e)}")


@router.delete("/import-configs/{config_id}")
async def delete_import_config(
    config_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Desactivar configuración de importación"""
    config = db.query(ImportConfig).filter(
        ImportConfig.id == config_id,
        ImportConfig.empresa_id == current_user.empresa_id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    
    try:
        config.is_active = False
        config.updated_by = current_user.id
        db.commit()
        return {"message": "Configuración desactivada exitosamente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error desactivando configuración: {str(e)}")


@router.post("/import-configs/{config_id}/validate", response_model=FileValidationResult)
async def validate_config_with_sample(
    config_id: int,
    file: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validar configuración con archivo de muestra"""
    config = db.query(ImportConfig).filter(
        ImportConfig.id == config_id,
        ImportConfig.empresa_id == current_user.empresa_id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    
    # Guardar archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{config.file_format.lower()}") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name
    
    try:
        import_engine = ImportEngine(db)
        result = import_engine.validate_file(temp_file_path, config_id)
        return result
    finally:
        # Limpiar archivo temporal
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


@router.post("/import-configs/{config_id}/test")
async def test_configuration_with_sample(
    config_id: int,
    file: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Probar configuración con archivo de muestra completo"""
    try:
        config_manager = ConfigurationManager(db)
        
        # Guardar archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            result = config_manager.test_configuration_with_sample(
                config_id, 
                temp_file_path, 
                current_user.empresa_id
            )
            return result
        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error probando configuración: {str(e)}")


@router.post("/import-configs/test")
async def test_configuration_without_file(
    config_data: dict,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Probar configuración sin archivo (solo validar estructura)"""
    try:
        config_manager = ConfigurationManager(db)
        
        # Validar estructura de configuración
        result = config_manager.validate_configuration_structure(config_data)
        
        return {
            "success": result["is_valid"],
            "message": result.get("message", "Configuración válida"),
            "errors": result.get("errors", []),
            "warnings": result.get("warnings", [])
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error validando configuración"
        }


@router.post("/import-configs/{config_id}/duplicate")
async def duplicate_configuration(
    config_id: int,
    new_name: str = Form(...),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Duplicar una configuración existente"""
    try:
        config_manager = ConfigurationManager(db)
        
        config = config_manager.duplicate_configuration(
            config_id, 
            new_name, 
            current_user.empresa_id, 
            current_user.id
        )
        
        return config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error duplicando configuración: {str(e)}")


@router.get("/import-configs/{config_id}/audit")
async def get_configuration_audit_trail(
    config_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener historial de cambios de una configuración"""
    try:
        config_manager = ConfigurationManager(db)
        audit_trail = config_manager.get_configuration_audit_trail(config_id, current_user.empresa_id)
        return {"audit_trail": audit_trail}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo historial: {str(e)}")


@router.get("/import-configs/by-bank/{bank_name}")
async def get_configurations_by_bank(
    bank_name: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener configuraciones filtradas por banco"""
    try:
        config_manager = ConfigurationManager(db)
        configurations = config_manager.get_configurations_by_bank(bank_name, current_user.empresa_id)
        return configurations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo configuraciones: {str(e)}")


# ==================== IMPORTACIÓN DE ARCHIVOS ====================

@router.post("/import", response_model=ImportSessionSchema)
async def import_bank_statement(
    file: UploadFile = File(...),
    config_id: int = Form(...),
    bank_account_id: int = Form(...),
    current_user: Usuario = Depends(has_permission("conciliacion_bancaria:importar")),
    db: Session = Depends(get_db)
):
    """Importar extracto bancario"""
    # Verificar configuración
    config = db.query(ImportConfig).filter(
        ImportConfig.id == config_id,
        ImportConfig.empresa_id == current_user.empresa_id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    
    # Guardar archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{config.file_format.lower()}") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name
    
    try:
        import_engine = ImportEngine(db)
        
        # 1. Validar archivo
        validation_result = import_engine.validate_file(temp_file_path, config_id)
        if not validation_result.is_valid:
            raise HTTPException(
                status_code=400, 
                detail={
                    "message": "Archivo inválido",
                    "errors": validation_result.errors
                }
            )
        
        # 2. Crear sesión de importación
        import_session = import_engine.create_import_session(
            temp_file_path, config_id, bank_account_id, current_user.empresa_id, current_user.id
        )
        
        # 3. Parsear movimientos
        movements = import_engine.parse_bank_statement(temp_file_path, config)
        
        # 4. Detectar duplicados
        duplicate_report = import_engine.detect_duplicates(movements, bank_account_id)
        
        if duplicate_report.action_required:
            # Actualizar sesión con información de duplicados
            import_engine.update_import_session(
                import_session.id,
                len(movements),
                0,
                [f"Se encontraron {duplicate_report.total_duplicates} posibles duplicados"],
                "PENDING_REVIEW"
            )
            
            return {
                **import_session.__dict__,
                "duplicate_report": duplicate_report
            }
        
        # 5. Almacenar movimientos
        store_result = import_engine.store_movements(
            movements, import_session.id, bank_account_id, current_user.empresa_id
        )
        
        # 6. Actualizar sesión
        import_engine.update_import_session(
            import_session.id,
            len(movements),
            store_result['total_stored'],
            [],
            "COMPLETED"
        )
        
        db.refresh(import_session)
        return import_session
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importando archivo: {str(e)}")
    finally:
        # Limpiar archivo temporal
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


@router.post("/import/{session_id}/confirm-duplicates")
async def confirm_duplicates_import(
    session_id: str,
    skip_duplicates: bool = Form(True),
    current_user: Usuario = Depends(has_permission("conciliacion_bancaria:importar")),
    db: Session = Depends(get_db)
):
    """Confirmar importación con duplicados"""
    session = db.query(ImportSession).filter(
        ImportSession.id == session_id,
        ImportSession.empresa_id == current_user.empresa_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Sesión de importación no encontrada")
    
    if session.status != "PENDING_REVIEW":
        raise HTTPException(status_code=400, detail="Sesión no está pendiente de revisión")
    
    try:
        # Aquí implementarías la lógica para manejar duplicados
        # Por ahora, simplemente marcamos como completada
        session.status = "COMPLETED"
        session.successful_imports = session.total_movements
        db.commit()
        
        return {"message": "Importación confirmada exitosamente"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error confirmando importación: {str(e)}")


# ==================== CONSULTAS ====================

@router.get("/import-sessions", response_model=List[ImportSessionSchema])
async def get_import_sessions(
    bank_account_id: Optional[int] = None,
    status: Optional[str] = None,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener sesiones de importación"""
    query = db.query(ImportSession).filter(ImportSession.empresa_id == current_user.empresa_id)
    
    if bank_account_id:
        query = query.filter(ImportSession.bank_account_id == bank_account_id)
    
    if status:
        query = query.filter(ImportSession.status == status)
    
    return query.order_by(ImportSession.import_date.desc()).all()


@router.get("/import-sessions/{session_id}", response_model=ImportSessionSchema)
async def get_import_session(
    session_id: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener sesión específica"""
    session = db.query(ImportSession).filter(
        ImportSession.id == session_id,
        ImportSession.empresa_id == current_user.empresa_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    return session


@router.get("/bank-movements", response_model=List[BankMovementSchema])
async def get_bank_movements(
    bank_account_id: Optional[int] = None,
    import_session_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener movimientos bancarios"""
    query = db.query(BankMovement).filter(BankMovement.empresa_id == current_user.empresa_id)
    
    if bank_account_id:
        query = query.filter(BankMovement.bank_account_id == bank_account_id)
    
    if import_session_id:
        query = query.filter(BankMovement.import_session_id == import_session_id)
    
    if status:
        query = query.filter(BankMovement.status == status)
    
    return query.order_by(BankMovement.transaction_date.desc()).offset(offset).limit(limit).all()


@router.get("/bank-movements/{movement_id}", response_model=BankMovementSchema)
async def get_bank_movement(
    movement_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener movimiento específico"""
    movement = db.query(BankMovement).filter(
        BankMovement.id == movement_id,
        BankMovement.empresa_id == current_user.empresa_id
    ).first()
    
    if not movement:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    
    return movement


# ==================== MOTOR DE CONCILIACIÓN AUTOMÁTICA ====================

@router.post("/reconcile/auto")
async def auto_reconcile(
    bank_account_id: int = Form(...),
    date_from: Optional[str] = Form(None),
    date_to: Optional[str] = Form(None),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ejecutar conciliación automática"""
    try:
        matching_engine = MatchingEngine(db)
        
        # Convertir fechas si se proporcionan
        date_from_obj = None
        date_to_obj = None
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
        
        if date_to:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
        
        result = matching_engine.auto_match(
            bank_account_id, 
            current_user.empresa_id,
            date_from_obj,
            date_to_obj
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en conciliación automática: {str(e)}")


@router.get("/reconcile/summary/{bank_account_id}")
async def get_reconciliation_summary(
    bank_account_id: int,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener resumen del estado de conciliación"""
    try:
        matching_engine = MatchingEngine(db)
        
        # Convertir fechas si se proporcionan
        date_from_obj = None
        date_to_obj = None
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
        
        if date_to:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
        
        summary = matching_engine.get_reconciliation_summary(
            bank_account_id,
            current_user.empresa_id,
            date_from_obj,
            date_to_obj
        )
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando resumen: {str(e)}")


@router.get("/reconcile/suggestions/{bank_movement_id}")
async def get_match_suggestions(
    bank_movement_id: int,
    limit: int = 5,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener sugerencias de conciliación para un movimiento bancario"""
    try:
        matching_engine = MatchingEngine(db)
        
        suggestions = matching_engine.suggest_matches(
            bank_movement_id,
            current_user.empresa_id,
            limit
        )
        
        # Formatear respuesta
        formatted_suggestions = []
        for suggestion in suggestions:
            acc_mov = suggestion["accounting_movement"]
            formatted_suggestions.append({
                "accounting_movement": {
                    "id": acc_mov.id,
                    "fecha": acc_mov.fecha.isoformat(),
                    "valor": float(acc_mov.valor),
                    "concepto": acc_mov.concepto,
                    "referencia": acc_mov.referencia,
                    "debito_credito": acc_mov.debito_credito
                },
                "confidence_score": suggestion["confidence_score"],
                "criteria_matched": suggestion["criteria_matched"],
                "date_difference": suggestion["date_difference"],
                "amount_difference": suggestion["amount_difference"],
                "reference_similarity": suggestion["reference_similarity"]
            })
        
        return {
            "bank_movement_id": bank_movement_id,
            "suggestions": formatted_suggestions
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando sugerencias: {str(e)}")


@router.post("/reconcile/manual")
async def apply_manual_reconciliation(
    bank_movement_id: int = Form(...),
    accounting_movement_ids: str = Form(...),  # IDs separados por coma
    notes: Optional[str] = Form(None),
    current_user: Usuario = Depends(has_permission("conciliacion_bancaria:conciliar")),
    db: Session = Depends(get_db)
):
    """Aplicar conciliación manual"""
    try:
        # Servicios de seguridad y auditoría
        security_service = SecurityService(db)
        audit_service = AuditService(db)
        
        # Validar acceso al movimiento bancario
        bank_movement = db.query(BankMovement).filter(
            BankMovement.id == bank_movement_id,
            BankMovement.empresa_id == current_user.empresa_id
        ).first()
        
        if not bank_movement:
            audit_service.log_operation(
                "UNAUTHORIZED_ACCESS_ATTEMPT", current_user.id, current_user.empresa_id,
                new_values={"attempted_bank_movement_id": bank_movement_id, "reason": "Movement not found or access denied"}
            )
            raise HTTPException(status_code=404, detail="Movimiento bancario no encontrado")
        
        # Verificar límite de tasa
        if not security_service.check_rate_limit(current_user.id, "MANUAL_RECONCILIATION", 60, 50):
            security_service.log_suspicious_activity(
                current_user.id, current_user.empresa_id, "RATE_LIMIT_EXCEEDED",
                f"Excedido límite de conciliaciones manuales por hora"
            )
            raise HTTPException(status_code=429, detail="Límite de operaciones excedido. Intente más tarde.")
        
        matching_engine = MatchingEngine(db)
        
        # Parsear IDs de movimientos contables
        acc_movement_ids = [int(id.strip()) for id in accounting_movement_ids.split(",")]
        
        # Registrar inicio de operación
        audit_service.log_operation(
            "MANUAL_RECONCILIATION_START", current_user.id, current_user.empresa_id,
            new_values={
                "bank_movement_id": bank_movement_id,
                "accounting_movement_ids": acc_movement_ids,
                "notes": notes
            }
        )
        
        result = matching_engine.apply_manual_match(
            bank_movement_id,
            acc_movement_ids,
            current_user.empresa_id,
            current_user.id,
            notes
        )
        
        # Registrar éxito de operación
        audit_service.log_operation(
            "MANUAL_RECONCILIATION_SUCCESS", current_user.id, current_user.empresa_id,
            reconciliation_id=result.get("reconciliation_id"),
            new_values={"result": "success", "reconciliation_id": result.get("reconciliation_id")}
        )
        
        return result
        
    except ValueError as e:
        audit_service.log_operation(
            "MANUAL_RECONCILIATION_ERROR", current_user.id, current_user.empresa_id,
            new_values={"error": str(e), "error_type": "ValueError"}
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        audit_service.log_operation(
            "MANUAL_RECONCILIATION_ERROR", current_user.id, current_user.empresa_id,
            new_values={"error": str(e), "error_type": "Exception"}
        )
        raise HTTPException(status_code=500, detail=f"Error en conciliación manual: {str(e)}")


@router.post("/reconcile/reverse/{reconciliation_id}")
async def reverse_reconciliation(
    reconciliation_id: int,
    reason: str = Form(...),
    current_user: Usuario = Depends(has_permission("conciliacion_bancaria:conciliar")),
    db: Session = Depends(get_db)
):
    """Revertir una conciliación existente"""
    try:
        matching_engine = MatchingEngine(db)
        
        result = matching_engine.reverse_reconciliation(
            reconciliation_id,
            current_user.empresa_id,
            current_user.id,
            reason
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error revirtiendo conciliación: {str(e)}")


@router.get("/reconciliations")
async def get_reconciliations(
    bank_account_id: Optional[int] = None,
    reconciliation_type: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener lista de conciliaciones"""
    try:
        from ...models.conciliacion_bancaria import Reconciliation, BankMovement
        
        query = db.query(Reconciliation).join(BankMovement).filter(
            Reconciliation.empresa_id == current_user.empresa_id
        )
        
        if bank_account_id:
            query = query.filter(BankMovement.bank_account_id == bank_account_id)
        
        if reconciliation_type:
            query = query.filter(Reconciliation.reconciliation_type == reconciliation_type)
        
        if status:
            query = query.filter(Reconciliation.status == status)
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
            query = query.filter(BankMovement.transaction_date >= date_from_obj)
        
        if date_to:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
            query = query.filter(BankMovement.transaction_date <= date_to_obj)
        
        reconciliations = query.order_by(
            Reconciliation.reconciliation_date.desc()
        ).offset(offset).limit(limit).all()
        
        # Formatear respuesta
        result = []
        for rec in reconciliations:
            result.append({
                "id": rec.id,
                "bank_movement_id": rec.bank_movement_id,
                "reconciliation_type": rec.reconciliation_type,
                "confidence_score": float(rec.confidence_score) if rec.confidence_score else None,
                "reconciliation_date": rec.reconciliation_date.isoformat(),
                "notes": rec.notes,
                "status": rec.status,
                "user_id": rec.user_id,
                "bank_movement": {
                    "id": rec.bank_movement.id,
                    "transaction_date": rec.bank_movement.transaction_date.isoformat(),
                    "amount": float(rec.bank_movement.amount),
                    "description": rec.bank_movement.description,
                    "reference": rec.bank_movement.reference
                },
                "accounting_movements_count": len(rec.accounting_movements)
            })
        
        return {
            "reconciliations": result,
            "total": query.count(),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo conciliaciones: {str(e)}")


@router.get("/reconciliations/{reconciliation_id}")
async def get_reconciliation_detail(
    reconciliation_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener detalle de una conciliación específica"""
    try:
        from ...models.conciliacion_bancaria import Reconciliation
        
        reconciliation = db.query(Reconciliation).filter(
            Reconciliation.id == reconciliation_id,
            Reconciliation.empresa_id == current_user.empresa_id
        ).first()
        
        if not reconciliation:
            raise HTTPException(status_code=404, detail="Conciliación no encontrada")
        
        # Obtener movimientos contables asociados
        accounting_movements = []
        for rec_mov in reconciliation.accounting_movements:
            acc_mov = rec_mov.accounting_movement
            accounting_movements.append({
                "id": acc_mov.id,
                "fecha": acc_mov.fecha.isoformat(),
                "valor": float(acc_mov.valor),
                "concepto": acc_mov.concepto,
                "referencia": acc_mov.referencia,
                "debito_credito": acc_mov.debito_credito
            })
        
        return {
            "id": reconciliation.id,
            "bank_movement": {
                "id": reconciliation.bank_movement.id,
                "transaction_date": reconciliation.bank_movement.transaction_date.isoformat(),
                "amount": float(reconciliation.bank_movement.amount),
                "description": reconciliation.bank_movement.description,
                "reference": reconciliation.bank_movement.reference,
                "status": reconciliation.bank_movement.status
            },
            "accounting_movements": accounting_movements,
            "reconciliation_type": reconciliation.reconciliation_type,
            "confidence_score": float(reconciliation.confidence_score) if reconciliation.confidence_score else None,
            "reconciliation_date": reconciliation.reconciliation_date.isoformat(),
            "notes": reconciliation.notes,
            "status": reconciliation.status,
            "user_id": reconciliation.user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo detalle: {str(e)}")


# ==================== CONFIGURACIÓN CONTABLE ====================

@router.get("/accounting-config/{bank_account_id}")
async def get_accounting_configuration(
    bank_account_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener configuración contable para una cuenta bancaria"""
    try:
        from ...models.conciliacion_bancaria import AccountingConfig
        
        config = db.query(AccountingConfig).filter(
            AccountingConfig.bank_account_id == bank_account_id,
            AccountingConfig.empresa_id == current_user.empresa_id,
            AccountingConfig.is_active == True
        ).first()
        
        if not config:
            raise HTTPException(status_code=404, detail="Configuración contable no encontrada")
        
        return {
            "id": config.id,
            "bank_account_id": config.bank_account_id,
            "commission_account_id": config.commission_account_id,
            "interest_income_account_id": config.interest_income_account_id,
            "bank_charges_account_id": config.bank_charges_account_id,
            "adjustment_account_id": config.adjustment_account_id,
            "default_cost_center_id": config.default_cost_center_id,
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo configuración: {str(e)}")


@router.get("/test-bank-accounts")
async def test_bank_accounts(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Endpoint de prueba para verificar cuentas bancarias"""
    try:
        from ...models.plan_cuenta import PlanCuenta
        
        print(f"[TEST] Buscando cuentas para empresa: {current_user.empresa_id}")
        
        # Buscar todas las cuentas que empiecen con 111
        bank_accounts = db.query(PlanCuenta).filter(
            PlanCuenta.codigo.like('111%'),
            PlanCuenta.empresa_id == current_user.empresa_id
        ).all()
        
        print(f"[TEST] Cuentas encontradas: {len(bank_accounts)}")
        
        result = []
        for acc in bank_accounts:
            print(f"[TEST] - {acc.codigo}: {acc.nombre} (ID: {acc.id})")
            result.append({
                "id": acc.id,
                "codigo": acc.codigo,
                "nombre": acc.nombre,
                "permite_movimiento": acc.permite_movimiento
            })
        
        return {
            "empresa_id": current_user.empresa_id,
            "total_cuentas": len(result),
            "cuentas": result
        }
        
    except Exception as e:
        print(f"[TEST] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.put("/accounting-config/{bank_account_id}")
async def update_accounting_configuration(
    bank_account_id: int,
    config_data: dict,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar o crear configuración contable para una cuenta bancaria"""
    print(f"[ACCOUNTING CONFIG] ===== INICIO ENDPOINT =====")
    print(f"[ACCOUNTING CONFIG] bank_account_id recibido: {bank_account_id}")
    print(f"[ACCOUNTING CONFIG] config_data recibido: {config_data}")
    print(f"[ACCOUNTING CONFIG] empresa_id: {current_user.empresa_id}")
    
    try:
        from ...models.conciliacion_bancaria import AccountingConfig
        from ...models.plan_cuenta import PlanCuenta
        
        # SOLUCIÓN: Buscar la cuenta bancaria real por código en lugar de asumir el ID
        print(f"[ACCOUNTING CONFIG] Buscando cuenta bancaria con ID: {bank_account_id}")
        
        # Primero, intentar encontrar la cuenta por ID
        bank_account = db.query(PlanCuenta).filter(
            PlanCuenta.id == bank_account_id,
            PlanCuenta.empresa_id == current_user.empresa_id
        ).first()
        
        print(f"[ACCOUNTING CONFIG] Cuenta encontrada por ID: {bank_account is not None}")
        
        # Si no se encuentra por ID, buscar por código común de cuentas bancarias
        if not bank_account:
            print(f"[ACCOUNTING CONFIG] Buscando cuentas bancarias con código 111% para empresa {current_user.empresa_id}")
            
            # Buscar cuentas que empiecen con 111 (cuentas bancarias típicas)
            bank_accounts = db.query(PlanCuenta).filter(
                PlanCuenta.codigo.like('111%'),
                PlanCuenta.empresa_id == current_user.empresa_id,
                PlanCuenta.permite_movimiento == True
            ).all()
            
            print(f"[ACCOUNTING CONFIG] Cuentas bancarias encontradas: {len(bank_accounts)}")
            for acc in bank_accounts:
                print(f"[ACCOUNTING CONFIG] - {acc.codigo}: {acc.nombre} (ID: {acc.id})")
            
            if bank_accounts:
                # Tomar la primera cuenta bancaria encontrada
                bank_account = bank_accounts[0]
                # Actualizar el bank_account_id para usar el ID correcto
                bank_account_id = bank_account.id
                print(f"[ACCOUNTING CONFIG] Usando cuenta bancaria: {bank_account.codigo} (ID: {bank_account.id})")
            else:
                print(f"[ACCOUNTING CONFIG] ERROR: No se encontraron cuentas bancarias")
                raise HTTPException(
                    status_code=404, 
                    detail="No se encontró ninguna cuenta bancaria válida. Asegúrate de tener cuentas que empiecen con '111' en tu plan de cuentas."
                )
        
        # Buscar configuración existente
        config = db.query(AccountingConfig).filter(
            AccountingConfig.bank_account_id == bank_account_id,
            AccountingConfig.empresa_id == current_user.empresa_id
        ).first()
        
        if config:
            # Actualizar configuración existente
            config.commission_account_id = config_data.get('commission_account_id')
            config.interest_income_account_id = config_data.get('interest_income_account_id')
            config.bank_charges_account_id = config_data.get('bank_charges_account_id')
            config.adjustment_account_id = config_data.get('adjustment_account_id')
            config.default_cost_center_id = config_data.get('default_cost_center_id')
            config.updated_at = datetime.utcnow()
            config.updated_by = current_user.id
            config.is_active = True
        else:
            # Crear nueva configuración
            config = AccountingConfig(
                bank_account_id=bank_account_id,
                empresa_id=current_user.empresa_id,
                commission_account_id=config_data.get('commission_account_id'),
                interest_income_account_id=config_data.get('interest_income_account_id'),
                bank_charges_account_id=config_data.get('bank_charges_account_id'),
                adjustment_account_id=config_data.get('adjustment_account_id'),
                default_cost_center_id=config_data.get('default_cost_center_id'),
                created_by=current_user.id,
                is_active=True
            )
            db.add(config)
        
        db.commit()
        db.refresh(config)
        
        return {
            "id": config.id,
            "bank_account_id": config.bank_account_id,
            "bank_account_code": bank_account.codigo,
            "bank_account_name": bank_account.nombre,
            "commission_account_id": config.commission_account_id,
            "interest_income_account_id": config.interest_income_account_id,
            "bank_charges_account_id": config.bank_charges_account_id,
            "adjustment_account_id": config.adjustment_account_id,
            "default_cost_center_id": config.default_cost_center_id,
            "message": "Configuración guardada exitosamente"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error guardando configuración: {str(e)}")


@router.delete("/accounting-config/{bank_account_id}")
async def delete_accounting_configuration(
    bank_account_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Desactivar configuración contable"""
    try:
        from ...models.conciliacion_bancaria import AccountingConfig
        
        config = db.query(AccountingConfig).filter(
            AccountingConfig.bank_account_id == bank_account_id,
            AccountingConfig.empresa_id == current_user.empresa_id
        ).first()
        
        if not config:
            raise HTTPException(status_code=404, detail="Configuración no encontrada")
        
        config.is_active = False
        config.updated_at = datetime.utcnow()
        config.updated_by = current_user.id
        
        db.commit()
        
        return {"message": "Configuración desactivada exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error desactivando configuración: {str(e)}")


@router.get("/accounting-config/{bank_account_id}/validate")
async def validate_accounting_configuration(
    bank_account_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validar configuración contable"""
    try:
        from ...models.conciliacion_bancaria import AccountingConfig
        from ...models.plan_cuenta import PlanCuenta
        
        config = db.query(AccountingConfig).filter(
            AccountingConfig.bank_account_id == bank_account_id,
            AccountingConfig.empresa_id == current_user.empresa_id,
            AccountingConfig.is_active == True
        ).first()
        
        if not config:
            return {
                "is_valid": False,
                "errors": ["No hay configuración contable para esta cuenta bancaria"],
                "warnings": []
            }
        
        errors = []
        warnings = []
        
        # Validar que las cuentas existan
        account_fields = [
            ('commission_account_id', 'Cuenta de comisiones'),
            ('interest_income_account_id', 'Cuenta de intereses'),
            ('bank_charges_account_id', 'Cuenta de cargos bancarios'),
            ('adjustment_account_id', 'Cuenta de ajustes')
        ]
        
        for field, description in account_fields:
            account_id = getattr(config, field)
            if account_id:
                account = db.query(PlanCuenta).filter(
                    PlanCuenta.id == account_id,
                    PlanCuenta.empresa_id == current_user.empresa_id
                ).first()
                
                if not account:
                    errors.append(f"{description}: La cuenta con ID {account_id} no existe")
                elif not account.activa:
                    warnings.append(f"{description}: La cuenta {account.codigo} está inactiva")
            else:
                warnings.append(f"{description}: No está configurada")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "configuration": {
                "commission_account_id": config.commission_account_id,
                "interest_income_account_id": config.interest_income_account_id,
                "bank_charges_account_id": config.bank_charges_account_id,
                "adjustment_account_id": config.adjustment_account_id,
                "default_cost_center_id": config.default_cost_center_id
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validando configuración: {str(e)}")


# ==================== SISTEMA DE REPORTES ====================

@router.get("/reports/generate")
async def generate_reconciliation_report(
    bank_account_id: int,
    report_type: str = "summary",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generar reporte de conciliación"""
    try:
        
        # Convertir fechas
        date_from_obj = None
        date_to_obj = None
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
        if date_to:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
        
        # Generar reporte según el tipo
        if report_type == "summary":
            report_data = await _generate_summary_report(
                bank_account_id, current_user.empresa_id, date_from_obj, date_to_obj, db
            )
        elif report_type == "detailed":
            report_data = await _generate_detailed_report(
                bank_account_id, current_user.empresa_id, date_from_obj, date_to_obj, db
            )
        elif report_type == "adjustments":
            report_data = await _generate_adjustments_report(
                bank_account_id, current_user.empresa_id, date_from_obj, date_to_obj, db
            )
        elif report_type == "unmatched":
            report_data = await _generate_unmatched_report(
                bank_account_id, current_user.empresa_id, date_from_obj, date_to_obj, db
            )
        else:
            raise HTTPException(status_code=400, detail="Tipo de reporte no válido")
        
        return report_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando reporte: {str(e)}")


async def _generate_summary_report(bank_account_id: int, empresa_id: int, 
                                 date_from: date, date_to: date, db: Session):
    """Generar reporte resumen"""
    # Obtener estadísticas generales
    bank_query = db.query(BankMovement).filter(
        BankMovement.bank_account_id == bank_account_id,
        BankMovement.empresa_id == empresa_id
    )
    
    if date_from:
        bank_query = bank_query.filter(BankMovement.transaction_date >= date_from)
    if date_to:
        bank_query = bank_query.filter(BankMovement.transaction_date <= date_to)
    
    total_movements = bank_query.count()
    reconciled_movements = bank_query.filter(BankMovement.status == "MATCHED").count()
    pending_movements = bank_query.filter(BankMovement.status == "PENDING").count()
    
    # Calcular montos
    total_amount = sum([float(m.amount) for m in bank_query.all()])
    reconciliation_rate = (reconciled_movements / total_movements * 100) if total_movements > 0 else 0
    
    # Obtener resumen por tipo de conciliación
    from ...models.conciliacion_bancaria import Reconciliation
    
    rec_query = db.query(Reconciliation).join(BankMovement).filter(
        BankMovement.bank_account_id == bank_account_id,
        Reconciliation.empresa_id == empresa_id,
        Reconciliation.status == "ACTIVE"
    )
    
    if date_from:
        rec_query = rec_query.filter(BankMovement.transaction_date >= date_from)
    if date_to:
        rec_query = rec_query.filter(BankMovement.transaction_date <= date_to)
    
    auto_reconciliations = rec_query.filter(Reconciliation.reconciliation_type == "AUTO").count()
    manual_reconciliations = rec_query.filter(Reconciliation.reconciliation_type == "MANUAL").count()
    
    # Obtener movimientos pendientes (primeros 10)
    pending_query = bank_query.filter(BankMovement.status == "PENDING").limit(10)
    pending_list = []
    
    for movement in pending_query.all():
        pending_list.append({
            "id": movement.id,
            "transaction_date": movement.transaction_date.isoformat(),
            "description": movement.description,
            "reference": movement.reference,
            "amount": float(movement.amount)
        })
    
    return {
        "summary": {
            "total_movements": total_movements,
            "reconciled_movements": reconciled_movements,
            "pending_movements": pending_movements,
            "reconciliation_rate": round(reconciliation_rate, 2),
            "total_amount": total_amount
        },
        "by_type": [
            {
                "type": "AUTO",
                "count": auto_reconciliations,
                "amount": 0,  # TODO: Calcular monto real
                "percentage": round((auto_reconciliations / (auto_reconciliations + manual_reconciliations) * 100) if (auto_reconciliations + manual_reconciliations) > 0 else 0, 2)
            },
            {
                "type": "MANUAL",
                "count": manual_reconciliations,
                "amount": 0,  # TODO: Calcular monto real
                "percentage": round((manual_reconciliations / (auto_reconciliations + manual_reconciliations) * 100) if (auto_reconciliations + manual_reconciliations) > 0 else 0, 2)
            }
        ],
        "pending_movements": pending_list
    }


async def _generate_detailed_report(bank_account_id: int, empresa_id: int, 
                                  date_from: date, date_to: date, db: Session):
    """Generar reporte detallado"""
    from ...models.conciliacion_bancaria import Reconciliation
    
    # Obtener todos los movimientos con información de conciliación
    query = db.query(BankMovement).outerjoin(Reconciliation).filter(
        BankMovement.bank_account_id == bank_account_id,
        BankMovement.empresa_id == empresa_id
    )
    
    if date_from:
        query = query.filter(BankMovement.transaction_date >= date_from)
    if date_to:
        query = query.filter(BankMovement.transaction_date <= date_to)
    
    movements = query.order_by(BankMovement.transaction_date.desc()).all()
    
    detailed_movements = []
    for movement in movements:
        # Buscar reconciliación activa
        reconciliation = db.query(Reconciliation).filter(
            Reconciliation.bank_movement_id == movement.id,
            Reconciliation.status == "ACTIVE"
        ).first()
        
        detailed_movements.append({
            "id": movement.id,
            "transaction_date": movement.transaction_date.isoformat(),
            "description": movement.description,
            "reference": movement.reference,
            "amount": float(movement.amount),
            "status": movement.status,
            "reconciliation_type": reconciliation.reconciliation_type if reconciliation else None,
            "reconciliation_date": reconciliation.reconciliation_date.isoformat() if reconciliation else None
        })
    
    return {
        "detailed_movements": detailed_movements,
        "total_count": len(detailed_movements)
    }


async def _generate_adjustments_report(bank_account_id: int, empresa_id: int, 
                                     date_from: date, date_to: date, db: Session):
    """Generar reporte de ajustes automáticos"""
    # TODO: Implementar cuando esté disponible el sistema de ajustes
    return {
        "adjustments": [],
        "total_adjustments": 0,
        "total_amount": 0
    }


async def _generate_unmatched_report(bank_account_id: int, empresa_id: int, 
                                   date_from: date, date_to: date, db: Session):
    """Generar reporte de movimientos no conciliados"""
    query = db.query(BankMovement).filter(
        BankMovement.bank_account_id == bank_account_id,
        BankMovement.empresa_id == empresa_id,
        BankMovement.status == "PENDING"
    )
    
    if date_from:
        query = query.filter(BankMovement.transaction_date >= date_from)
    if date_to:
        query = query.filter(BankMovement.transaction_date <= date_to)
    
    movements = query.order_by(BankMovement.transaction_date.desc()).all()
    
    pending_movements = []
    for movement in movements:
        pending_movements.append({
            "id": movement.id,
            "transaction_date": movement.transaction_date.isoformat(),
            "description": movement.description,
            "reference": movement.reference,
            "amount": float(movement.amount)
        })
    
    return {
        "pending_movements": pending_movements,
        "total_pending": len(pending_movements),
        "total_amount": sum([float(m.amount) for m in movements])
    }


@router.get("/reports/export")
async def export_reconciliation_report(
    bank_account_id: int,
    report_type: str = "summary",
    format: str = "pdf",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Exportar reporte de conciliación"""
    try:
        from fastapi.responses import StreamingResponse
        import io
        
        # Generar datos del reporte
        
        date_from_obj = None
        date_to_obj = None
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
        if date_to:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
        
        # Obtener datos del reporte
        if report_type == "summary":
            report_data = await _generate_summary_report(
                bank_account_id, current_user.empresa_id, date_from_obj, date_to_obj, db
            )
        elif report_type == "detailed":
            report_data = await _generate_detailed_report(
                bank_account_id, current_user.empresa_id, date_from_obj, date_to_obj, db
            )
        else:
            raise HTTPException(status_code=400, detail="Tipo de reporte no soportado para exportación")
        
        if format == "excel":
            # Generar Excel
            output = io.BytesIO()
            
            # Usar pandas para crear Excel
            import pandas as pd
            
            if report_type == "summary":
                # Crear DataFrame con resumen
                summary_df = pd.DataFrame([report_data["summary"]])
                
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    summary_df.to_excel(writer, sheet_name='Resumen', index=False)
                    
                    if report_data.get("pending_movements"):
                        pending_df = pd.DataFrame(report_data["pending_movements"])
                        pending_df.to_excel(writer, sheet_name='Pendientes', index=False)
            
            elif report_type == "detailed":
                detailed_df = pd.DataFrame(report_data["detailed_movements"])
                
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    detailed_df.to_excel(writer, sheet_name='Detallado', index=False)
            
            output.seek(0)
            
            return StreamingResponse(
                io.BytesIO(output.read()),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=conciliacion_{report_type}_{date_from}_{date_to}.xlsx"}
            )
        
        elif format == "pdf":
            # Generar PDF mejorado
            output = await _generate_pdf_report(report_data, report_type, bank_account_id, date_from, date_to, db, current_user.empresa_id)
            
            return StreamingResponse(
                io.BytesIO(output.read()),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=conciliacion_{report_type}_{date_from}_{date_to}.pdf"}
            )
        
        else:
            raise HTTPException(status_code=400, detail="Formato de exportación no soportado")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exportando reporte: {str(e)}")


async def _generate_pdf_report(report_data: dict, report_type: str, bank_account_id: int, 
                             date_from: str, date_to: str, db: Session, empresa_id: int):
    """Generar PDF mejorado para reportes de conciliación"""
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    import io
    
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Obtener información de la empresa y cuenta
    from ...models.empresa import Empresa
    from ...models.plan_cuenta import PlanCuenta
    
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    cuenta = db.query(PlanCuenta).filter(PlanCuenta.id == bank_account_id).first()
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Centrado
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=20
    )
    
    # Contenido del documento
    story = []
    
    # Título principal
    story.append(Paragraph(f"REPORTE DE CONCILIACIÓN BANCARIA", title_style))
    story.append(Paragraph(f"{report_type.upper()}", subtitle_style))
    story.append(Spacer(1, 12))
    
    # Información de la empresa y cuenta
    info_data = [
        ['Empresa:', empresa.nombre if empresa else 'N/A'],
        ['Cuenta Bancaria:', f"{cuenta.codigo} - {cuenta.nombre}" if cuenta else 'N/A'],
        ['Período:', f"{date_from} - {date_to}"],
        ['Fecha de Generación:', datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 20))
    
    if report_type == "summary":
        # Reporte resumen
        summary = report_data["summary"]
        
        # Estadísticas principales
        story.append(Paragraph("ESTADÍSTICAS GENERALES", subtitle_style))
        
        stats_data = [
            ['Concepto', 'Valor'],
            ['Total de Movimientos', str(summary['total_movements'])],
            ['Movimientos Conciliados', str(summary['reconciled_movements'])],
            ['Movimientos Pendientes', str(summary['pending_movements'])],
            ['Tasa de Conciliación', f"{summary['reconciliation_rate']}%"],
            ['Monto Total', f"${summary['total_amount']:,.2f}"]
        ]
        
        stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 20))
        
        # Resumen por tipo
        if report_data.get("by_type"):
            story.append(Paragraph("RESUMEN POR TIPO DE CONCILIACIÓN", subtitle_style))
            
            type_data = [['Tipo', 'Cantidad', 'Porcentaje']]
            for item in report_data["by_type"]:
                type_name = "Automática" if item["type"] == "AUTO" else "Manual"
                type_data.append([type_name, str(item["count"]), f"{item['percentage']}%"])
            
            type_table = Table(type_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
            type_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(type_table)
            story.append(Spacer(1, 20))
        
        # Movimientos pendientes (primeros 10)
        if report_data.get("pending_movements"):
            story.append(Paragraph("MOVIMIENTOS PENDIENTES (Primeros 10)", subtitle_style))
            
            pending_data = [['Fecha', 'Descripción', 'Referencia', 'Monto']]
            for movement in report_data["pending_movements"][:10]:
                pending_data.append([
                    movement["transaction_date"],
                    movement["description"][:40] + "..." if len(movement["description"]) > 40 else movement["description"],
                    movement["reference"] or "-",
                    f"${movement['amount']:,.2f}"
                ])
            
            pending_table = Table(pending_data, colWidths=[1.2*inch, 2.5*inch, 1*inch, 1.3*inch])
            pending_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(pending_table)
    
    elif report_type == "detailed":
        # Reporte detallado
        story.append(Paragraph("REPORTE DETALLADO DE MOVIMIENTOS", subtitle_style))
        
        if report_data.get("detailed_movements"):
            # Dividir en páginas si hay muchos movimientos
            movements = report_data["detailed_movements"]
            page_size = 25
            
            for i in range(0, len(movements), page_size):
                page_movements = movements[i:i+page_size]
                
                detailed_data = [['Fecha', 'Descripción', 'Referencia', 'Monto', 'Estado', 'Tipo']]
                
                for movement in page_movements:
                    status_text = "Conciliado" if movement["status"] == "MATCHED" else "Pendiente"
                    type_text = "-"
                    if movement.get("reconciliation_type"):
                        type_text = "Auto" if movement["reconciliation_type"] == "AUTO" else "Manual"
                    
                    detailed_data.append([
                        movement["transaction_date"],
                        movement["description"][:30] + "..." if len(movement["description"]) > 30 else movement["description"],
                        movement["reference"][:15] + "..." if movement["reference"] and len(movement["reference"]) > 15 else (movement["reference"] or "-"),
                        f"${movement['amount']:,.2f}",
                        status_text,
                        type_text
                    ])
                
                detailed_table = Table(detailed_data, colWidths=[0.8*inch, 2*inch, 1*inch, 1*inch, 0.8*inch, 0.6*inch])
                detailed_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 7),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(detailed_table)
                
                if i + page_size < len(movements):
                    story.append(Spacer(1, 20))
    
    # Construir el documento
    doc.build(story)
    output.seek(0)
    
    return output


# ==================== INTERFAZ DE CONCILIACIÓN MANUAL ====================

@router.get("/manual-reconciliation/unmatched-movements")
async def get_unmatched_movements_for_manual_reconciliation(
    bank_account_id: int,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener movimientos no conciliados para interfaz manual"""
    try:
        from ...models.movimiento_contable import MovimientoContable
        from ...models.documento import Documento
        
        # Convertir fechas si se proporcionan
        date_from_obj = None
        date_to_obj = None
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
        
        if date_to:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
        
        # Obtener movimientos bancarios no conciliados
        bank_query = db.query(BankMovement).filter(
            BankMovement.bank_account_id == bank_account_id,
            BankMovement.empresa_id == current_user.empresa_id,
            BankMovement.status == "PENDING"
        )
        
        if date_from_obj:
            bank_query = bank_query.filter(BankMovement.transaction_date >= date_from_obj)
        if date_to_obj:
            bank_query = bank_query.filter(BankMovement.transaction_date <= date_to_obj)
        
        bank_movements = bank_query.order_by(
            BankMovement.transaction_date.desc()
        ).offset(offset).limit(limit).all()
        
        # Obtener movimientos contables no conciliados
        acc_query = db.query(MovimientoContable).join(Documento).filter(
            MovimientoContable.cuenta_id == bank_account_id,
            Documento.empresa_id == current_user.empresa_id,
            MovimientoContable.reconciliation_status == "UNRECONCILED"
        )
        
        if date_from_obj:
            acc_query = acc_query.filter(Documento.fecha >= date_from_obj)
        if date_to_obj:
            acc_query = acc_query.filter(Documento.fecha <= date_to_obj)
        
        accounting_movements = acc_query.order_by(
            Documento.fecha.desc()
        ).limit(100).all()  # Limitar a 100 para performance
        
        # Formatear movimientos bancarios
        formatted_bank_movements = []
        for bm in bank_movements:
            formatted_bank_movements.append({
                "id": bm.id,
                "transaction_date": bm.transaction_date.isoformat(),
                "value_date": bm.value_date.isoformat() if bm.value_date else None,
                "amount": float(bm.amount),
                "description": bm.description,
                "reference": bm.reference,
                "transaction_type": bm.transaction_type,
                "balance": float(bm.balance) if bm.balance else None,
                "status": bm.status
            })
        
        # Formatear movimientos contables
        formatted_accounting_movements = []
        for am in accounting_movements:
            formatted_accounting_movements.append({
                "id": am.id,
                "fecha": am.documento.fecha.isoformat(),
                "debito": float(am.debito),
                "credito": float(am.credito),
                "valor": float(am.debito - am.credito),
                "concepto": am.concepto or "",
                "referencia": getattr(am.documento, 'reconciliation_reference', '') or "",
                "documento_id": am.documento_id,
                "documento_numero": am.documento.numero,
                "documento_tipo": am.documento.tipo_documento.nombre if hasattr(am.documento, 'tipo_documento') and am.documento.tipo_documento else "N/A",
                "reconciliation_status": am.reconciliation_status
            })
        
        return {
            "bank_movements": formatted_bank_movements,
            "accounting_movements": formatted_accounting_movements,
            "total_bank_movements": bank_query.count(),
            "total_accounting_movements": acc_query.count(),
            "pagination": {
                "limit": limit,
                "offset": offset
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo movimientos: {str(e)}")


@router.post("/manual-reconciliation/match-preview")
async def preview_manual_match(
    bank_movement_id: int = Form(...),
    accounting_movement_ids: str = Form(...),  # IDs separados por coma
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Vista previa de una conciliación manual antes de aplicarla"""
    try:
        from ...models.movimiento_contable import MovimientoContable
        from ...models.documento import Documento
        
        # Obtener movimiento bancario
        bank_movement = db.query(BankMovement).filter(
            BankMovement.id == bank_movement_id,
            BankMovement.empresa_id == current_user.empresa_id,
            BankMovement.status == "PENDING"
        ).first()
        
        if not bank_movement:
            raise HTTPException(status_code=404, detail="Movimiento bancario no encontrado o ya conciliado")
        
        # Parsear y validar movimientos contables
        acc_movement_ids = [int(id.strip()) for id in accounting_movement_ids.split(",")]
        
        accounting_movements = db.query(MovimientoContable).join(Documento).filter(
            MovimientoContable.id.in_(acc_movement_ids),
            Documento.empresa_id == current_user.empresa_id,
            MovimientoContable.reconciliation_status == "UNRECONCILED"
        ).all()
        
        if len(accounting_movements) != len(acc_movement_ids):
            raise HTTPException(status_code=400, detail="Algunos movimientos contables no están disponibles")
        
        # Calcular totales
        total_accounting = sum(am.debito - am.credito for am in accounting_movements)
        bank_amount = bank_movement.amount
        difference = abs(bank_amount - abs(total_accounting))
        
        # Calcular score de confianza basado en diferencia
        confidence_score = 1.0 if difference < 0.01 else max(0.5, 1.0 - (difference / abs(bank_amount)))
        
        # Formatear respuesta
        return {
            "bank_movement": {
                "id": bank_movement.id,
                "transaction_date": bank_movement.transaction_date.isoformat(),
                "amount": float(bank_movement.amount),
                "description": bank_movement.description,
                "reference": bank_movement.reference
            },
            "accounting_movements": [
                {
                    "id": am.id,
                    "fecha": am.documento.fecha.isoformat(),
                    "debito": float(am.debito),
                    "credito": float(am.credito),
                    "valor": float(am.debito - am.credito),
                    "concepto": am.concepto,
                    "referencia": am.referencia,
                    "documento_numero": am.documento.numero
                } for am in accounting_movements
            ],
            "totals": {
                "bank_amount": float(bank_amount),
                "accounting_total": float(total_accounting),
                "difference": float(difference),
                "is_balanced": difference < 0.01
            },
            "confidence_score": confidence_score,
            "warnings": [] if difference < 0.01 else [
                f"Diferencia de ${difference:.2f} entre movimiento bancario y contable"
            ]
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Error en datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando vista previa: {str(e)}")


@router.get("/manual-reconciliation/movement-detail/{movement_id}")
async def get_movement_detail_for_reconciliation(
    movement_id: int,
    movement_type: str,  # "bank" o "accounting"
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener detalle completo de un movimiento para la interfaz de conciliación"""
    try:
        if movement_type == "bank":
            movement = db.query(BankMovement).filter(
                BankMovement.id == movement_id,
                BankMovement.empresa_id == current_user.empresa_id
            ).first()
            
            if not movement:
                raise HTTPException(status_code=404, detail="Movimiento bancario no encontrado")
            
            return {
                "type": "bank",
                "id": movement.id,
                "transaction_date": movement.transaction_date.isoformat(),
                "value_date": movement.value_date.isoformat() if movement.value_date else None,
                "amount": float(movement.amount),
                "description": movement.description,
                "reference": movement.reference,
                "transaction_type": movement.transaction_type,
                "balance": float(movement.balance) if movement.balance else None,
                "status": movement.status,
                "import_session_id": movement.import_session_id,
                "bank_account_id": movement.bank_account_id
            }
            
        elif movement_type == "accounting":
            from ...models.movimiento_contable import MovimientoContable
            from ...models.documento import Documento
            
            movement = db.query(MovimientoContable).join(Documento).filter(
                MovimientoContable.id == movement_id,
                Documento.empresa_id == current_user.empresa_id
            ).first()
            
            if not movement:
                raise HTTPException(status_code=404, detail="Movimiento contable no encontrado")
            
            return {
                "type": "accounting",
                "id": movement.id,
                "fecha": movement.documento.fecha.isoformat(),
                "debito": float(movement.debito),
                "credito": float(movement.credito),
                "valor": float(movement.debito - movement.credito),
                "concepto": movement.concepto,
                "referencia": movement.referencia,
                "documento_id": movement.documento_id,
                "documento_numero": movement.documento.numero,
                "documento_tipo": movement.documento.tipo_documento.nombre if movement.documento.tipo_documento else None,
                "cuenta_id": movement.cuenta_id,
                "cuenta_codigo": movement.cuenta.codigo if movement.cuenta else None,
                "cuenta_nombre": movement.cuenta.nombre if movement.cuenta else None,
                "reconciliation_status": movement.reconciliation_status
            }
        else:
            raise HTTPException(status_code=400, detail="Tipo de movimiento inválido")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo detalle: {str(e)}")


@router.get("/manual-reconciliation/search-accounting-movements")
async def search_accounting_movements_for_reconciliation(
    bank_account_id: int,
    query: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 20,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Buscar movimientos contables para conciliación manual"""
    try:
        from ...models.movimiento_contable import MovimientoContable
        from ...models.documento import Documento
        from sqlalchemy import or_
        
        # Convertir fechas si se proporcionan
        date_from_obj = None
        date_to_obj = None
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
        
        if date_to:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
        
        # Construir query base
        search_query = db.query(MovimientoContable).join(Documento).filter(
            MovimientoContable.cuenta_id == bank_account_id,
            Documento.empresa_id == current_user.empresa_id,
            MovimientoContable.reconciliation_status == "UNRECONCILED"
        )
        
        # Aplicar filtros de fecha
        if date_from_obj:
            search_query = search_query.filter(Documento.fecha >= date_from_obj)
        if date_to_obj:
            search_query = search_query.filter(Documento.fecha <= date_to_obj)
        
        # Aplicar filtro de búsqueda
        if query:
            search_terms = query.strip().split()
            for term in search_terms:
                search_query = search_query.filter(
                    or_(
                        MovimientoContable.concepto.ilike(f"%{term}%"),
                        MovimientoContable.referencia.ilike(f"%{term}%"),
                        Documento.numero.ilike(f"%{term}%")
                    )
                )
        
        # Ejecutar query
        movements = search_query.order_by(
            Documento.fecha.desc()
        ).limit(limit).all()
        
        # Formatear resultados
        results = []
        for am in movements:
            results.append({
                "id": am.id,
                "fecha": am.documento.fecha.isoformat(),
                "debito": float(am.debito),
                "credito": float(am.credito),
                "valor": float(am.debito - am.credito),
                "concepto": am.concepto,
                "referencia": am.referencia,
                "documento_id": am.documento_id,
                "documento_numero": am.documento.numero,
                "documento_tipo": am.documento.tipo_documento.nombre if am.documento.tipo_documento else None
            })
        
        return {
            "movements": results,
            "total_found": len(results),
            "query": query,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en búsqueda: {str(e)}")


@router.get("/manual-reconciliation/audit-trail/{reconciliation_id}")
async def get_reconciliation_audit_trail(
    reconciliation_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener historial de auditoría de una conciliación"""
    try:
        from ...models.conciliacion_bancaria import ReconciliationAudit
        
        # Verificar que la conciliación pertenece a la empresa del usuario
        reconciliation = db.query(Reconciliation).filter(
            Reconciliation.id == reconciliation_id,
            Reconciliation.empresa_id == current_user.empresa_id
        ).first()
        
        if not reconciliation:
            raise HTTPException(status_code=404, detail="Conciliación no encontrada")
        
        # Obtener registros de auditoría
        audit_records = db.query(ReconciliationAudit).filter(
            ReconciliationAudit.reconciliation_id == reconciliation_id
        ).order_by(ReconciliationAudit.operation_date.desc()).all()
        
        # Formatear respuesta
        audit_trail = []
        for record in audit_records:
            audit_trail.append({
                "id": record.id,
                "operation_type": record.operation_type,
                "operation_date": record.operation_date.isoformat(),
                "user_id": record.user_id,
                "old_values": record.old_values,
                "new_values": record.new_values,
                "notes": record.notes
            })
        
        return {
            "reconciliation_id": reconciliation_id,
            "audit_trail": audit_trail,
            "total_operations": len(audit_trail)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo auditoría: {str(e)}")


@router.post("/manual-reconciliation/bulk-operations")
async def bulk_reconciliation_operations(
    operation: str = Form(...),  # "match", "unmatch", "suggest"
    bank_movement_ids: str = Form(...),  # IDs separados por coma
    accounting_movement_ids: Optional[str] = Form(None),  # Para operación "match"
    notes: Optional[str] = Form(None),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Operaciones en lote para conciliación manual"""
    try:
        matching_engine = MatchingEngine(db)
        
        # Parsear IDs de movimientos bancarios
        bank_ids = [int(id.strip()) for id in bank_movement_ids.split(",")]
        
        results = []
        
        if operation == "match" and accounting_movement_ids:
            # Conciliación en lote
            acc_ids = [int(id.strip()) for id in accounting_movement_ids.split(",")]
            
            for bank_id in bank_ids:
                try:
                    result = matching_engine.apply_manual_match(
                        bank_id,
                        acc_ids,
                        current_user.empresa_id,
                        current_user.id,
                        notes
                    )
                    results.append({
                        "bank_movement_id": bank_id,
                        "success": True,
                        "reconciliation_id": result["reconciliation_id"]
                    })
                except Exception as e:
                    results.append({
                        "bank_movement_id": bank_id,
                        "success": False,
                        "error": str(e)
                    })
        
        elif operation == "suggest":
            # Generar sugerencias en lote
            for bank_id in bank_ids:
                try:
                    suggestions = matching_engine.suggest_matches(
                        bank_id,
                        current_user.empresa_id,
                        5
                    )
                    results.append({
                        "bank_movement_id": bank_id,
                        "success": True,
                        "suggestions_count": len(suggestions),
                        "best_suggestion": suggestions[0] if suggestions else None
                    })
                except Exception as e:
                    results.append({
                        "bank_movement_id": bank_id,
                        "success": False,
                        "error": str(e)
                    })
        
        else:
            raise HTTPException(status_code=400, detail="Operación no válida o parámetros faltantes")
        
        # Calcular estadísticas
        successful_operations = sum(1 for r in results if r["success"])
        failed_operations = len(results) - successful_operations
        
        return {
            "operation": operation,
            "total_processed": len(results),
            "successful": successful_operations,
            "failed": failed_operations,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en operación en lote: {str(e)}")


# ==================== GENERACIÓN AUTOMÁTICA DE AJUSTES ====================

@router.get("/adjustments/preview/{bank_account_id}")
async def preview_automatic_adjustments(
    bank_account_id: int,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: Usuario = Depends(has_permission("conciliacion_bancaria:ajustar")),
    db: Session = Depends(get_db)
):
    """Generar vista previa de ajustes automáticos"""
    try:
        from ...services.conciliacion_bancaria import AdjustmentEngine
        
        adjustment_engine = AdjustmentEngine(db)
        
        # Convertir fechas si se proporcionan
        date_from_obj = None
        date_to_obj = None
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
        
        if date_to:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
        
        preview = adjustment_engine.preview_adjustments(
            bank_account_id,
            current_user.empresa_id,
            date_from_obj,
            date_to_obj
        )
        
        return {
            "status": "success",
            "data": preview
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando vista previa de ajustes: {str(e)}")


@router.post("/adjustments/apply")
async def apply_automatic_adjustments(
    bank_movement_ids: str = Form(...),  # IDs separados por coma
    notes: Optional[str] = Form(None),
    current_user: Usuario = Depends(has_permission("conciliacion_bancaria:ajustar")),
    db: Session = Depends(get_db)
):
    """Aplicar ajustes automáticos seleccionados"""
    try:
        from ...services.conciliacion_bancaria import AdjustmentEngine
        
        adjustment_engine = AdjustmentEngine(db)
        
        # Parsear IDs de movimientos bancarios
        movement_ids = [int(id.strip()) for id in bank_movement_ids.split(",")]
        
        result = adjustment_engine.apply_adjustments(
            movement_ids,
            current_user.id,
            current_user.empresa_id,
            notes
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error aplicando ajustes: {str(e)}")


@router.get("/adjustments/detect/{bank_account_id}")
async def detect_adjustments_for_account(
    bank_account_id: int,
    limit: int = 50,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Detectar movimientos que requieren ajustes automáticos"""
    try:
        from ...services.conciliacion_bancaria import AdjustmentEngine
        
        adjustment_engine = AdjustmentEngine(db)
        
        # Obtener movimientos bancarios pendientes
        bank_movements = db.query(BankMovement).filter(
            BankMovement.bank_account_id == bank_account_id,
            BankMovement.empresa_id == current_user.empresa_id,
            BankMovement.status == "PENDING"
        ).limit(limit).all()
        
        # Detectar ajustes
        adjustments = adjustment_engine.detect_adjustments(
            bank_movements,
            bank_account_id,
            current_user.empresa_id
        )
        
        return {
            "bank_account_id": bank_account_id,
            "total_movements_analyzed": len(bank_movements),
            "adjustments_detected": len(adjustments),
            "adjustments": adjustments
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detectando ajustes: {str(e)}")


@router.get("/adjustments/types")
async def get_adjustment_types():
    """Obtener tipos de ajustes disponibles"""
    return {
        "adjustment_types": [
            {
                "code": "COMMISSION",
                "name": "Comisión bancaria",
                "description": "Comisiones cobradas por el banco",
                "account_type": "expense"
            },
            {
                "code": "INTEREST",
                "name": "Interés ganado",
                "description": "Intereses pagados por el banco",
                "account_type": "income"
            },
            {
                "code": "DEBIT_NOTE",
                "name": "Nota débito",
                "description": "Cargos automáticos del banco",
                "account_type": "expense"
            },
            {
                "code": "CREDIT_NOTE",
                "name": "Nota crédito",
                "description": "Abonos automáticos del banco",
                "account_type": "income"
            }
        ]
    }


@router.post("/adjustments/preview-single")
async def preview_single_adjustment(
    bank_movement_id: int = Form(...),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Vista previa de un ajuste específico"""
    try:
        from ...services.conciliacion_bancaria import AdjustmentEngine
        
        adjustment_engine = AdjustmentEngine(db)
        
        # Obtener movimiento bancario
        bank_movement = db.query(BankMovement).filter(
            BankMovement.id == bank_movement_id,
            BankMovement.empresa_id == current_user.empresa_id
        ).first()
        
        if not bank_movement:
            raise HTTPException(status_code=404, detail="Movimiento bancario no encontrado")
        
        # Detectar ajustes para este movimiento
        adjustments = adjustment_engine.detect_adjustments(
            [bank_movement],
            bank_movement.bank_account_id,
            current_user.empresa_id
        )
        
        if not adjustments:
            return {
                "bank_movement_id": bank_movement_id,
                "adjustment_detected": False,
                "message": "No se detectó ningún ajuste automático para este movimiento"
            }
        
        return {
            "bank_movement_id": bank_movement_id,
            "adjustment_detected": True,
            "adjustment": adjustments[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando vista previa: {str(e)}")


@router.get("/adjustments/history")
async def get_adjustments_history(
    bank_account_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener historial de ajustes aplicados"""
    try:
        
        # Obtener movimientos bancarios que han sido ajustados
        query = db.query(BankMovement).filter(
            BankMovement.empresa_id == current_user.empresa_id,
            BankMovement.status == "ADJUSTED"
        )
        
        if bank_account_id:
            query = query.filter(BankMovement.bank_account_id == bank_account_id)
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
            query = query.filter(BankMovement.transaction_date >= date_from_obj)
        
        if date_to:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
            query = query.filter(BankMovement.transaction_date <= date_to_obj)
        
        total = query.count()
        movements = query.order_by(
            BankMovement.transaction_date.desc()
        ).offset(offset).limit(limit).all()
        
        # Formatear respuesta
        adjustments_history = []
        for movement in movements:
            adjustments_history.append({
                "id": movement.id,
                "transaction_date": movement.transaction_date.isoformat(),
                "amount": float(movement.amount),
                "description": movement.description,
                "reference": movement.reference,
                "bank_account_id": movement.bank_account_id,
                "status": movement.status,
                "created_at": movement.created_at.isoformat()
            })
        
        return {
            "adjustments": adjustments_history,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo historial: {str(e)}")


# ==================== SISTEMA DE SEGURIDAD Y AUDITORÍA ====================

@router.get("/audit/trail")
async def get_audit_trail(
    reconciliation_id: Optional[int] = None,
    operation_type: Optional[str] = None,
    user_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 100,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener historial completo de auditoría"""
    try:
        audit_service = AuditService(db)
        
        # Convertir fechas si se proporcionan
        date_from_obj = None
        date_to_obj = None
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
        
        if date_to:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
        
        trail = audit_service.get_audit_trail(
            empresa_id=current_user.empresa_id,
            reconciliation_id=reconciliation_id,
            operation_type=operation_type,
            user_id=user_id,
            date_from=date_from_obj,
            date_to=date_to_obj,
            limit=limit
        )
        
        return {
            "audit_trail": trail,
            "total": len(trail),
            "filters": {
                "reconciliation_id": reconciliation_id,
                "operation_type": operation_type,
                "user_id": user_id,
                "date_from": date_from,
                "date_to": date_to
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo historial de auditoría: {str(e)}")


@router.get("/audit/user-activity/{user_id}")
async def get_user_activity(
    user_id: int,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas de actividad de un usuario"""
    try:
        audit_service = AuditService(db)
        
        # Convertir fechas si se proporcionan
        date_from_obj = None
        date_to_obj = None
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
        
        if date_to:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
        
        activity = audit_service.get_user_activity(
            user_id=user_id,
            empresa_id=current_user.empresa_id,
            date_from=date_from_obj,
            date_to=date_to_obj
        )
        
        return activity
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo actividad de usuario: {str(e)}")


@router.post("/security/report-suspicious")
async def report_suspicious_activity(
    activity_type: str = Form(...),
    details: str = Form(...),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reportar actividad sospechosa"""
    try:
        security_service = SecurityService(db)
        
        security_service.log_suspicious_activity(
            user_id=current_user.id,
            empresa_id=current_user.empresa_id,
            activity_type=activity_type,
            details=details
        )
        
        return {
            "message": "Actividad sospechosa reportada exitosamente",
            "activity_type": activity_type,
            "reported_by": current_user.id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reportando actividad: {str(e)}")


@router.get("/security/validate-access/{resource_type}/{resource_id}")
async def validate_resource_access(
    resource_type: str,  # "bank_account", "reconciliation", "import_session"
    resource_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validar acceso a un recurso específico"""
    try:
        security_service = SecurityService(db)
        
        has_access = False
        
        if resource_type == "bank_account":
            has_access = security_service.validate_bank_account_access(
                current_user.id, current_user.empresa_id, resource_id
            )
        elif resource_type == "reconciliation":
            has_access = security_service.validate_reconciliation_access(
                current_user.id, current_user.empresa_id, resource_id
            )
        elif resource_type == "import_session":
            has_access = security_service.validate_import_session_access(
                current_user.id, current_user.empresa_id, str(resource_id)
            )
        else:
            raise HTTPException(status_code=400, detail="Tipo de recurso no válido")
        
        return {
            "has_access": has_access,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "user_id": current_user.id,
            "empresa_id": current_user.empresa_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validando acceso: {str(e)}")


@router.get("/security/rate-limit-status/{operation_type}")
async def get_rate_limit_status(
    operation_type: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verificar estado de límite de tasa para un tipo de operación"""
    try:
        security_service = SecurityService(db)
        
        # Definir límites según el tipo de operación
        limits = {
            "MANUAL_RECONCILIATION": {"window": 60, "max": 50},
            "AUTO_RECONCILIATION": {"window": 30, "max": 10},
            "FILE_IMPORT": {"window": 60, "max": 20},
            "CONFIG_UPDATE": {"window": 60, "max": 25}
        }
        
        if operation_type not in limits:
            raise HTTPException(status_code=400, detail="Tipo de operación no válido")
        
        limit_config = limits[operation_type]
        can_proceed = security_service.check_rate_limit(
            user_id=current_user.id,
            operation_type=operation_type,
            time_window_minutes=limit_config["window"],
            max_operations=limit_config["max"]
        )
        
        # Contar operaciones actuales en la ventana de tiempo
        time_threshold = datetime.utcnow() - timedelta(minutes=limit_config["window"])
        current_count = db.query(ReconciliationAudit).filter(
            ReconciliationAudit.user_id == current_user.id,
            ReconciliationAudit.operation_type == operation_type,
            ReconciliationAudit.operation_date >= time_threshold
        ).count()
        
        return {
            "can_proceed": can_proceed,
            "operation_type": operation_type,
            "current_count": current_count,
            "max_allowed": limit_config["max"],
            "time_window_minutes": limit_config["window"],
            "remaining": max(0, limit_config["max"] - current_count),
            "reset_time": (datetime.utcnow() + timedelta(minutes=limit_config["window"])).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verificando límite de tasa: {str(e)}")


# ==================== ENDPOINTS DE WEBSOCKET PARA TIEMPO REAL ====================

@router.get("/websocket/reconciliation-progress/{session_id}")
async def get_reconciliation_progress(
    session_id: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener progreso de conciliación en tiempo real"""
    try:
        # Validar acceso a la sesión
        security_service = SecurityService(db)
        if not security_service.validate_import_session_access(current_user.id, current_user.empresa_id, session_id):
            raise HTTPException(status_code=403, detail="Acceso denegado a la sesión")
        
        # Obtener estado actual de la sesión
        session = db.query(ImportSession).filter(
            ImportSession.id == session_id,
            ImportSession.empresa_id == current_user.empresa_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
        # Obtener estadísticas de conciliación
        total_movements = db.query(BankMovement).filter(
            BankMovement.import_session_id == session_id
        ).count()
        
        matched_movements = db.query(BankMovement).filter(
            BankMovement.import_session_id == session_id,
            BankMovement.status == "MATCHED"
        ).count()
        
        pending_movements = total_movements - matched_movements
        progress_percentage = (matched_movements / total_movements * 100) if total_movements > 0 else 0
        
        return {
            "session_id": session_id,
            "status": session.status,
            "total_movements": total_movements,
            "matched_movements": matched_movements,
            "pending_movements": pending_movements,
            "progress_percentage": round(progress_percentage, 2),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo progreso: {str(e)}")


# ==================== ENDPOINTS DE UTILIDADES ====================

@router.get("/health")
async def health_check():
    """Verificar estado de salud del módulo"""
    return {
        "status": "healthy",
        "module": "conciliacion-bancaria",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@router.get("/stats/summary")
async def get_module_stats(
    current_user: Usuario = Depends(has_permission("conciliacion_bancaria:auditoria")),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas generales del módulo"""
    try:
        # Estadísticas de importaciones
        total_imports = db.query(ImportSession).filter(
            ImportSession.empresa_id == current_user.empresa_id
        ).count()
        
        successful_imports = db.query(ImportSession).filter(
            ImportSession.empresa_id == current_user.empresa_id,
            ImportSession.status == "COMPLETED"
        ).count()
        
        # Estadísticas de movimientos
        total_movements = db.query(BankMovement).filter(
            BankMovement.empresa_id == current_user.empresa_id
        ).count()
        
        matched_movements = db.query(BankMovement).filter(
            BankMovement.empresa_id == current_user.empresa_id,
            BankMovement.status == "MATCHED"
        ).count()
        
        # Estadísticas de conciliaciones
        total_reconciliations = db.query(Reconciliation).filter(
            Reconciliation.empresa_id == current_user.empresa_id
        ).count()
        
        active_reconciliations = db.query(Reconciliation).filter(
            Reconciliation.empresa_id == current_user.empresa_id,
            Reconciliation.status == "ACTIVE"
        ).count()
        
        # Estadísticas de configuraciones
        total_configs = db.query(ImportConfig).filter(
            ImportConfig.empresa_id == current_user.empresa_id,
            ImportConfig.is_active == True
        ).count()
        
        return {
            "imports": {
                "total": total_imports,
                "successful": successful_imports,
                "success_rate": round((successful_imports / total_imports * 100) if total_imports > 0 else 0, 2)
            },
            "movements": {
                "total": total_movements,
                "matched": matched_movements,
                "pending": total_movements - matched_movements,
                "match_rate": round((matched_movements / total_movements * 100) if total_movements > 0 else 0, 2)
            },
            "reconciliations": {
                "total": total_reconciliations,
                "active": active_reconciliations,
                "reversed": total_reconciliations - active_reconciliations
            },
            "configurations": {
                "total": total_configs
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")


# ==================== ENDPOINTS DE MONITOREO Y RENDIMIENTO ====================

@router.get("/monitoring/performance")
async def get_performance_metrics(
    current_user: Usuario = Depends(has_permission("conciliacion_bancaria:auditoria")),
    db: Session = Depends(get_db)
):
    """Obtener métricas de rendimiento del módulo"""
    try:
        from ...core.monitoring import performance_monitor, BankReconciliationMonitor
        
        # Obtener métricas generales
        general_stats = performance_monitor.get_operation_stats()
        
        # Obtener métricas específicas de conciliación
        reconciliation_metrics = BankReconciliationMonitor.get_reconciliation_metrics()
        
        # Obtener operaciones lentas
        slow_operations = performance_monitor.get_slow_operations(threshold_ms=2000)
        
        return {
            "status": "success",
            "data": {
                "general_statistics": general_stats,
                "reconciliation_metrics": reconciliation_metrics,
                "slow_operations": [
                    {
                        "operation": op.operation,
                        "duration_ms": op.duration_ms,
                        "timestamp": op.timestamp.isoformat(),
                        "success": op.success
                    }
                    for op in slow_operations[-10:]  # Últimas 10 operaciones lentas
                ],
                "performance_summary": {
                    "total_operations": sum(stats['count'] for stats in general_stats.values()),
                    "avg_response_time": sum(stats['avg_duration'] for stats in general_stats.values()) / max(1, len(general_stats)),
                    "success_rate": (
                        sum(stats['success_count'] for stats in general_stats.values()) /
                        max(1, sum(stats['count'] for stats in general_stats.values()))
                    ) * 100
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo métricas: {str(e)}")


@router.get("/monitoring/health")
async def get_system_health(
    current_user: Usuario = Depends(has_permission("conciliacion_bancaria:auditoria")),
    db: Session = Depends(get_db)
):
    """Obtener estado de salud del sistema"""
    try:
        from ...core.monitoring import alert_manager
        from ...core.cache import get_cache_health
        
        # Obtener estado general de salud
        health_status = alert_manager.get_system_health()
        
        # Verificar conectividad de base de datos
        try:
            db.execute("SELECT 1")
            db_status = "healthy"
        except Exception as e:
            db_status = "unhealthy"
            health_status['database_error'] = str(e)
        
        health_status['database'] = {
            'status': db_status,
            'connection_pool_size': db.bind.pool.size() if hasattr(db.bind, 'pool') else 'unknown'
        }
        
        return {
            "status": "success",
            "data": health_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado de salud: {str(e)}")


@router.get("/monitoring/cache-stats")
async def get_cache_statistics(
    current_user: Usuario = Depends(has_permission("conciliacion_bancaria:auditoria")),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas del sistema de caché"""
    try:
        from ...core.cache import cache, get_cache_health
        
        cache_stats = cache.get_stats()
        cache_health = get_cache_health()
        
        return {
            "status": "success",
            "data": {
                "cache_statistics": cache_stats,
                "cache_health": cache_health,
                "recommendations": cache_health.get('recommendations', [])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas de caché: {str(e)}")


@router.post("/monitoring/cache/clear")
async def clear_cache(
    cache_pattern: Optional[str] = None,
    current_user: Usuario = Depends(has_permission("conciliacion_bancaria:configurar")),
    db: Session = Depends(get_db)
):
    """Limpiar caché del sistema"""
    try:
        from ...core.cache import cache, invalidate_cache_pattern
        
        if cache_pattern:
            cleared_count = invalidate_cache_pattern(cache_pattern)
            message = f"Se limpiaron {cleared_count} entradas que coinciden con el patrón '{cache_pattern}'"
        else:
            cache.clear()
            message = "Se limpió todo el caché del sistema"
        
        return {
            "status": "success",
            "message": message
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error limpiando caché: {str(e)}")


@router.get("/monitoring/alerts")
async def get_system_alerts(
    current_user: Usuario = Depends(has_permission("conciliacion_bancaria:auditoria")),
    db: Session = Depends(get_db)
):
    """Obtener alertas activas del sistema"""
    try:
        from ...core.monitoring import alert_manager
        
        alerts = alert_manager.check_performance_alerts()
        
        return {
            "status": "success",
            "data": {
                "active_alerts": alerts,
                "alert_count": len(alerts),
                "critical_alerts": [alert for alert in alerts if alert.get('severity') == 'critical'],
                "warning_alerts": [alert for alert in alerts if alert.get('severity') == 'warning']
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo alertas: {str(e)}")


@router.get("/monitoring/database-performance")
async def get_database_performance(
    current_user: Usuario = Depends(has_permission("conciliacion_bancaria:auditoria")),
    db: Session = Depends(get_db)
):
    """Obtener métricas de rendimiento de la base de datos"""
    try:
        # Consultas para obtener estadísticas de rendimiento
        performance_queries = {
            "table_sizes": """
                SELECT 
                    table_name,
                    table_rows,
                    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name IN ('bank_movements', 'reconciliations', 'import_sessions')
                ORDER BY size_mb DESC
            """,
            "recent_activity": """
                SELECT 
                    COUNT(*) as total_bank_movements,
                    COUNT(CASE WHEN status = 'MATCHED' THEN 1 END) as matched_movements,
                    COUNT(CASE WHEN status = 'PENDING' THEN 1 END) as pending_movements,
                    COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR) THEN 1 END) as movements_last_24h
                FROM bank_movements 
                WHERE empresa_id = :empresa_id
            """
        }
        
        results = {}
        
        # Ejecutar consultas de rendimiento
        for query_name, query_sql in performance_queries.items():
            try:
                if query_name == "recent_activity":
                    result = db.execute(query_sql, {"empresa_id": current_user.empresa_id}).fetchall()
                else:
                    result = db.execute(query_sql).fetchall()
                
                results[query_name] = [dict(row) for row in result]
            except Exception as e:
                results[query_name] = f"Error: {str(e)}"
        
        return {
            "status": "success",
            "data": {
                "database_performance": results,
                "empresa_id": current_user.empresa_id,
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo rendimiento de BD: {str(e)}")

# ==================== ENDPOINT DE PRUEBA ====================

@router.get("/test/adjustments-preview/{bank_account_id}")
async def test_adjustments_preview(
    bank_account_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Endpoint de prueba para vista previa de ajustes"""
    try:
        # Verificar que la cuenta bancaria existe
        from ...models.plan_cuenta import PlanCuenta
        bank_account = db.query(PlanCuenta).filter(
            PlanCuenta.id == bank_account_id,
            PlanCuenta.empresa_id == current_user.empresa_id
        ).first()
        
        if not bank_account:
            return {
                "status": "error",
                "message": "Cuenta bancaria no encontrada",
                "data": None
            }
        
        # Contar movimientos bancarios
        from ...models.conciliacion_bancaria import BankMovement
        movements_count = db.query(BankMovement).filter(
            BankMovement.bank_account_id == bank_account_id,
            BankMovement.empresa_id == current_user.empresa_id
        ).count()
        
        return {
            "status": "success",
            "message": "Endpoint funcionando correctamente",
            "data": {
                "bank_account_id": bank_account_id,
                "bank_account_name": bank_account.nombre,
                "movements_count": movements_count,
                "empresa_id": current_user.empresa_id,
                "user_id": current_user.id
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error en endpoint de prueba: {str(e)}",
            "data": None
        }