import os
import csv
import hashlib
import uuid
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal, InvalidOperation
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import difflib
import time
from ..core.cache import cached, BankReconciliationCache, cache
from ..core.monitoring import monitor_performance, BankReconciliationMonitor, log_performance_warning

from ..models.conciliacion_bancaria import (
    ImportConfig, ImportSession, BankMovement, AccountingConfig,
    Reconciliation, ReconciliationMovement, ReconciliationAudit
)
from ..schemas.conciliacion_bancaria import (
    FileValidationResult, ImportSessionCreate, BankMovementCreate, DuplicateReport
)
from ..core.database import get_db


class AuditService:
    """Servicio de auditoría para operaciones de conciliación bancaria"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_operation(self, operation_type: str, user_id: int, empresa_id: int,
                     reconciliation_id: int = None, old_values: dict = None, 
                     new_values: dict = None, ip_address: str = None, 
                     user_agent: str = None):
        """Registra una operación en el log de auditoría"""
        try:
            audit_record = ReconciliationAudit(
                reconciliation_id=reconciliation_id,
                empresa_id=empresa_id,
                operation_type=operation_type,
                user_id=user_id,
                operation_date=datetime.utcnow(),
                old_values=old_values,
                new_values=new_values,
                ip_address=ip_address,
                user_agent=user_agent
            )
            self.db.add(audit_record)
            self.db.commit()
            return audit_record.id
        except Exception as e:
            print(f"Error logging audit operation: {str(e)}")
            return None
    
    def get_audit_trail(self, empresa_id: int, reconciliation_id: int = None, 
                       operation_type: str = None, user_id: int = None,
                       date_from: date = None, date_to: date = None,
                       limit: int = 100) -> List[Dict[str, Any]]:
        """Obtiene el historial de auditoría con filtros"""
        try:
            query = self.db.query(ReconciliationAudit).filter(
                ReconciliationAudit.empresa_id == empresa_id
            )
            
            if reconciliation_id:
                query = query.filter(ReconciliationAudit.reconciliation_id == reconciliation_id)
            
            if operation_type:
                query = query.filter(ReconciliationAudit.operation_type == operation_type)
            
            if user_id:
                query = query.filter(ReconciliationAudit.user_id == user_id)
            
            if date_from:
                query = query.filter(ReconciliationAudit.operation_date >= date_from)
            
            if date_to:
                query = query.filter(ReconciliationAudit.operation_date <= date_to)
            
            records = query.order_by(ReconciliationAudit.operation_date.desc()).limit(limit).all()
            
            trail = []
            for record in records:
                trail.append({
                    "id": record.id,
                    "reconciliation_id": record.reconciliation_id,
                    "operation_type": record.operation_type,
                    "operation_date": record.operation_date.isoformat(),
                    "user_id": record.user_id,
                    "old_values": record.old_values,
                    "new_values": record.new_values,
                    "ip_address": record.ip_address,
                    "user_agent": record.user_agent
                })
            
            return trail
        except Exception as e:
            print(f"Error getting audit trail: {str(e)}")
            return []
    
    def get_user_activity(self, user_id: int, empresa_id: int, 
                         date_from: date = None, date_to: date = None) -> Dict[str, Any]:
        """Obtiene estadísticas de actividad de un usuario"""
        try:
            query = self.db.query(ReconciliationAudit).filter(
                ReconciliationAudit.user_id == user_id,
                ReconciliationAudit.empresa_id == empresa_id
            )
            
            if date_from:
                query = query.filter(ReconciliationAudit.operation_date >= date_from)
            
            if date_to:
                query = query.filter(ReconciliationAudit.operation_date <= date_to)
            
            records = query.all()
            
            activity = {
                "total_operations": len(records),
                "operations_by_type": {},
                "operations_by_date": {},
                "last_activity": None
            }
            
            for record in records:
                # Contar por tipo
                op_type = record.operation_type
                activity["operations_by_type"][op_type] = activity["operations_by_type"].get(op_type, 0) + 1
                
                # Contar por fecha
                op_date = record.operation_date.date().isoformat()
                activity["operations_by_date"][op_date] = activity["operations_by_date"].get(op_date, 0) + 1
                
                # Última actividad
                if not activity["last_activity"] or record.operation_date > datetime.fromisoformat(activity["last_activity"]):
                    activity["last_activity"] = record.operation_date.isoformat()
            
            return activity
        except Exception as e:
            print(f"Error getting user activity: {str(e)}")
            return {"total_operations": 0, "operations_by_type": {}, "operations_by_date": {}, "last_activity": None}


class SecurityService:
    """Servicio de seguridad para validación de acceso y permisos"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_bank_account_access(self, user_id: int, empresa_id: int, bank_account_id: int) -> bool:
        """Valida que el usuario tenga acceso a la cuenta bancaria"""
        try:
            from ..models.plan_cuenta import PlanCuenta
            
            account = self.db.query(PlanCuenta).filter(
                PlanCuenta.id == bank_account_id,
                PlanCuenta.empresa_id == empresa_id
            ).first()
            
            return account is not None
        except Exception as e:
            print(f"Error validating bank account access: {str(e)}")
            return False
    
    def validate_reconciliation_access(self, user_id: int, empresa_id: int, reconciliation_id: int) -> bool:
        """Valida que el usuario tenga acceso a la conciliación"""
        try:
            reconciliation = self.db.query(Reconciliation).filter(
                Reconciliation.id == reconciliation_id,
                Reconciliation.empresa_id == empresa_id
            ).first()
            
            return reconciliation is not None
        except Exception as e:
            print(f"Error validating reconciliation access: {str(e)}")
            return False
    
    def validate_import_session_access(self, user_id: int, empresa_id: int, session_id: str) -> bool:
        """Valida que el usuario tenga acceso a la sesión de importación"""
        try:
            session = self.db.query(ImportSession).filter(
                ImportSession.id == session_id,
                ImportSession.empresa_id == empresa_id
            ).first()
            
            return session is not None
        except Exception as e:
            print(f"Error validating import session access: {str(e)}")
            return False
    
    def log_suspicious_activity(self, user_id: int, empresa_id: int, activity_type: str, 
                              details: str, ip_address: str = None, user_agent: str = None):
        """Registra actividad sospechosa"""
        try:
            audit_service = AuditService(self.db)
            audit_service.log_operation(
                operation_type=f"SUSPICIOUS_{activity_type}",
                user_id=user_id,
                empresa_id=empresa_id,
                new_values={"details": details, "severity": "WARNING"},
                ip_address=ip_address,
                user_agent=user_agent
            )
        except Exception as e:
            print(f"Error logging suspicious activity: {str(e)}")
    
    def check_rate_limit(self, user_id: int, operation_type: str, time_window_minutes: int = 60, 
                        max_operations: int = 100) -> bool:
        """Verifica límites de tasa de operaciones"""
        try:
            time_threshold = datetime.utcnow() - timedelta(minutes=time_window_minutes)
            
            count = self.db.query(ReconciliationAudit).filter(
                ReconciliationAudit.user_id == user_id,
                ReconciliationAudit.operation_type == operation_type,
                ReconciliationAudit.operation_date >= time_threshold
            ).count()
            
            return count < max_operations
        except Exception as e:
            print(f"Error checking rate limit: {str(e)}")
            return True  # En caso de error, permitir la operación


