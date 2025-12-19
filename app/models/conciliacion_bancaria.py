from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date, DateTime, TIMESTAMP, Text, Numeric, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base

class ImportConfig(Base):
    """Configuración de importación para diferentes bancos"""
    __tablename__ = "import_configs"

    id = Column(Integer, primary_key=True, index=True)
    bank_id = Column(Integer, ForeignKey("terceros.id"), nullable=False)  # Referencia al tercero que representa el banco
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    name = Column(String(255), nullable=False)
    file_format = Column(String(10), nullable=False)  # CSV, TXT, XLS
    delimiter = Column(String(5), default=",")
    date_format = Column(String(20), default="%Y-%m-%d")
    field_mapping = Column(JSON, nullable=False)  # Mapeo de campos: {"date": 0, "amount": 1, "description": 2, etc.}
    header_rows = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    # Relaciones
    bank = relationship("Tercero", foreign_keys=[bank_id])
    empresa = relationship("Empresa")
    creator = relationship("Usuario", foreign_keys=[created_by])
    updater = relationship("Usuario", foreign_keys=[updated_by])
    import_sessions = relationship("ImportSession", back_populates="import_config")


class ImportSession(Base):
    """Sesión de importación de extracto bancario"""
    __tablename__ = "import_sessions"

    id = Column(String(36), primary_key=True, index=True)  # UUID
    bank_account_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=False)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA256 hash del archivo
    import_config_id = Column(Integer, ForeignKey("import_configs.id"), nullable=False)
    total_movements = Column(Integer, default=0)
    successful_imports = Column(Integer, default=0)
    errors = Column(JSON, nullable=True)  # Lista de errores encontrados
    user_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    import_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="PROCESSING")  # PROCESSING, COMPLETED, FAILED
    
    # Relaciones
    bank_account = relationship("PlanCuenta")
    empresa = relationship("Empresa")
    import_config = relationship("ImportConfig", back_populates="import_sessions")
    user = relationship("Usuario")
    bank_movements = relationship("BankMovement", back_populates="import_session")


class BankMovement(Base):
    """Movimiento bancario importado"""
    __tablename__ = "bank_movements"

    id = Column(Integer, primary_key=True, index=True)
    import_session_id = Column(String(36), ForeignKey("import_sessions.id"), nullable=False)
    bank_account_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=False)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    transaction_date = Column(Date, nullable=False)
    value_date = Column(Date, nullable=True)
    amount = Column(Numeric(15, 2), nullable=False)
    description = Column(Text, nullable=False)
    reference = Column(String(100), nullable=True)
    transaction_type = Column(String(50), nullable=True)  # DEBIT, CREDIT, etc.
    balance = Column(Numeric(15, 2), nullable=True)
    status = Column(String(20), default="PENDING")  # PENDING, MATCHED, ADJUSTED
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    import_session = relationship("ImportSession", back_populates="bank_movements")
    bank_account = relationship("PlanCuenta")
    empresa = relationship("Empresa")
    reconciliations = relationship("Reconciliation", back_populates="bank_movement")


class Reconciliation(Base):
    """Registro de conciliación entre movimientos bancarios y contables"""
    __tablename__ = "reconciliations"

    id = Column(Integer, primary_key=True, index=True)
    bank_movement_id = Column(Integer, ForeignKey("bank_movements.id"), nullable=False)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    reconciliation_type = Column(String(20), nullable=False)  # AUTO, MANUAL, ADJUSTMENT
    user_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    reconciliation_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
    status = Column(String(20), default="ACTIVE")  # ACTIVE, REVERSED
    confidence_score = Column(Numeric(5, 2), nullable=True)  # Para matching automático

    # Relaciones
    bank_movement = relationship("BankMovement", back_populates="reconciliations")
    empresa = relationship("Empresa")
    user = relationship("Usuario")
    accounting_movements = relationship("ReconciliationMovement", back_populates="reconciliation")


class ReconciliationMovement(Base):
    """Tabla de unión entre conciliaciones y movimientos contables"""
    __tablename__ = "reconciliation_movements"

    id = Column(Integer, primary_key=True, index=True)
    reconciliation_id = Column(Integer, ForeignKey("reconciliations.id"), nullable=False)
    accounting_movement_id = Column(Integer, ForeignKey("movimientos_contables.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    reconciliation = relationship("Reconciliation", back_populates="accounting_movements")
    accounting_movement = relationship("MovimientoContable")


class AccountingConfig(Base):
    """Configuración contable para cuentas bancarias"""
    __tablename__ = "accounting_configs"

    id = Column(Integer, primary_key=True, index=True)
    bank_account_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=False)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    commission_account_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True)
    interest_income_account_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True)
    bank_charges_account_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True)
    adjustment_account_id = Column(Integer, ForeignKey("plan_cuentas.id"), nullable=True)
    default_cost_center_id = Column(Integer, ForeignKey("centros_costo.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    # Relaciones
    bank_account = relationship("PlanCuenta", foreign_keys=[bank_account_id])
    empresa = relationship("Empresa")
    commission_account = relationship("PlanCuenta", foreign_keys=[commission_account_id])
    interest_income_account = relationship("PlanCuenta", foreign_keys=[interest_income_account_id])
    bank_charges_account = relationship("PlanCuenta", foreign_keys=[bank_charges_account_id])
    adjustment_account = relationship("PlanCuenta", foreign_keys=[adjustment_account_id])
    default_cost_center = relationship("CentroCosto")
    creator = relationship("Usuario", foreign_keys=[created_by])
    updater = relationship("Usuario", foreign_keys=[updated_by])


class ReconciliationAudit(Base):
    """Auditoría de operaciones de conciliación"""
    __tablename__ = "reconciliation_audits"

    id = Column(Integer, primary_key=True, index=True)
    reconciliation_id = Column(Integer, ForeignKey("reconciliations.id"), nullable=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    operation_type = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE, REVERSE
    user_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    operation_date = Column(DateTime, default=datetime.utcnow)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Relaciones
    reconciliation = relationship("Reconciliation")
    empresa = relationship("Empresa")
    user = relationship("Usuario")