"""add_2fa_to_usuarios

Revision ID: 1aaa70741648
Revises: ee1ef08d68c0
Create Date: 2026-04-29 20:08:52.716942

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '1aaa70741648'
down_revision: Union[str, Sequence[str], None] = 'ee1ef08d68c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Añadimos las columnas a la tabla usuarios
    # Usamos batch_op para mayor compatibilidad
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.add_column(sa.Column('totp_secret', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('totp_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')))

def downgrade() -> None:
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.drop_column('totp_enabled')
        batch_op.drop_column('totp_secret')
