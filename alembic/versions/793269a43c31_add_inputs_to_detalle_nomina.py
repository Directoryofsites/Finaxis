"""add_inputs_to_detalle_nomina

Revision ID: 793269a43c31
Revises: b222d60e2c01
Create Date: 2025-12-16 12:19:09.663963

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '793269a43c31'
down_revision: Union[str, Sequence[str], None] = 'b222d60e2c01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('nomina_detalles', sa.Column('otros_devengados', sa.Numeric(precision=18, scale=2), nullable=True))
    op.add_column('nomina_detalles', sa.Column('otras_deducciones', sa.Numeric(precision=18, scale=2), nullable=True))

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('nomina_detalles', 'otras_deducciones')
    op.drop_column('nomina_detalles', 'otros_devengados')