class ImportEngine:
    """Motor de importación de extractos bancarios"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_file(self, file_path: str, config_id: int) -> FileValidationResult:
        """Valida un archivo de extracto bancario según la configuración"""
        try:
            # Obtener configuración
            config = self.db.query(ImportConfig).filter(ImportConfig.id == config_id).first()
            if not config:
                return FileValidationResult(
                    is_valid=False,
                    errors=["Configuración de importación no encontrada"]
                )
            
            # Verificar que el archivo existe
            if not os.path.exists(file_path):
                return FileValidationResult(
                    is_valid=False,
                    errors=["Archivo no encontrado"]
                )
            
            # Validar formato de archivo
            file_extension = os.path.splitext(file_path)[1].upper()
            if config.file_format.upper() not in file_extension:
                return FileValidationResult(
                    is_valid=False,
                    errors=[f"Formato de archivo incorrecto. Esperado: {config.file_format}, Encontrado: {file_extension}"]
                )
            
            errors = []
            warnings = []
            sample_data = []
            total_rows = 0
            
            # Validar contenido según el formato
            if config.file_format.upper() in ['CSV', 'TXT']:
                result = self._validate_csv_file(file_path, config)
            elif config.file_format.upper() in ['XLS', 'XLSX']:
                result = self._validate_excel_file(file_path, config)
            else:
                return FileValidationResult(
                    is_valid=False,
                    errors=[f"Formato de archivo no soportado: {config.file_format}"]
                )
            
            return result
            
        except Exception as e:
            return FileValidationResult(
                is_valid=False,
                errors=[f"Error validando archivo: {str(e)}"]
            )
    
    def _validate_csv_file(self, file_path: str, config: ImportConfig) -> FileValidationResult:
        """Valida archivo CSV/TXT"""
        errors = []
        warnings = []
        sample_data = []
        total_rows = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                # Saltar filas de encabezado
                for _ in range(config.header_rows):
                    next(file, None)
                
                reader = csv.reader(file, delimiter=config.delimiter)
                
                for row_num, row in enumerate(reader, start=config.header_rows + 1):
                    total_rows += 1
                    
                    # Validar que la fila tenga suficientes columnas
                    required_columns = max(config.field_mapping.values()) + 1
                    if len(row) < required_columns:
                        errors.append(f"Fila {row_num}: Insuficientes columnas. Esperadas: {required_columns}, Encontradas: {len(row)}")
                        continue
                    
                    # Validar campos obligatorios
                    row_errors = self._validate_row_data(row, config, row_num)
                    errors.extend(row_errors)
                    
                    # Agregar muestra de datos (primeras 5 filas válidas)
                    if len(sample_data) < 5 and not row_errors:
                        sample_data.append(self._extract_row_data(row, config))
                    
                    # Limitar validación para archivos muy grandes
                    if total_rows > 10000:
                        warnings.append("Archivo muy grande. Validación limitada a las primeras 10,000 filas.")
                        break
        
        except UnicodeDecodeError:
            errors.append("Error de codificación. Intente con codificación UTF-8.")
        except Exception as e:
            errors.append(f"Error leyendo archivo CSV: {str(e)}")
        
        return FileValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            total_rows=total_rows,
            sample_data=sample_data
        )
    
    def _validate_excel_file(self, file_path: str, config: ImportConfig) -> FileValidationResult:
        """Valida archivo Excel"""
        errors = []
        warnings = []
        sample_data = []
        
        try:
            # Leer archivo Excel
            df = pd.read_excel(file_path, skiprows=config.header_rows)
            total_rows = len(df)
            
            # Validar que tenga suficientes columnas
            required_columns = max(config.field_mapping.values()) + 1
            if len(df.columns) < required_columns:
                errors.append(f"Insuficientes columnas. Esperadas: {required_columns}, Encontradas: {len(df.columns)}")
                return FileValidationResult(
                    is_valid=False,
                    errors=errors,
                    total_rows=total_rows
                )
            
            # Validar cada fila
            for index, row in df.iterrows():
                row_num = index + config.header_rows + 2  # +2 porque Excel empieza en 1 y saltamos headers
                row_list = row.tolist()
                
                row_errors = self._validate_row_data(row_list, config, row_num)
                errors.extend(row_errors)
                
                # Agregar muestra de datos
                if len(sample_data) < 5 and not row_errors:
                    sample_data.append(self._extract_row_data(row_list, config))
        
        except Exception as e:
            errors.append(f"Error leyendo archivo Excel: {str(e)}")
        
        return FileValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            total_rows=total_rows,
            sample_data=sample_data
        )
    
    def _validate_row_data(self, row: List[str], config: ImportConfig, row_num: int) -> List[str]:
        """Valida los datos de una fila"""
        errors = []
        
        try:
            # Validar fecha
            if 'date' in config.field_mapping:
                date_col = config.field_mapping['date']
                if date_col < len(row):
                    try:
                        datetime.strptime(str(row[date_col]).strip(), config.date_format)
                    except ValueError:
                        errors.append(f"Fila {row_num}: Formato de fecha inválido en columna {date_col + 1}")
            
            # Validar monto
            if 'amount' in config.field_mapping:
                amount_col = config.field_mapping['amount']
                if amount_col < len(row):
                    try:
                        amount_str = str(row[amount_col]).strip().replace(',', '')
                        Decimal(amount_str)
                    except (InvalidOperation, ValueError):
                        errors.append(f"Fila {row_num}: Formato de monto inválido en columna {amount_col + 1}")
            
            # Validar descripción (no puede estar vacía)
            if 'description' in config.field_mapping:
                desc_col = config.field_mapping['description']
                if desc_col < len(row):
                    if not str(row[desc_col]).strip():
                        errors.append(f"Fila {row_num}: Descripción vacía en columna {desc_col + 1}")
        
        except Exception as e:
            errors.append(f"Fila {row_num}: Error validando datos - {str(e)}")
        
        return errors
    
    def _extract_row_data(self, row: List[str], config: ImportConfig) -> Dict[str, Any]:
        """Extrae los datos de una fila según el mapeo de configuración"""
        data = {}
        
        for field, col_index in config.field_mapping.items():
            if col_index < len(row):
                value = str(row[col_index]).strip()
                
                if field == 'date' and value:
                    try:
                        data[field] = datetime.strptime(value, config.date_format).date().isoformat()
                    except ValueError:
                        data[field] = value
                elif field == 'amount' and value:
                    try:
                        data[field] = float(Decimal(value.replace(',', '')))
                    except (InvalidOperation, ValueError):
                        data[field] = value
                else:
                    data[field] = value
        
        return data
    
    def parse_bank_statement(self, file_path: str, config: ImportConfig) -> List[BankMovementCreate]:
        """Parsea un extracto bancario y retorna lista de movimientos"""
        movements = []
        
        try:
            if config.file_format.upper() in ['CSV', 'TXT']:
                movements = self._parse_csv_file(file_path, config)
            elif config.file_format.upper() in ['XLS', 'XLSX']:
                movements = self._parse_excel_file(file_path, config)
        
        except Exception as e:
            raise Exception(f"Error parseando archivo: {str(e)}")
        
        return movements
    
    def _parse_csv_file(self, file_path: str, config: ImportConfig) -> List[BankMovementCreate]:
        """Parsea archivo CSV/TXT"""
        movements = []
        
        with open(file_path, 'r', encoding='utf-8') as file:
            # Saltar filas de encabezado
            for _ in range(config.header_rows):
                next(file, None)
            
            reader = csv.reader(file, delimiter=config.delimiter)
            
            for row in reader:
                try:
                    movement = self._create_movement_from_row(row, config)
                    if movement:
                        movements.append(movement)
                except Exception as e:
                    # Log error pero continúa procesando
                    print(f"Error procesando fila: {str(e)}")
                    continue
        
        return movements
    
    def _parse_excel_file(self, file_path: str, config: ImportConfig) -> List[BankMovementCreate]:
        """Parsea archivo Excel"""
        movements = []
        
        df = pd.read_excel(file_path, skiprows=config.header_rows)
        
        for _, row in df.iterrows():
            try:
                movement = self._create_movement_from_row(row.tolist(), config)
                if movement:
                    movements.append(movement)
            except Exception as e:
                print(f"Error procesando fila: {str(e)}")
                continue
        
        return movements
    
    def _create_movement_from_row(self, row: List[str], config: ImportConfig) -> Optional[BankMovementCreate]:
        """Crea un movimiento bancario desde una fila de datos"""
        try:
            # Extraer campos obligatorios
            transaction_date = None
            amount = None
            description = ""
            
            # Fecha de transacción
            if 'date' in config.field_mapping:
                date_col = config.field_mapping['date']
                if date_col < len(row):
                    date_str = str(row[date_col]).strip()
                    transaction_date = datetime.strptime(date_str, config.date_format).date()
            
            # Monto
            if 'amount' in config.field_mapping:
                amount_col = config.field_mapping['amount']
                if amount_col < len(row):
                    amount_str = str(row[amount_col]).strip().replace(',', '')
                    amount = Decimal(amount_str)
            
            # Descripción
            if 'description' in config.field_mapping:
                desc_col = config.field_mapping['description']
                if desc_col < len(row):
                    description = str(row[desc_col]).strip()
            
            # Campos opcionales
            value_date = transaction_date  # Por defecto igual a transaction_date
            if 'value_date' in config.field_mapping:
                val_date_col = config.field_mapping['value_date']
                if val_date_col < len(row):
                    try:
                        val_date_str = str(row[val_date_col]).strip()
                        if val_date_str:
                            value_date = datetime.strptime(val_date_str, config.date_format).date()
                    except ValueError:
                        pass
            
            reference = None
            if 'reference' in config.field_mapping:
                ref_col = config.field_mapping['reference']
                if ref_col < len(row):
                    reference = str(row[ref_col]).strip() or None
            
            transaction_type = None
            if 'transaction_type' in config.field_mapping:
                type_col = config.field_mapping['transaction_type']
                if type_col < len(row):
                    transaction_type = str(row[type_col]).strip() or None
            
            balance = None
            if 'balance' in config.field_mapping:
                balance_col = config.field_mapping['balance']
                if balance_col < len(row):
                    try:
                        balance_str = str(row[balance_col]).strip().replace(',', '')
                        if balance_str:
                            balance = Decimal(balance_str)
                    except (InvalidOperation, ValueError):
                        pass
            
            # Validar campos obligatorios
            if not transaction_date or amount is None or not description:
                return None
            
            return BankMovementCreate(
                transaction_date=transaction_date,
                value_date=value_date,
                amount=amount,
                description=description,
                reference=reference,
                transaction_type=transaction_type,
                balance=balance,
                import_session_id="",  # Se asignará después
                bank_account_id=0      # Se asignará después
            )
        
        except Exception as e:
            print(f"Error creando movimiento: {str(e)}")
            return None
    
    def detect_duplicates(self, movements: List[BankMovementCreate], bank_account_id: int) -> DuplicateReport:
        """Detecta movimientos duplicados"""
        duplicates = []
        duplicate_groups = []
        
        # Buscar duplicados en la base de datos
        for movement in movements:
            existing = self.db.query(BankMovement).filter(
                and_(
                    BankMovement.bank_account_id == bank_account_id,
                    BankMovement.transaction_date == movement.transaction_date,
                    BankMovement.amount == movement.amount,
                    BankMovement.description == movement.description
                )
            ).first()
            
            if existing:
                duplicates.append({
                    'new_movement': movement.dict(),
                    'existing_movement': {
                        'id': existing.id,
                        'transaction_date': existing.transaction_date.isoformat(),
                        'amount': float(existing.amount),
                        'description': existing.description,
                        'import_session_id': existing.import_session_id
                    }
                })
        
        # Buscar duplicados dentro del mismo lote
        seen = {}
        for i, movement in enumerate(movements):
            key = (movement.transaction_date, movement.amount, movement.description)
            if key in seen:
                duplicate_groups.append({
                    'criteria': {
                        'date': movement.transaction_date.isoformat(),
                        'amount': float(movement.amount),
                        'description': movement.description
                    },
                    'indices': [seen[key], i]
                })
            else:
                seen[key] = i
        
        return DuplicateReport(
            total_duplicates=len(duplicates) + len(duplicate_groups),
            duplicate_groups=duplicates + duplicate_groups,
            action_required=len(duplicates) > 0 or len(duplicate_groups) > 0
        )
    
    def store_movements(self, movements: List[BankMovementCreate], import_session_id: str, 
                       bank_account_id: int, empresa_id: int) -> Dict[str, Any]:
        """Almacena los movimientos en la base de datos"""
        try:
            stored_movements = []
            
            for movement_data in movements:
                movement = BankMovement(
                    import_session_id=import_session_id,
                    bank_account_id=bank_account_id,
                    empresa_id=empresa_id,
                    transaction_date=movement_data.transaction_date,
                    value_date=movement_data.value_date,
                    amount=movement_data.amount,
                    description=movement_data.description,
                    reference=movement_data.reference,
                    transaction_type=movement_data.transaction_type,
                    balance=movement_data.balance,
                    status="PENDING"
                )
                
                self.db.add(movement)
                stored_movements.append(movement)
            
            self.db.commit()
            
            return {
                'success': True,
                'total_stored': len(stored_movements),
                'movements': [m.id for m in stored_movements]
            }
        
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error almacenando movimientos: {str(e)}")
    
    def create_import_session(self, file_path: str, config_id: int, bank_account_id: int, 
                            empresa_id: int, user_id: int) -> ImportSession:
        """Crea una nueva sesión de importación"""
        try:
            # Generar hash del archivo
            file_hash = self._generate_file_hash(file_path)
            
            # Crear sesión
            session_id = str(uuid.uuid4())
            session = ImportSession(
                id=session_id,
                bank_account_id=bank_account_id,
                empresa_id=empresa_id,
                file_name=os.path.basename(file_path),
                file_hash=file_hash,
                import_config_id=config_id,
                user_id=user_id,
                status="PROCESSING"
            )
            
            self.db.add(session)
            self.db.commit()
            
            return session
        
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error creando sesión de importación: {str(e)}")
    
    def _generate_file_hash(self, file_path: str) -> str:
        """Genera hash SHA256 del archivo"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def update_import_session(self, session_id: str, total_movements: int, 
                            successful_imports: int, errors: List[str], status: str):
        """Actualiza el estado de una sesión de importación"""
        try:
            session = self.db.query(ImportSession).filter(ImportSession.id == session_id).first()
            if session:
                session.total_movements = total_movements
                session.successful_imports = successful_imports
                session.errors = errors
                session.status = status
                self.db.commit()
        
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error actualizando sesión: {str(e)}")


