"""Unificar cabezas de migracion eliminar producto

Revision ID: d95a5034a124
Revises: b06ab1195ff2, cf3013120956
Create Date: 2025-10-24 13:42:53.985450

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd95a5034a124'
down_revision: Union[str, Sequence[str], None] = ('b06ab1195ff2', 'cf3013120956')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
