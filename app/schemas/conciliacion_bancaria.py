from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal

# Schemas para ImportConfig
class ImportConfigBase(BaseModel):
    bank_id: int
    name: str
    file_format: str = Field(..., pattern="^(CSV|TXT|XLS|XLSX)$")
    delimiter: str = ","
    date_format: str = "%Y-%m-%d"
    field_mapping: Dict[str, int]
    header_rows: int = 1
    is_active: bool = True

class ImportConfigCreate(ImportConfigBase):
    pass

class ImportConfigUpdate(BaseModel):
    name: Optional[str] = None
    file_format: Optional[str] = None
    delimiter: Optional[str] = None
    date_format: Optional[str] = None
    field_mapping: Optional[Dict[str, int]] = None
    header_rows: Optional[int] = None
    is_active: Optional[bool] = None

class ImportConfig(ImportConfigBase):
    id: int
    empresa_id: int
    created_at: datetime
    updated_at: datetime
    created_by: int
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

# Schemas para ImportSession
class ImportSessionBase(BaseModel):
    bank_account_id: int
    file_name: str
    file_hash: str
    import_config_id: int
    total_movements: int = 0
    successful_imports: int = 0
    errors: Optional[List[str]] = None
    status: str = "PROCESSING"

class ImportSessionCreate(ImportSessionBase):
    pass

class ImportSession(ImportSessionBase):
    id: str
    empresa_id: int
    user_id: int
    import_date: datetime

    class Config:
        from_attributes = True

# Schemas para BankMovement
class BankMovementBase(BaseModel):
    transaction_date: date
    value_date: Optional[date] = None
    amount: Decimal
    description: str
    reference: Optional[str] = None
    transaction_type: Optional[str] = None
    balance: Optional[Decimal] = None
    status: str = "PENDING"

class BankMovementCreate(BankMovementBase):
    import_session_id: str
    bank_account_id: int

class BankMovement(BankMovementBase):
    id: int
    import_session_id: str
    bank_account_id: int
    empresa_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Schemas para Reconciliation
class ReconciliationBase(BaseModel):
    reconciliation_type: str = Field(..., pattern="^(AUTO|MANUAL|ADJUSTMENT)$")
    notes: Optional[str] = None
    status: str = "ACTIVE"
    confidence_score: Optional[Decimal] = None

class ReconciliationCreate(ReconciliationBase):
    bank_movement_id: int
    accounting_movement_ids: List[int]

class ReconciliationUpdate(BaseModel):
    notes: Optional[str] = None
    status: Optional[str] = None

class Reconciliation(ReconciliationBase):
    id: int
    bank_movement_id: int
    empresa_id: int
    user_id: int
    reconciliation_date: datetime

    class Config:
        from_attributes = True

# Schemas para AccountingConfig
class AccountingConfigBase(BaseModel):
    commission_account_id: Optional[int] = None
    interest_income_account_id: Optional[int] = None
    bank_charges_account_id: Optional[int] = None
    adjustment_account_id: Optional[int] = None
    default_cost_center_id: Optional[int] = None
    is_active: bool = True

class AccountingConfigCreate(AccountingConfigBase):
    bank_account_id: int

class AccountingConfigUpdate(AccountingConfigBase):
    pass

class AccountingConfig(AccountingConfigBase):
    id: int
    bank_account_id: int
    empresa_id: int
    created_at: datetime
    updated_at: datetime
    created_by: int
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True

# Schemas para respuestas y operaciones
class FileValidationResult(BaseModel):
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    total_rows: int = 0
    sample_data: List[Dict[str, Any]] = []

class MatchingResult(BaseModel):
    total_bank_movements: int
    total_accounting_movements: int
    exact_matches: int
    suggested_matches: int
    unmatched_bank: int
    unmatched_accounting: int
    confidence_threshold: float = 0.8

class MatchSuggestion(BaseModel):
    bank_movement_id: int
    accounting_movement_id: int
    confidence_score: float
    matching_criteria: List[str]

class ReconciliationSummary(BaseModel):
    period_start: date
    period_end: date
    bank_account_id: int
    opening_balance: Decimal
    closing_balance: Decimal
    total_reconciled: int
    total_pending: int
    total_adjustments: int
    reconciled_amount: Decimal
    pending_amount: Decimal

class DuplicateReport(BaseModel):
    total_duplicates: int
    duplicate_groups: List[Dict[str, Any]]
    action_required: bool

# Schemas para interfaz de conciliación manual
class UnmatchedMovement(BaseModel):
    id: int
    date: date
    amount: Decimal
    description: str
    reference: Optional[str] = None
    type: str  # "bank" o "accounting"
    status: str
    additional_info: Optional[Dict[str, Any]] = None

class ManualMatchPreview(BaseModel):
    bank_movement: Dict[str, Any]
    accounting_movements: List[Dict[str, Any]]
    totals: Dict[str, Any]
    confidence_score: float
    warnings: List[str] = []
    is_balanced: bool