class ConfigurationManager:
    """Gestor de configuraciones de importación bancaria"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_configurations(self, empresa_id: int) -> List[ImportConfig]:
        """Obtiene todas las configuraciones de importación para una empresa"""
        return self.db.query(ImportConfig).filter(
            ImportConfig.empresa_id == empresa_id,
            ImportConfig.is_active == True
        ).all()
    
    @cached(ttl=600, key_prefix="import_config")  # Cache por 10 minutos
    def get_configuration_by_id(self, config_id: int, empresa_id: int) -> Optional[ImportConfig]:
        """Obtiene una configuración específica por ID"""
        return self.db.query(ImportConfig).filter(
            ImportConfig.id == config_id,
            ImportConfig.empresa_id == empresa_id
        ).first()
    
    def create_configuration(self, config_data: dict, empresa_id: int, user_id: int) -> ImportConfig:
        """Crea una nueva configuración de importación"""
        # Validar que todos los campos obligatorios estén mapeados
        required_fields = ['date', 'amount', 'description']
        field_mapping = config_data.get('field_mapping', {})
        
        missing_fields = [field for field in required_fields if field not in field_mapping]
        if missing_fields:
            raise ValueError(f"Campos obligatorios faltantes en el mapeo: {missing_fields}")
        
        config = ImportConfig(
            name=config_data['name'],
            bank_id=config_data['bank_id'],
            file_format=config_data['file_format'],
            delimiter=config_data.get('delimiter', ','),
            date_format=config_data['date_format'],
            field_mapping=field_mapping,
            header_rows=config_data.get('header_rows', 0),
            empresa_id=empresa_id,
            created_by=user_id,
            is_active=True
        )
        
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        
        # Registrar en auditoría
        self._log_configuration_change(
            config.id, "CREATE", user_id, "Configuración creada",
            new_values={"name": config.name, "bank_id": config.bank_id, "file_format": config.file_format}
        )
        
        return config
    
    def update_configuration(self, config_id: int, config_data: dict, 
                           empresa_id: int, user_id: int) -> Optional[ImportConfig]:
        """Actualiza una configuración existente"""
        config = self.get_configuration_by_id(config_id, empresa_id)
        if not config:
            return None
        
        # Guardar valores anteriores para auditoría
        old_values = {
            "name": config.name,
            "field_mapping": config.field_mapping,
            "file_format": config.file_format
        }
        
        # Actualizar campos
        for field, value in config_data.items():
            if hasattr(config, field):
                setattr(config, field, value)
        
        # Validar campos obligatorios si se actualiza el mapeo
        if 'field_mapping' in config_data:
            required_fields = ['date', 'amount', 'description']
            field_mapping = config.field_mapping or {}
            missing_fields = [field for field in required_fields if field not in field_mapping]
            if missing_fields:
                raise ValueError(f"Campos obligatorios faltantes en el mapeo: {missing_fields}")
        
        config.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(config)
        
        # Registrar cambios en auditoría
        changes = []
        for field, old_value in old_values.items():
            new_value = getattr(config, field)
            if old_value != new_value:
                changes.append(f"{field}: {old_value} -> {new_value}")
        
        if changes:
            self._log_configuration_change(
                config.id, "UPDATE", user_id, 
                f"Configuración actualizada: {'; '.join(changes)}",
                old_values=old_values,
                new_values={field: getattr(config, field) for field in old_values.keys()}
            )
        
        return config
    
    def delete_configuration(self, config_id: int, empresa_id: int, user_id: int) -> bool:
        """Elimina una configuración (soft delete)"""
        config = self.get_configuration_by_id(config_id, empresa_id)
        if not config:
            return False
        
        # Verificar que no esté siendo usada en importaciones activas
        active_sessions = self.db.query(ImportSession).filter(
            ImportSession.import_config_id == config_id,
            ImportSession.status.in_(['PROCESSING', 'PENDING'])
        ).count()
        
        if active_sessions > 0:
            raise ValueError("No se puede eliminar una configuración con importaciones activas")
        
        config.is_active = False
        config.updated_at = datetime.utcnow()
        self.db.commit()
        
        self._log_configuration_change(config.id, "DELETE", user_id, "Configuración eliminada")
        
        return True
    
    def validate_configuration(self, config: ImportConfig, sample_file_path: str = None) -> Dict[str, Any]:
        """Valida una configuración, opcionalmente con un archivo de muestra"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "sample_validation": None
        }
        
        # Validaciones básicas
        if not config.field_mapping:
            validation_result["errors"].append("El mapeo de campos es obligatorio")
            validation_result["is_valid"] = False
        
        required_fields = ['date', 'amount', 'description']
        field_mapping = config.field_mapping or {}
        missing_fields = [field for field in required_fields if field not in field_mapping]
        if missing_fields:
            validation_result["errors"].append(f"Campos obligatorios faltantes: {missing_fields}")
            validation_result["is_valid"] = False
        
        # Validar formato de fecha
        if config.date_format:
            try:
                datetime.strptime("2023-01-01", config.date_format)
            except ValueError:
                validation_result["errors"].append(f"Formato de fecha inválido: {config.date_format}")
                validation_result["is_valid"] = False
        
        # Validación con archivo de muestra si se proporciona
        if sample_file_path and validation_result["is_valid"]:
            try:
                import_engine = ImportEngine(self.db)
                sample_result = import_engine.validate_file(sample_file_path, config.id)
                validation_result["sample_validation"] = {
                    "file_valid": sample_result.is_valid,
                    "sample_records": sample_result.sample_data[:5] if hasattr(sample_result, 'sample_data') else [],
                    "total_records": sample_result.total_rows if hasattr(sample_result, 'total_rows') else 0,
                    "errors": sample_result.errors
                }
                
                if not sample_result.is_valid:
                    validation_result["warnings"].append("El archivo de muestra no es válido con esta configuración")
                    
            except Exception as e:
                validation_result["warnings"].append(f"Error al validar archivo de muestra: {str(e)}")
        
        return validation_result
    
    def test_configuration_with_sample(self, config_id: int, sample_file_path: str, 
                                     empresa_id: int) -> Dict[str, Any]:
        """Prueba una configuración con un archivo de muestra"""
        config = self.get_configuration_by_id(config_id, empresa_id)
        if not config:
            raise ValueError("Configuración no encontrada")
        
        import_engine = ImportEngine(self.db)
        
        try:
            # Validar archivo
            validation_result = import_engine.validate_file(sample_file_path, config_id)
            
            if validation_result.is_valid:
                # Procesar una muestra pequeña (primeros 10 registros)
                sample_movements = import_engine.parse_bank_statement(sample_file_path, config)[:10]
                
                return {
                    "success": True,
                    "validation": {
                        "is_valid": validation_result.is_valid,
                        "errors": validation_result.errors,
                        "warnings": validation_result.warnings,
                        "total_rows": getattr(validation_result, 'total_rows', 0)
                    },
                    "sample_movements": [
                        {
                            "transaction_date": mov.transaction_date.isoformat(),
                            "amount": float(mov.amount),
                            "description": mov.description,
                            "reference": mov.reference
                        } for mov in sample_movements
                    ],
                    "total_detected": getattr(validation_result, 'total_rows', 0),
                    "message": f"Configuración válida. Se detectaron {getattr(validation_result, 'total_rows', 0)} registros en el archivo."
                }
            else:
                return {
                    "success": False,
                    "validation": {
                        "is_valid": validation_result.is_valid,
                        "errors": validation_result.errors,
                        "warnings": validation_result.warnings
                    },
                    "message": "La configuración no es compatible con el archivo de muestra."
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error al procesar el archivo de muestra."
            }
    
    def get_configuration_audit_trail(self, config_id: int, empresa_id: int) -> List[Dict[str, Any]]:
        """Obtiene el historial de cambios de una configuración"""
        try:
            # Obtener registros de auditoría para la configuración
            audit_records = self.db.query(ReconciliationAudit).filter(
                ReconciliationAudit.empresa_id == empresa_id,
                ReconciliationAudit.operation_type.like(f'CONFIG_%')
            ).order_by(ReconciliationAudit.operation_date.desc()).all()
            
            trail = []
            for record in audit_records:
                trail.append({
                    "id": record.id,
                    "operation_type": record.operation_type,
                    "operation_date": record.operation_date.isoformat(),
                    "user_id": record.user_id,
                    "old_values": record.old_values,
                    "new_values": record.new_values,
                    "ip_address": record.ip_address
                })
            
            return trail
        except Exception as e:
            print(f"Error obteniendo audit trail: {str(e)}")
            return []
    
    def _log_configuration_change(self, config_id: int, action: str, user_id: int, details: str, 
                                old_values: dict = None, new_values: dict = None, 
                                ip_address: str = None, user_agent: str = None):
        """Registra cambios en la configuración para auditoría"""
        try:
            audit_record = ReconciliationAudit(
                empresa_id=self.db.query(ImportConfig).filter(ImportConfig.id == config_id).first().empresa_id,
                operation_type=f"CONFIG_{action}",
                user_id=user_id,
                operation_date=datetime.utcnow(),
                old_values=old_values,
                new_values=new_values or {"details": details},
                ip_address=ip_address,
                user_agent=user_agent
            )
            self.db.add(audit_record)
            self.db.commit()
        except Exception as e:
            print(f"Error logging configuration change: {str(e)}")
    
    def get_configurations_by_bank(self, bank_id: int, empresa_id: int) -> List[ImportConfig]:
        """Obtiene configuraciones filtradas por banco"""
        return self.db.query(ImportConfig).filter(
            ImportConfig.empresa_id == empresa_id,
            ImportConfig.bank_id == bank_id,
            ImportConfig.is_active == True
        ).all()
    
    def duplicate_configuration(self, config_id: int, new_name: str, 
                              empresa_id: int, user_id: int) -> ImportConfig:
        """Duplica una configuración existente con un nuevo nombre"""
        original_config = self.get_configuration_by_id(config_id, empresa_id)
        if not original_config:
            raise ValueError("Configuración original no encontrada")
        
        # Crear nueva configuración basada en la original
        new_config_data = {
            'name': new_name,
            'bank_id': original_config.bank_id,
            'file_format': original_config.file_format,
            'delimiter': original_config.delimiter,
            'date_format': original_config.date_format,
            'field_mapping': original_config.field_mapping.copy() if original_config.field_mapping else {},
            'header_rows': original_config.header_rows
        }
        
        return self.create_configuration(new_config_data, empresa_id, user_id)
    
    def validate_config(self, config: ImportConfig, sample_file: str = None) -> FileValidationResult:
        """Valida una configuración de importación (método legacy)"""
        errors = []
        warnings = []
        
        # Validar campos obligatorios en el mapeo
        required_fields = ['date', 'amount', 'description']
        for field in required_fields:
            if field not in config.field_mapping:
                errors.append(f"Campo obligatorio '{field}' no está mapeado")
        
        # Validar formato de fecha
        try:
            datetime.strptime('2023-01-01', config.date_format)
        except ValueError:
            errors.append(f"Formato de fecha inválido: {config.date_format}")
        
        # Si se proporciona archivo de muestra, validar con él
        if sample_file and os.path.exists(sample_file):
            import_engine = ImportEngine(self.db)
            sample_result = import_engine.validate_file(sample_file, config.id)
            if not sample_result.is_valid:
                errors.extend([f"Muestra: {error}" for error in sample_result.errors])
        
        return FileValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_configuration_structure(self, config_data: dict) -> dict:
        """Valida la estructura de una configuración sin archivo"""
        errors = []
        warnings = []
        
        # Validar campos obligatorios básicos
        required_basic_fields = ['name', 'bank_name', 'file_format']
        for field in required_basic_fields:
            if not config_data.get(field):
                errors.append(f"Campo obligatorio '{field}' está vacío")
        
        # Validar formato de archivo
        valid_formats = ['csv', 'txt', 'excel', 'xls', 'xlsx']
        file_format = config_data.get('file_format', '').lower()
        if file_format and file_format not in valid_formats:
            errors.append(f"Formato de archivo no válido: {file_format}. Formatos válidos: {', '.join(valid_formats)}")
        
        # Validar mapeo de campos
        field_mappings = config_data.get('field_mappings', {})
        if not field_mappings:
            errors.append("El mapeo de campos no puede estar vacío")
        else:
            # Validar campos obligatorios en el mapeo
            required_mapping_fields = ['date', 'description', 'amount']
            for field in required_mapping_fields:
                if not field_mappings.get(field):
                    errors.append(f"Campo obligatorio '{field}' no está mapeado")
        
        # Validar formato de fecha
        date_format = config_data.get('date_format')
        if date_format:
            try:
                # Probar con una fecha de ejemplo
                test_date = '2023-12-31'
                if date_format == 'DD/MM/YYYY':
                    datetime.strptime('31/12/2023', '%d/%m/%Y')
                elif date_format == 'MM/DD/YYYY':
                    datetime.strptime('12/31/2023', '%m/%d/%Y')
                elif date_format == 'YYYY-MM-DD':
                    datetime.strptime('2023-12-31', '%Y-%m-%d')
                elif date_format == 'DD-MM-YYYY':
                    datetime.strptime('31-12-2023', '%d-%m-%Y')
                else:
                    warnings.append(f"Formato de fecha no estándar: {date_format}")
            except ValueError:
                errors.append(f"Formato de fecha inválido: {date_format}")
        
        # Validar delimitador para CSV/TXT
        if file_format in ['csv', 'txt']:
            delimiter = config_data.get('delimiter')
            if not delimiter:
                warnings.append("Delimitador no especificado para archivo CSV/TXT, se usará coma por defecto")
        
        # Validar codificación
        encoding = config_data.get('encoding', 'utf-8')
        valid_encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        if encoding not in valid_encodings:
            warnings.append(f"Codificación no estándar: {encoding}. Recomendadas: {', '.join(valid_encodings)}")
        
        # Validar filas a omitir
        skip_rows = config_data.get('skip_rows', 0)
        if skip_rows < 0:
            errors.append("El número de filas a omitir no puede ser negativo")
        elif skip_rows > 10:
            warnings.append(f"Número alto de filas a omitir: {skip_rows}. Verifique que sea correcto")
        
        # Validar reglas de validación
        validation_rules = config_data.get('validation_rules', {})
        if validation_rules:
            required_fields = validation_rules.get('required_fields', [])
            if not isinstance(required_fields, list):
                errors.append("Los campos requeridos deben ser una lista")
            else:
                # Verificar que los campos requeridos estén en el mapeo
                for field in required_fields:
                    if field not in field_mappings:
                        errors.append(f"Campo requerido '{field}' no está en el mapeo de campos")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "message": "Configuración válida" if len(errors) == 0 else f"Se encontraron {len(errors)} errores"
        }


