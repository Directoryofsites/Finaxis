"""add_otras_cuentas_nomina

Revision ID: b222d60e2c01
Revises: e6b8737374b6
Create Date: 2025-12-16 12:09:11.655921

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b222d60e2c01'
down_revision: Union[str, Sequence[str], None] = 'e6b8737374b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('nomina_configuracion', sa.Column('cuenta_otros_devengados_id', sa.Integer(), nullable=True))
    op.add_column('nomina_configuracion', sa.Column('cuenta_otras_deducciones_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'nomina_configuracion', 'plan_cuentas', ['cuenta_otras_deducciones_id'], ['id'])
    op.create_foreign_key(None, 'nomina_configuracion', 'plan_cuentas', ['cuenta_otros_devengados_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(None, 'nomina_configuracion', type_='foreignkey')
    op.drop_constraint(None, 'nomina_configuracion', type_='foreignkey')
    op.drop_column('nomina_configuracion', 'cuenta_otras_deducciones_id')
    op.drop_column('nomina_configuracion', 'cuenta_otros_devengados_id')
