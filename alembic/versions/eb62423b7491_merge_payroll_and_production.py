"""merge_payroll_and_production

Revision ID: eb62423b7491
Revises: 10a7f6e76b82, bab916791fb8
Create Date: 2025-12-09 21:18:01.950276

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eb62423b7491'
down_revision: Union[str, Sequence[str], None] = ('10a7f6e76b82', 'bab916791fb8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
