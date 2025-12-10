"""add_tipo_nomina_model

Revision ID: b481fb0e2488
Revises: f4f8ac4d05e5
Create Date: 2025-12-09 22:23:16.172939

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b481fb0e2488'
down_revision: Union[str, Sequence[str], None] = 'f4f8ac4d05e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create nomina_tipos table - SKIPPED (Already exists)
    # op.create_table('nomina_tipos',
    #     sa.Column('id', sa.Integer(), nullable=False),
    #     sa.Column('empresa_id', sa.Integer(), nullable=True),
    #     sa.Column('nombre', sa.String(length=100), nullable=False),
    #     sa.Column('descripcion', sa.String(length=255), nullable=True),
    #     sa.Column('periodo_pago', postgresql.ENUM('MENSUAL', 'QUINCENAL', name='periodopago', create_type=False), nullable=True),
    #     sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ),
    #     sa.PrimaryKeyConstraint('id')
    # )
    # op.create_index(op.f('ix_nomina_tipos_id'), 'nomina_tipos', ['id'], unique=False)

    # Add tipo_nomina_id to nomina_empleados
    op.add_column('nomina_empleados', sa.Column('tipo_nomina_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'nomina_empleados', 'nomina_tipos', ['tipo_nomina_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(None, 'nomina_empleados', type_='foreignkey')
    op.drop_column('nomina_empleados', 'tipo_nomina_id')
    op.drop_index(op.f('ix_nomina_tipos_id'), table_name='nomina_tipos')
    op.drop_table('nomina_tipos')
