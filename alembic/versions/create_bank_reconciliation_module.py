"""Create bank reconciliation module tables and columns

Revision ID: bank_reconciliation_001
Revises: f596acd9b6b3
Create Date: 2025-12-17 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'bank_reconciliation_001'
down_revision: Union[str, Sequence[str], None] = 'f596acd9b6b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    # Add new columns to existing tables
    op.add_column('plan_cuentas', sa.Column('is_bank_reconciliation_account', sa.Boolean(), nullable=True, default=False))
    op.add_column('documentos', sa.Column('reconciliation_reference', sa.String(255), nullable=True))
    op.add_column('movimientos_contables', sa.Column('reconciliation_status', sa.String(50), nullable=True, default='UNRECONCILED'))
    
    # Create import_configs table
    op.create_table('import_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bank_id', sa.Integer(), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('file_format', sa.String(10), nullable=False),
        sa.Column('delimiter', sa.String(5), nullable=True, default=','),
        sa.Column('date_format', sa.String(20), nullable=True, default='%Y-%m-%d'),
        sa.Column('field_mapping', sa.JSON(), nullable=False),
        sa.Column('header_rows', sa.Integer(), nullable=True, default=1),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['bank_id'], ['terceros.id'], ),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['usuarios.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_import_configs_id'), 'import_configs', ['id'], unique=False)
    
    # Create import_sessions table
    op.create_table('import_sessions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('bank_account_id', sa.Integer(), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_hash', sa.String(64), nullable=False),
        sa.Column('import_config_id', sa.Integer(), nullable=False),
        sa.Column('total_movements', sa.Integer(), nullable=True, default=0),
        sa.Column('successful_imports', sa.Integer(), nullable=True, default=0),
        sa.Column('errors', sa.JSON(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('import_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True, default='PROCESSING'),
        sa.ForeignKeyConstraint(['bank_account_id'], ['plan_cuentas.id'], ),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ),
        sa.ForeignKeyConstraint(['import_config_id'], ['import_configs.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_import_sessions_id'), 'import_sessions', ['id'], unique=False)
    
    # Create bank_movements table
    op.create_table('bank_movements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('import_session_id', sa.String(36), nullable=False),
        sa.Column('bank_account_id', sa.Integer(), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('transaction_date', sa.Date(), nullable=False),
        sa.Column('value_date', sa.Date(), nullable=True),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('reference', sa.String(100), nullable=True),
        sa.Column('transaction_type', sa.String(50), nullable=True),
        sa.Column('balance', sa.Numeric(15, 2), nullable=True),
        sa.Column('status', sa.String(20), nullable=True, default='PENDING'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['import_session_id'], ['import_sessions.id'], ),
        sa.ForeignKeyConstraint(['bank_account_id'], ['plan_cuentas.id'], ),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bank_movements_id'), 'bank_movements', ['id'], unique=False)
    
    # Create reconciliations table
    op.create_table('reconciliations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bank_movement_id', sa.Integer(), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('reconciliation_type', sa.String(20), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('reconciliation_date', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True, default='ACTIVE'),
        sa.Column('confidence_score', sa.Numeric(5, 2), nullable=True),
        sa.ForeignKeyConstraint(['bank_movement_id'], ['bank_movements.id'], ),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reconciliations_id'), 'reconciliations', ['id'], unique=False)
    
    # Create reconciliation_movements table
    op.create_table('reconciliation_movements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reconciliation_id', sa.Integer(), nullable=False),
        sa.Column('accounting_movement_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['reconciliation_id'], ['reconciliations.id'], ),
        sa.ForeignKeyConstraint(['accounting_movement_id'], ['movimientos_contables.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reconciliation_movements_id'), 'reconciliation_movements', ['id'], unique=False)
    
    # Create accounting_configs table
    op.create_table('accounting_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bank_account_id', sa.Integer(), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('commission_account_id', sa.Integer(), nullable=True),
        sa.Column('interest_income_account_id', sa.Integer(), nullable=True),
        sa.Column('bank_charges_account_id', sa.Integer(), nullable=True),
        sa.Column('adjustment_account_id', sa.Integer(), nullable=True),
        sa.Column('default_cost_center_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['bank_account_id'], ['plan_cuentas.id'], ),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ),
        sa.ForeignKeyConstraint(['commission_account_id'], ['plan_cuentas.id'], ),
        sa.ForeignKeyConstraint(['interest_income_account_id'], ['plan_cuentas.id'], ),
        sa.ForeignKeyConstraint(['bank_charges_account_id'], ['plan_cuentas.id'], ),
        sa.ForeignKeyConstraint(['adjustment_account_id'], ['plan_cuentas.id'], ),
        sa.ForeignKeyConstraint(['default_cost_center_id'], ['centros_costo.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['usuarios.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_accounting_configs_id'), 'accounting_configs', ['id'], unique=False)
    
    # Create reconciliation_audits table
    op.create_table('reconciliation_audits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reconciliation_id', sa.Integer(), nullable=True),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('operation_type', sa.String(50), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('operation_date', sa.DateTime(), nullable=True),
        sa.Column('old_values', sa.JSON(), nullable=True),
        sa.Column('new_values', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['reconciliation_id'], ['reconciliations.id'], ),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reconciliation_audits_id'), 'reconciliation_audits', ['id'], unique=False)
    
    # Create indexes for better performance
    op.create_index('ix_bank_movements_transaction_date', 'bank_movements', ['transaction_date'])
    op.create_index('ix_bank_movements_amount', 'bank_movements', ['amount'])
    op.create_index('ix_bank_movements_status', 'bank_movements', ['status'])
    op.create_index('ix_reconciliations_type', 'reconciliations', ['reconciliation_type'])
    op.create_index('ix_reconciliations_status', 'reconciliations', ['status'])


def downgrade() -> None:
    """Downgrade schema."""
    
    # Drop indexes
    op.drop_index('ix_reconciliations_status', table_name='reconciliations')
    op.drop_index('ix_reconciliations_type', table_name='reconciliations')
    op.drop_index('ix_bank_movements_status', table_name='bank_movements')
    op.drop_index('ix_bank_movements_amount', table_name='bank_movements')
    op.drop_index('ix_bank_movements_transaction_date', table_name='bank_movements')
    
    # Drop tables in reverse order
    op.drop_index(op.f('ix_reconciliation_audits_id'), table_name='reconciliation_audits')
    op.drop_table('reconciliation_audits')
    
    op.drop_index(op.f('ix_accounting_configs_id'), table_name='accounting_configs')
    op.drop_table('accounting_configs')
    
    op.drop_index(op.f('ix_reconciliation_movements_id'), table_name='reconciliation_movements')
    op.drop_table('reconciliation_movements')
    
    op.drop_index(op.f('ix_reconciliations_id'), table_name='reconciliations')
    op.drop_table('reconciliations')
    
    op.drop_index(op.f('ix_bank_movements_id'), table_name='bank_movements')
    op.drop_table('bank_movements')
    
    op.drop_index(op.f('ix_import_sessions_id'), table_name='import_sessions')
    op.drop_table('import_sessions')
    
    op.drop_index(op.f('ix_import_configs_id'), table_name='import_configs')
    op.drop_table('import_configs')
    
    # Remove columns from existing tables
    op.drop_column('movimientos_contables', 'reconciliation_status')
    op.drop_column('documentos', 'reconciliation_reference')
    op.drop_column('plan_cuentas', 'is_bank_reconciliation_account')