class ManualMatchRequest(BaseModel):
    bank_movement_id: int
    accounting_movement_ids: List[int]
    notes: Optional[str] = None

class ManualMatchResponse(BaseModel):
    success: bool
    reconciliation_id: Optional[int] = None
    message: str
    warnings: List[str] = []

class ReconciliationAuditRecord(BaseModel):
    id: int
    operation_type: str
    operation_date: datetime
    user_id: int
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None

class ReconciliationAuditTrail(BaseModel):
    reconciliation_id: int
    audit_trail: List[ReconciliationAuditRecord]
    total_operations: int

class BulkOperationRequest(BaseModel):
    operation: str  # "match", "unmatch", "suggest"
    bank_movement_ids: List[int]
    accounting_movement_ids: Optional[List[int]] = None
    notes: Optional[str] = None

class BulkOperationResult(BaseModel):
    bank_movement_id: int
    success: bool
    reconciliation_id: Optional[int] = None
    error: Optional[str] = None
    suggestions_count: Optional[int] = None

class BulkOperationResponse(BaseModel):
    operation: str
    total_processed: int
    successful: int
    failed: int
    results: List[BulkOperationResult]

class MovementSearchRequest(BaseModel):
    bank_account_id: int
    query: str
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    limit: int = 20

class MovementSearchResponse(BaseModel):
    movements: List[Dict[str, Any]]
    total_found: int
    query: str
    limit: int

class ReconciliationDetail(BaseModel):
    id: int
    bank_movement: Dict[str, Any]
    accounting_movements: List[Dict[str, Any]]
    reconciliation_type: str
    confidence_score: Optional[float] = None
    reconciliation_date: datetime
    notes: Optional[str] = None
    status: str
    user_id: int

class ReconciliationListItem(BaseModel):
    id: int
    bank_movement_id: int
    reconciliation_type: str
    confidence_score: Optional[float] = None
    reconciliation_date: datetime
    notes: Optional[str] = None
    status: str
    user_id: int
    bank_movement: Dict[str, Any]
    accounting_movements_count: int

class ReconciliationListResponse(BaseModel):
    reconciliations: List[ReconciliationListItem]
    total: int
    limit: int
    offset: int

class UnmatchedMovementsResponse(BaseModel):
    bank_movements: List[Dict[str, Any]]
    accounting_movements: List[Dict[str, Any]]
    total_bank_movements: int
    total_accounting_movements: int
    pagination: Dict[str, int]

class MovementDetail(BaseModel):
    type: str  # "bank" o "accounting"
    id: int
    data: Dict[str, Any]

class MatchSuggestionDetail(BaseModel):
    accounting_movement: Dict[str, Any]
    bank_movement: Dict[str, Any]
    confidence_score: float
    criteria_matched: List[str]
    date_difference: int
    amount_difference: float
    reference_similarity: float

class MatchSuggestionsResponse(BaseModel):
    bank_movement_id: int
    suggestions: List[MatchSuggestionDetail]

# Schemas para generación automática de ajustes
class AdjustmentEntry(BaseModel):
    account_id: int
    account_code: str
    account_name: str
    debit: float
    credit: float
    description: str

class AdjustmentProposal(BaseModel):
    bank_movement_id: int
    bank_movement: Dict[str, Any]
    adjustment_type: str
    adjustment_description: str
    total_amount: float
    entries: List[AdjustmentEntry]
    document_concept: str
    requires_approval: bool

class AdjustmentPreview(BaseModel):
    bank_account_id: int
    period: Dict[str, Optional[str]]
    summary: Dict[str, Any]
    adjustments: List[AdjustmentProposal]
    requires_approval: bool

class AdjustmentResult(BaseModel):
    bank_movement_id: int
    success: bool
    document_id: Optional[int] = None
    document_number: Optional[str] = None
    adjustment_type: Optional[str] = None
    amount: Optional[float] = None
    error: Optional[str] = None

class AdjustmentApplicationResponse(BaseModel):
    total_processed: int
    total_successful: int
    total_failed: int
    results: List[AdjustmentResult]

class AdjustmentType(BaseModel):
    code: str
    name: str
    description: str
    account_type: str

class AdjustmentTypesResponse(BaseModel):
    adjustment_types: List[AdjustmentType]

class SingleAdjustmentPreview(BaseModel):
    bank_movement_id: int
    adjustment_detected: bool
    adjustment: Optional[AdjustmentProposal] = None
    message: Optional[str] = None

class AdjustmentDetectionResponse(BaseModel):
    bank_account_id: int
    total_movements_analyzed: int
    adjustments_detected: int
    adjustments: List[AdjustmentProposal]

class AdjustmentHistoryItem(BaseModel):
    id: int
    transaction_date: date
    amount: float
    description: str
    reference: Optional[str] = None
    bank_account_id: int
    status: str
    created_at: datetime

class AdjustmentHistoryResponse(BaseModel):
    adjustments: List[AdjustmentHistoryItem]
    total: int
    limit: int
    offset: int