class MatchingEngine:
    """Motor de conciliación automática de movimientos bancarios y contables"""
    
    def __init__(self, db: Session):
        self.db = db
        self.default_date_tolerance = 3  # días
        self.default_amount_tolerance = 0.01  # 1 centavo
        self.min_confidence_score = 0.7  # 70% mínimo para auto-match
    
    @monitor_performance("bank_reconciliation.auto_matching")
    def auto_match(self, bank_account_id: int, empresa_id: int, 
                   date_from: date = None, date_to: date = None) -> Dict[str, Any]:
        """Ejecuta el proceso de conciliación automática"""
        try:
            # 1. Obtener movimientos bancarios pendientes
            bank_movements = self._get_unmatched_bank_movements(
                bank_account_id, empresa_id, date_from, date_to
            )
            
            # 2. Obtener movimientos contables no conciliados
            accounting_movements = self._get_unmatched_accounting_movements(
                bank_account_id, empresa_id, date_from, date_to
            )
            
            # 3. Ejecutar algoritmos de matching
            exact_matches = self._find_exact_matches(bank_movements, accounting_movements)
            probable_matches = self._find_probable_matches(bank_movements, accounting_movements, exact_matches)
            
            # 4. Aplicar matches automáticos (solo exactos y con alta confianza)
            auto_applied = self._apply_automatic_matches(exact_matches, probable_matches)
            
            # 5. Generar reporte de resultados
            result = {
                "total_bank_movements": len(bank_movements),
                "total_accounting_movements": len(accounting_movements),
                "exact_matches": len(exact_matches),
                "probable_matches": len(probable_matches),
                "auto_applied": len(auto_applied),
                "pending_review": len(bank_movements) - len(auto_applied),
                "matches_applied": auto_applied,
                "suggested_matches": probable_matches,
                "unmatched_bank": [bm for bm in bank_movements if not self._is_movement_matched(bm.id)],
                "unmatched_accounting": [am for am in accounting_movements if not self._is_accounting_movement_matched(am.id)]
            }
            
            return result
            
        except Exception as e:
            raise Exception(f"Error en conciliación automática: {str(e)}")
    
    def _get_unmatched_bank_movements(self, bank_account_id: int, empresa_id: int, 
                                    date_from: date = None, date_to: date = None) -> List[BankMovement]:
        """Obtiene movimientos bancarios no conciliados"""
        query = self.db.query(BankMovement).filter(
            BankMovement.bank_account_id == bank_account_id,
            BankMovement.empresa_id == empresa_id,
            BankMovement.status == "PENDING"
        )
        
        if date_from:
            query = query.filter(BankMovement.transaction_date >= date_from)
        if date_to:
            query = query.filter(BankMovement.transaction_date <= date_to)
        
        return query.all()
    
    def _get_unmatched_accounting_movements(self, bank_account_id: int, empresa_id: int,
                                          date_from: date = None, date_to: date = None):
        """Obtiene movimientos contables no conciliados"""
        # Importar aquí para evitar circular imports
        from ..models.movimiento_contable import MovimientoContable
        from ..models.documento import Documento
        
        query = self.db.query(MovimientoContable).join(Documento).filter(
            MovimientoContable.cuenta_id == bank_account_id,
            Documento.empresa_id == empresa_id,
            MovimientoContable.reconciliation_status == "UNRECONCILED"
        )
        
        if date_from:
            query = query.filter(Documento.fecha >= date_from)
        if date_to:
            query = query.filter(Documento.fecha <= date_to)
        
        return query.all()
    
    def _find_exact_matches(self, bank_movements: List[BankMovement], 
                           accounting_movements: List) -> List[Dict[str, Any]]:
        """Encuentra coincidencias exactas por fecha, monto y referencia"""
        exact_matches = []
        
        for bank_mov in bank_movements:
            for acc_mov in accounting_movements:
                # Obtener fecha del documento asociado
                acc_date = acc_mov.documento.fecha
                # Calcular valor del movimiento contable (débito - crédito)
                acc_value = acc_mov.debito - acc_mov.credito
                
                # Verificar coincidencia exacta
                if (bank_mov.transaction_date == acc_date and
                    abs(bank_mov.amount - abs(acc_value)) < self.default_amount_tolerance):
                    
                    match = {
                        "bank_movement": bank_mov,
                        "accounting_movements": [acc_mov],
                        "match_type": "EXACT",
                        "confidence_score": 1.0,
                        "criteria_matched": ["date", "amount"],
                        "date_difference": 0,
                        "amount_difference": float(abs(bank_mov.amount - abs(acc_value)))
                    }
                    exact_matches.append(match)
                    break  # Una vez encontrado match exacto, no buscar más
        
        return exact_matches
    
    def _find_probable_matches(self, bank_movements: List[BankMovement], 
                              accounting_movements: List, 
                              exact_matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Encuentra coincidencias probables con scoring"""
        probable_matches = []
        
        # Excluir movimientos ya matched exactamente
        exact_bank_ids = {match["bank_movement"].id for match in exact_matches}
        exact_acc_ids = {acc_mov.id for match in exact_matches for acc_mov in match["accounting_movements"]}
        
        for bank_mov in bank_movements:
            if bank_mov.id in exact_bank_ids:
                continue
                
            best_matches = []
            
            for acc_mov in accounting_movements:
                if acc_mov.id in exact_acc_ids:
                    continue
                
                # Calcular score de coincidencia
                score_data = self._calculate_match_score(bank_mov, acc_mov)
                
                if score_data["confidence_score"] >= 0.5:  # Umbral mínimo para considerar
                    match = {
                        "bank_movement": bank_mov,
                        "accounting_movements": [acc_mov],
                        "match_type": "PROBABLE",
                        **score_data
                    }
                    best_matches.append(match)
            
            # Ordenar por score y tomar los mejores
            best_matches.sort(key=lambda x: x["confidence_score"], reverse=True)
            probable_matches.extend(best_matches[:3])  # Top 3 matches por movimiento bancario
        
        return probable_matches
    
    def _calculate_match_score(self, bank_mov: BankMovement, acc_mov) -> Dict[str, Any]:
        """Calcula el score de coincidencia entre dos movimientos"""
        score = 0.0
        criteria_matched = []
        
        # Obtener fecha del documento asociado
        acc_date = acc_mov.documento.fecha
        # Calcular valor del movimiento contable (débito - crédito)
        acc_value = acc_mov.debito - acc_mov.credito
        
        # 1. Coincidencia de fecha (40% del score)
        date_diff = abs((bank_mov.transaction_date - acc_date).days)
        if date_diff == 0:
            score += 0.4
            criteria_matched.append("date")
        elif date_diff <= self.default_date_tolerance:
            score += 0.4 * (1 - date_diff / self.default_date_tolerance)
            criteria_matched.append("date_close")
        
        # 2. Coincidencia de monto (40% del score)
        amount_diff = abs(bank_mov.amount - abs(acc_value))
        if amount_diff < self.default_amount_tolerance:
            score += 0.4
            criteria_matched.append("amount")
        elif amount_diff <= abs(bank_mov.amount * 0.05):  # 5% de tolerancia
            score += 0.4 * (1 - amount_diff / abs(bank_mov.amount * 0.05))
            criteria_matched.append("amount_close")
        
        # 3. Coincidencia de referencia/descripción (20% del score)
        ref_similarity = self._calculate_text_similarity(
            bank_mov.description or "", 
            acc_mov.concepto or ""
        )
        
        if ref_similarity > 0.8:
            score += 0.2
            criteria_matched.append("reference")
        elif ref_similarity > 0.5:
            score += 0.2 * ref_similarity
            criteria_matched.append("reference_partial")
        
        return {
            "confidence_score": min(score, 1.0),
            "criteria_matched": criteria_matched,
            "date_difference": date_diff,
            "amount_difference": float(amount_diff),
            "reference_similarity": ref_similarity
        }
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calcula similitud entre dos textos"""
        if not text1 or not text2:
            return 0.0
        
        # Normalizar textos
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()
        
        if text1 == text2:
            return 1.0
        
        # Usar difflib para calcular similitud
        similarity = difflib.SequenceMatcher(None, text1, text2).ratio()
        return similarity
    
    def _compare_references(self, ref1: str, ref2: str) -> bool:
        """Compara referencias para match exacto"""
        if not ref1 or not ref2:
            return False
        
        return ref1.strip().lower() == ref2.strip().lower()
    
    def _apply_automatic_matches(self, exact_matches: List[Dict[str, Any]], 
                               probable_matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aplica matches automáticos que cumplen criterios de confianza"""
        applied_matches = []
        
        try:
            # Aplicar todos los matches exactos
            for match in exact_matches:
                reconciliation = self._create_reconciliation(
                    match["bank_movement"],
                    match["accounting_movements"],
                    "AUTO",
                    match["confidence_score"],
                    f"Match automático exacto: {', '.join(match['criteria_matched'])}"
                )
                
                if reconciliation:
                    applied_matches.append({
                        **match,
                        "reconciliation_id": reconciliation.id,
                        "applied": True
                    })
            
            # Aplicar matches probables con alta confianza
            for match in probable_matches:
                if match["confidence_score"] >= self.min_confidence_score:
                    reconciliation = self._create_reconciliation(
                        match["bank_movement"],
                        match["accounting_movements"],
                        "AUTO",
                        match["confidence_score"],
                        f"Match automático probable: {', '.join(match['criteria_matched'])}"
                    )
                    
                    if reconciliation:
                        applied_matches.append({
                            **match,
                            "reconciliation_id": reconciliation.id,
                            "applied": True
                        })
            
            self.db.commit()
            return applied_matches
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error aplicando matches automáticos: {str(e)}")
    
    def _create_reconciliation(self, bank_movement: BankMovement, 
                             accounting_movements: List, 
                             reconciliation_type: str,
                             confidence_score: float,
                             notes: str) -> Optional[Reconciliation]:
        """Crea un registro de conciliación"""
        try:
            # Crear reconciliación principal
            reconciliation = Reconciliation(
                bank_movement_id=bank_movement.id,
                empresa_id=bank_movement.empresa_id,
                reconciliation_type=reconciliation_type,
                user_id=1,  # TODO: Obtener usuario del contexto
                confidence_score=confidence_score,
                notes=notes,
                status="ACTIVE"
            )
            
            self.db.add(reconciliation)
            self.db.flush()  # Para obtener el ID
            
            # Crear relaciones con movimientos contables
            for acc_mov in accounting_movements:
                reconciliation_movement = ReconciliationMovement(
                    reconciliation_id=reconciliation.id,
                    accounting_movement_id=acc_mov.id
                )
                self.db.add(reconciliation_movement)
                
                # Actualizar estado del movimiento contable
                acc_mov.reconciliation_status = "RECONCILED"
            
            # Actualizar estado del movimiento bancario
            bank_movement.status = "MATCHED"
            
            return reconciliation
            
        except Exception as e:
            print(f"Error creando reconciliación: {str(e)}")
            return None
    
    def _is_movement_matched(self, bank_movement_id: int) -> bool:
        """Verifica si un movimiento bancario ya está conciliado"""
        return self.db.query(Reconciliation).filter(
            Reconciliation.bank_movement_id == bank_movement_id,
            Reconciliation.status == "ACTIVE"
        ).first() is not None
    
    def _is_accounting_movement_matched(self, accounting_movement_id: int) -> bool:
        """Verifica si un movimiento contable ya está conciliado"""
        return self.db.query(ReconciliationMovement).filter(
            ReconciliationMovement.accounting_movement_id == accounting_movement_id
        ).first() is not None
    
    def suggest_matches(self, bank_movement_id: int, empresa_id: int, 
                       limit: int = 5) -> List[Dict[str, Any]]:
        """Sugiere matches para un movimiento bancario específico"""
        try:
            # Obtener movimiento bancario
            bank_movement = self.db.query(BankMovement).filter(
                BankMovement.id == bank_movement_id,
                BankMovement.empresa_id == empresa_id
            ).first()
            
            if not bank_movement:
                raise ValueError("Movimiento bancario no encontrado")
            
            # Obtener movimientos contables candidatos
            accounting_movements = self._get_unmatched_accounting_movements(
                bank_movement.bank_account_id, 
                empresa_id,
                bank_movement.transaction_date - timedelta(days=self.default_date_tolerance),
                bank_movement.transaction_date + timedelta(days=self.default_date_tolerance)
            )
            
            # Calcular scores y ordenar
            suggestions = []
            for acc_mov in accounting_movements:
                score_data = self._calculate_match_score(bank_movement, acc_mov)
                
                if score_data["confidence_score"] > 0.3:  # Umbral mínimo para sugerencias
                    suggestion = {
                        "accounting_movement": acc_mov,
                        "bank_movement": bank_movement,
                        **score_data
                    }
                    suggestions.append(suggestion)
            
            # Ordenar por score y limitar resultados
            suggestions.sort(key=lambda x: x["confidence_score"], reverse=True)
            return suggestions[:limit]
            
        except Exception as e:
            raise Exception(f"Error generando sugerencias: {str(e)}")
    
    @monitor_performance("bank_reconciliation.manual_reconciliation")
    def apply_manual_match(self, bank_movement_id: int, accounting_movement_ids: List[int],
                          empresa_id: int, user_id: int, notes: str = None) -> Dict[str, Any]:
        """Aplica una conciliación manual"""
        try:
            # Validar movimiento bancario
            bank_movement = self.db.query(BankMovement).filter(
                BankMovement.id == bank_movement_id,
                BankMovement.empresa_id == empresa_id,
                BankMovement.status == "PENDING"
            ).first()
            
            if not bank_movement:
                raise ValueError("Movimiento bancario no encontrado o ya conciliado")
            
            # Validar movimientos contables
            from ..models.movimiento_contable import MovimientoContable
            from ..models.documento import Documento
            
            accounting_movements = self.db.query(MovimientoContable).join(Documento).filter(
                MovimientoContable.id.in_(accounting_movement_ids),
                Documento.empresa_id == empresa_id,
                MovimientoContable.reconciliation_status == "UNRECONCILED"
            ).all()
            
            if len(accounting_movements) != len(accounting_movement_ids):
                raise ValueError("Algunos movimientos contables no están disponibles para conciliación")
            
            # Crear reconciliación manual
            reconciliation = self._create_reconciliation(
                bank_movement,
                accounting_movements,
                "MANUAL",
                1.0,  # Confianza máxima para matches manuales
                notes or "Conciliación manual"
            )
            
            if not reconciliation:
                raise Exception("Error creando reconciliación")
            
            self.db.commit()
            
            return {
                "success": True,
                "reconciliation_id": reconciliation.id,
                "bank_movement_id": bank_movement_id,
                "accounting_movement_ids": accounting_movement_ids,
                "message": "Conciliación manual aplicada exitosamente"
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error en conciliación manual: {str(e)}")
    
    def reverse_reconciliation(self, reconciliation_id: int, empresa_id: int, 
                             user_id: int, reason: str) -> Dict[str, Any]:
        """Revierte una conciliación existente"""
        try:
            # Obtener reconciliación
            reconciliation = self.db.query(Reconciliation).filter(
                Reconciliation.id == reconciliation_id,
                Reconciliation.empresa_id == empresa_id,
                Reconciliation.status == "ACTIVE"
            ).first()
            
            if not reconciliation:
                raise ValueError("Conciliación no encontrada o ya revertida")
            
            # Revertir estado del movimiento bancario
            bank_movement = reconciliation.bank_movement
            bank_movement.status = "PENDING"
            
            # Revertir estado de movimientos contables
            for rec_mov in reconciliation.accounting_movements:
                acc_mov = rec_mov.accounting_movement
                acc_mov.reconciliation_status = "UNRECONCILED"
            
            # Marcar reconciliación como revertida
            reconciliation.status = "REVERSED"
            
            # Crear registro de auditoría
            audit_record = ReconciliationAudit(
                reconciliation_id=reconciliation_id,
                empresa_id=empresa_id,
                operation_type="REVERSE",
                user_id=user_id,
                old_values={"status": "ACTIVE"},
                new_values={"status": "REVERSED", "reason": reason}
            )
            self.db.add(audit_record)
            
            self.db.commit()
            
            return {
                "success": True,
                "reconciliation_id": reconciliation_id,
                "message": "Conciliación revertida exitosamente"
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error revirtiendo conciliación: {str(e)}")
    
    def get_reconciliation_summary(self, bank_account_id: int, empresa_id: int,
                                 date_from: date = None, date_to: date = None) -> Dict[str, Any]:
        """Obtiene resumen del estado de conciliación"""
        try:
            # Contar movimientos bancarios
            bank_query = self.db.query(BankMovement).filter(
                BankMovement.bank_account_id == bank_account_id,
                BankMovement.empresa_id == empresa_id
            )
            
            if date_from:
                bank_query = bank_query.filter(BankMovement.transaction_date >= date_from)
            if date_to:
                bank_query = bank_query.filter(BankMovement.transaction_date <= date_to)
            
            total_bank_movements = bank_query.count()
            matched_bank_movements = bank_query.filter(BankMovement.status == "MATCHED").count()
            pending_bank_movements = bank_query.filter(BankMovement.status == "PENDING").count()
            
            # Contar movimientos contables
            from ..models.movimiento_contable import MovimientoContable
            from ..models.documento import Documento
            
            acc_query = self.db.query(MovimientoContable).join(Documento).filter(
                MovimientoContable.cuenta_id == bank_account_id,
                Documento.empresa_id == empresa_id
            )
            
            if date_from:
                acc_query = acc_query.filter(Documento.fecha >= date_from)
            if date_to:
                acc_query = acc_query.filter(Documento.fecha <= date_to)
            
            total_accounting_movements = acc_query.count()
            reconciled_accounting_movements = acc_query.filter(
                MovimientoContable.reconciliation_status == "RECONCILED"
            ).count()
            unreconciled_accounting_movements = acc_query.filter(
                MovimientoContable.reconciliation_status == "UNRECONCILED"
            ).count()
            
            # Contar reconciliaciones por tipo
            rec_query = self.db.query(Reconciliation).join(BankMovement).filter(
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
            
            # Calcular porcentajes
            reconciliation_rate = (matched_bank_movements / total_bank_movements * 100) if total_bank_movements > 0 else 0
            
            return {
                "bank_movements": {
                    "total": total_bank_movements,
                    "matched": matched_bank_movements,
                    "pending": pending_bank_movements
                },
                "accounting_movements": {
                    "total": total_accounting_movements,
                    "reconciled": reconciled_accounting_movements,
                    "unreconciled": unreconciled_accounting_movements
                },
                "reconciliations": {
                    "automatic": auto_reconciliations,
                    "manual": manual_reconciliations,
                    "total": auto_reconciliations + manual_reconciliations
                },
                "reconciliation_rate": round(reconciliation_rate, 2),
                "period": {
                    "from": date_from.isoformat() if date_from else None,
                    "to": date_to.isoformat() if date_to else None
                }
            }
            
        except Exception as e:
            raise Exception(f"Error generando resumen: {str(e)}")


class AdjustmentEngine:
    """Motor de generación automática de asientos de ajuste"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Patrones de detección para diferentes tipos de ajustes
        self.commission_patterns = [
            'comision', 'comisión', 'fee', 'cargo', 'tarifa',
            'manejo', 'administracion', 'administración'
        ]
        
        self.interest_patterns = [
            'interes', 'interés', 'interest', 'rendimiento',
            'ganancia', 'beneficio'
        ]
        
        self.debit_note_patterns = [
            'nota debito', 'nota débito', 'debit note', 'nd',
            'cargo automatico', 'cargo automático'
        ]
        
        self.credit_note_patterns = [
            'nota credito', 'nota crédito', 'credit note', 'nc',
            'abono automatico', 'abono automático'
        ]
    
    def detect_adjustments(self, bank_movements: List[BankMovement], 
                          bank_account_id: int, empresa_id: int) -> List[Dict[str, Any]]:
        """Detecta movimientos bancarios que requieren ajustes contables"""
        try:
            adjustments = []
            
            # Obtener configuración contable para la cuenta
            accounting_config = self._get_accounting_config(bank_account_id, empresa_id)
            
            for movement in bank_movements:
                # Solo procesar movimientos pendientes
                if movement.status != "PENDING":
                    continue
                
                # Detectar tipo de ajuste basado en descripción
                adjustment_type = self._classify_movement(movement)
                
                if adjustment_type:
                    adjustment = self._create_adjustment_proposal(
                        movement, adjustment_type, accounting_config
                    )
                    if adjustment:
                        adjustments.append(adjustment)
            
            return adjustments
            
        except Exception as e:
            raise Exception(f"Error detectando ajustes: {str(e)}")
    
    def _classify_movement(self, movement: BankMovement) -> Optional[str]:
        """Clasifica un movimiento bancario según su tipo de ajuste"""
        description = movement.description.lower() if movement.description else ""
        
        # Detectar comisiones (generalmente débitos)
        if movement.amount < 0:
            for pattern in self.commission_patterns:
                if pattern in description:
                    return "COMMISSION"
            
            for pattern in self.debit_note_patterns:
                if pattern in description:
                    return "DEBIT_NOTE"
        
        # Detectar intereses (generalmente créditos)
        elif movement.amount > 0:
            for pattern in self.interest_patterns:
                if pattern in description:
                    return "INTEREST"
            
            for pattern in self.credit_note_patterns:
                if pattern in description:
                    return "CREDIT_NOTE"
        
        return None
    
    @cached(ttl=300, key_prefix="accounting_config")  # Cache por 5 minutos
    def _get_accounting_config(self, bank_account_id: int, empresa_id: int) -> Optional[AccountingConfig]:
        """Obtiene la configuración contable para una cuenta bancaria"""
        return self.db.query(AccountingConfig).filter(
            AccountingConfig.bank_account_id == bank_account_id,
            AccountingConfig.empresa_id == empresa_id,
            AccountingConfig.is_active == True
        ).first()
    
    def _create_adjustment_proposal(self, movement: BankMovement, 
                                  adjustment_type: str, 
                                  config: Optional[AccountingConfig]) -> Optional[Dict[str, Any]]:
        """Crea una propuesta de ajuste contable"""
        if not config:
            return None
        
        try:
            # Determinar cuentas según el tipo de ajuste
            account_mapping = {
                "COMMISSION": config.commission_account_id,
                "INTEREST": config.interest_income_account_id,
                "DEBIT_NOTE": config.bank_charges_account_id,
                "CREDIT_NOTE": config.adjustment_account_id
            }
            
            counterpart_account_id = account_mapping.get(adjustment_type)
            if not counterpart_account_id:
                return None
            
            # Obtener información de las cuentas
            bank_account = self._get_account_info(movement.bank_account_id)
            counterpart_account = self._get_account_info(counterpart_account_id)
            
            if not bank_account or not counterpart_account:
                return None
            
            # Crear estructura del asiento
            amount = abs(movement.amount)
            
            # Determinar débitos y créditos según el tipo
            if adjustment_type in ["COMMISSION", "DEBIT_NOTE"]:
                # Gasto: Débito a cuenta de gasto, Crédito a banco
                entries = [
                    {
                        "account_id": counterpart_account_id,
                        "account_code": counterpart_account.codigo,
                        "account_name": counterpart_account.nombre,
                        "debit": amount,
                        "credit": 0,
                        "description": f"{adjustment_type.replace('_', ' ').title()}: {movement.description}"
                    },
                    {
                        "account_id": movement.bank_account_id,
                        "account_code": bank_account.codigo,
                        "account_name": bank_account.nombre,
                        "debit": 0,
                        "credit": amount,
                        "description": f"{adjustment_type.replace('_', ' ').title()}: {movement.description}"
                    }
                ]
            else:  # INTEREST, CREDIT_NOTE
                # Ingreso: Débito a banco, Crédito a cuenta de ingreso
                entries = [
                    {
                        "account_id": movement.bank_account_id,
                        "account_code": bank_account.codigo,
                        "account_name": bank_account.nombre,
                        "debit": amount,
                        "credit": 0,
                        "description": f"{adjustment_type.replace('_', ' ').title()}: {movement.description}"
                    },
                    {
                        "account_id": counterpart_account_id,
                        "account_code": counterpart_account.codigo,
                        "account_name": counterpart_account.nombre,
                        "debit": 0,
                        "credit": amount,
                        "description": f"{adjustment_type.replace('_', ' ').title()}: {movement.description}"
                    }
                ]
            
            return {
                "bank_movement_id": movement.id,
                "bank_movement": {
                    "id": movement.id,
                    "transaction_date": movement.transaction_date.isoformat(),
                    "amount": float(movement.amount),
                    "description": movement.description,
                    "reference": movement.reference
                },
                "adjustment_type": adjustment_type,
                "adjustment_description": self._get_adjustment_description(adjustment_type),
                "total_amount": amount,
                "entries": entries,
                "document_concept": f"Ajuste automático - {adjustment_type.replace('_', ' ').title()}",
                "requires_approval": amount > 100000  # Requiere aprobación si es mayor a $100,000
            }
            
        except Exception as e:
            print(f"Error creando propuesta de ajuste: {str(e)}")
            return None
    
    def _get_account_info(self, account_id: int):
        """Obtiene información de una cuenta contable"""
        from ..models.plan_cuenta import PlanCuenta
        return self.db.query(PlanCuenta).filter(PlanCuenta.id == account_id).first()
    
    def _get_adjustment_description(self, adjustment_type: str) -> str:
        """Obtiene descripción amigable del tipo de ajuste"""
        descriptions = {
            "COMMISSION": "Comisión bancaria",
            "INTEREST": "Interés ganado",
            "DEBIT_NOTE": "Nota débito bancaria",
            "CREDIT_NOTE": "Nota crédito bancaria"
        }
        return descriptions.get(adjustment_type, "Ajuste bancario")
    
    def generate_adjustment_document(self, adjustment_proposal: Dict[str, Any], 
                                   user_id: int, empresa_id: int) -> Dict[str, Any]:
        """Genera el documento contable para un ajuste"""
        try:
            from ..models.documento import Documento
            from ..models.movimiento_contable import MovimientoContable
            from ..models.tipo_documento import TipoDocumento
            
            # Buscar tipo de documento para ajustes (o usar uno genérico)
            tipo_doc = self.db.query(TipoDocumento).filter(
                TipoDocumento.codigo == "AJ",
                TipoDocumento.empresa_id == empresa_id
            ).first()
            
            if not tipo_doc:
                # Usar tipo de documento genérico si no existe específico para ajustes
                tipo_doc = self.db.query(TipoDocumento).filter(
                    TipoDocumento.empresa_id == empresa_id
                ).first()
            
            if not tipo_doc:
                raise Exception("No se encontró tipo de documento disponible")
            
            # Generar número de documento
            next_number = self._get_next_document_number(tipo_doc.id, empresa_id)
            
            # Crear documento
            documento = Documento(
                numero=str(next_number),
                fecha=adjustment_proposal["bank_movement"]["transaction_date"],
                concepto=adjustment_proposal["document_concept"],
                tipo_documento_id=tipo_doc.id,
                empresa_id=empresa_id,
                usuario_id=user_id,
                estado="ACTIVO",
                total_debito=adjustment_proposal["total_amount"],
                total_credito=adjustment_proposal["total_amount"]
            )
            
            self.db.add(documento)
            self.db.flush()  # Para obtener el ID
            
            # Crear movimientos contables
            movimientos = []
            for entry in adjustment_proposal["entries"]:
                movimiento = MovimientoContable(
                    documento_id=documento.id,
                    cuenta_id=entry["account_id"],
                    debito=entry["debit"],
                    credito=entry["credit"],
                    concepto=entry["description"],
                    referencia=adjustment_proposal["bank_movement"]["reference"],
                    fecha=adjustment_proposal["bank_movement"]["transaction_date"],
                    reconciliation_status="RECONCILED"  # Ya está conciliado por definición
                )
                self.db.add(movimiento)
                movimientos.append(movimiento)
            
            self.db.commit()
            
            # Actualizar estado del movimiento bancario
            bank_movement = self.db.query(BankMovement).filter(
                BankMovement.id == adjustment_proposal["bank_movement_id"]
            ).first()
            
            if bank_movement:
                bank_movement.status = "ADJUSTED"
                self.db.commit()
            
            return {
                "success": True,
                "document_id": documento.id,
                "document_number": documento.numero,
                "total_amount": adjustment_proposal["total_amount"],
                "entries_count": len(movimientos),
                "bank_movement_id": adjustment_proposal["bank_movement_id"]
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error generando documento de ajuste: {str(e)}")
    
    def _get_next_document_number(self, tipo_documento_id: int, empresa_id: int) -> int:
        """Obtiene el siguiente número de documento"""
        from ..models.documento import Documento
        
        last_doc = self.db.query(Documento).filter(
            Documento.tipo_documento_id == tipo_documento_id,
            Documento.empresa_id == empresa_id
        ).order_by(Documento.numero.desc()).first()
        
        if last_doc and last_doc.numero.isdigit():
            return int(last_doc.numero) + 1
        else:
            return 1
    
    def preview_adjustments(self, bank_account_id: int, empresa_id: int, 
                          date_from: date = None, date_to: date = None) -> Dict[str, Any]:
        """Genera vista previa de ajustes automáticos"""
        try:
            # Verificar si existe configuración contable
            accounting_config = self._get_accounting_config(bank_account_id, empresa_id)
            
            # Obtener movimientos bancarios pendientes
            query = self.db.query(BankMovement).filter(
                BankMovement.bank_account_id == bank_account_id,
                BankMovement.empresa_id == empresa_id,
                BankMovement.status == "PENDING"
            )
            
            if date_from:
                query = query.filter(BankMovement.transaction_date >= date_from)
            if date_to:
                query = query.filter(BankMovement.transaction_date <= date_to)
            
            bank_movements = query.all()
            
            # Si no hay configuración contable, retornar respuesta informativa
            if not accounting_config:
                return {
                    "bank_account_id": bank_account_id,
                    "period": {
                        "from": date_from.isoformat() if date_from else None,
                        "to": date_to.isoformat() if date_to else None
                    },
                    "summary": {
                        "total_movements_analyzed": len(bank_movements),
                        "total_adjustments_detected": 0,
                        "total_amount": 0,
                        "adjustments_by_type": {}
                    },
                    "adjustments": [],
                    "requires_approval": False,
                    "configuration_missing": True,
                    "message": "No se encontró configuración contable para esta cuenta bancaria. Configure las cuentas contables para generar ajustes automáticos."
                }
            
            # Detectar ajustes
            adjustments = self.detect_adjustments(bank_movements, bank_account_id, empresa_id)
            
            # Calcular estadísticas
            total_adjustments = len(adjustments)
            total_amount = sum(adj.get("total_amount", 0) for adj in adjustments)
            
            adjustments_by_type = {}
            for adj in adjustments:
                adj_type = adj.get("adjustment_type", "UNKNOWN")
                if adj_type not in adjustments_by_type:
                    adjustments_by_type[adj_type] = {
                        "count": 0,
                        "total_amount": 0,
                        "description": adj.get("adjustment_description", "")
                    }
                adjustments_by_type[adj_type]["count"] += 1
                adjustments_by_type[adj_type]["total_amount"] += adj.get("total_amount", 0)
            
            return {
                "bank_account_id": bank_account_id,
                "period": {
                    "from": date_from.isoformat() if date_from else None,
                    "to": date_to.isoformat() if date_to else None
                },
                "summary": {
                    "total_movements_analyzed": len(bank_movements),
                    "total_adjustments_detected": total_adjustments,
                    "total_amount": total_amount,
                    "adjustments_by_type": adjustments_by_type
                },
                "adjustments": adjustments,
                "requires_approval": any(adj.get("requires_approval", False) for adj in adjustments),
                "configuration_missing": False
            }
            
        except Exception as e:
            raise Exception(f"Error generando vista previa de ajustes: {str(e)}")
    
    def apply_adjustments(self, adjustment_ids: List[int], user_id: int, 
                         empresa_id: int, notes: str = None) -> Dict[str, Any]:
        """Aplica ajustes seleccionados generando documentos contables"""
        try:
            results = []
            total_processed = 0
            total_successful = 0
            
            # Obtener movimientos bancarios para los ajustes
            bank_movements = self.db.query(BankMovement).filter(
                BankMovement.id.in_(adjustment_ids),
                BankMovement.empresa_id == empresa_id,
                BankMovement.status == "PENDING"
            ).all()
            
            # Detectar ajustes para estos movimientos
            adjustments = self.detect_adjustments(bank_movements, 
                                                bank_movements[0].bank_account_id if bank_movements else 0, 
                                                empresa_id)
            
            # Filtrar solo los ajustes solicitados
            filtered_adjustments = [
                adj for adj in adjustments 
                if adj["bank_movement_id"] in adjustment_ids
            ]
            
            for adjustment in filtered_adjustments:
                total_processed += 1
                
                try:
                    # Agregar notas si se proporcionaron
                    if notes:
                        adjustment["document_concept"] += f" - {notes}"
                    
                    # Generar documento contable
                    result = self.generate_adjustment_document(adjustment, user_id, empresa_id)
                    
                    results.append({
                        "bank_movement_id": adjustment["bank_movement_id"],
                        "success": True,
                        "document_id": result["document_id"],
                        "document_number": result["document_number"],
                        "adjustment_type": adjustment["adjustment_type"],
                        "amount": adjustment["total_amount"]
                    })
                    
                    total_successful += 1
                    
                except Exception as e:
                    results.append({
                        "bank_movement_id": adjustment["bank_movement_id"],
                        "success": False,
                        "error": str(e),
                        "adjustment_type": adjustment["adjustment_type"],
                        "amount": adjustment["total_amount"]
                    })
            
            return {
                "total_processed": total_processed,
                "total_successful": total_successful,
                "total_failed": total_processed - total_successful,
                "results": results
            }
            
        except Exception as e:
            raise Exception(f"Error aplicando ajustes: {str(e)}")