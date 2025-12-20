"""merge_kiro_and_main

Revision ID: f7addb49d1cc
Revises: bank_reconciliation_001, db2267ce7084
Create Date: 2025-12-19 00:08:28.062405

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7addb49d1cc'
down_revision: Union[str, Sequence[str], None] = ('bank_reconciliation_001', 'db2267ce7084')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
