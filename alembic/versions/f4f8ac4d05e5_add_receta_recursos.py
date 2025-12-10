"""add_receta_recursos

Revision ID: f4f8ac4d05e5
Revises: eb62423b7491
Create Date: 2025-12-09 21:53:03.251380

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4f8ac4d05e5'
down_revision: Union[str, Sequence[str], None] = 'eb62423b7491'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('receta_recursos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('receta_id', sa.Integer(), nullable=False),
    sa.Column('descripcion', sa.String(length=255), nullable=False),
    sa.Column('tipo', sa.String(length=50), nullable=False),
    sa.Column('costo_estimado', sa.Float(), nullable=False),
    sa.Column('cuenta_contable_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['cuenta_contable_id'], ['plan_cuentas.id'], ),
    sa.ForeignKeyConstraint(['receta_id'], ['recetas.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_receta_recursos_id'), 'receta_recursos', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_receta_recursos_id'), table_name='receta_recursos')
    op.drop_table('receta_recursos')
