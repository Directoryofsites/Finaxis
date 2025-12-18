"""add_documento_contable_link_to_nomina

Revision ID: e6b8737374b6
Revises: expand_favoritos_24
Create Date: 2025-12-16 10:43:20.692699

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6b8737374b6'
down_revision: Union[str, Sequence[str], None] = 'expand_favoritos_24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('nomina_detalles', sa.Column('documento_contable_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'nomina_detalles', 'documentos', ['documento_contable_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(None, 'nomina_detalles', type_='foreignkey')
    op.drop_column('nomina_detalles', 'documento_contable_id')
