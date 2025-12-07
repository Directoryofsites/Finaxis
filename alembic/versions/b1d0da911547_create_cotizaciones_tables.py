"""create_cotizaciones_tables

Revision ID: b1d0da911547
Revises: bce4561eaa4a
Create Date: 2025-12-06 19:05:03.677779

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1d0da911547'
down_revision: Union[str, Sequence[str], None] = 'bce4561eaa4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Crear tabla 'cotizaciones'
    op.create_table('cotizaciones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('numero', sa.Integer(), nullable=False),
        sa.Column('fecha', sa.Date(), nullable=False),
        sa.Column('fecha_vencimiento', sa.Date(), nullable=True),
        sa.Column('tercero_id', sa.Integer(), nullable=True),
        sa.Column('bodega_id', sa.Integer(), nullable=True),
        sa.Column('usuario_id', sa.Integer(), nullable=True),
        sa.Column('estado', sa.String(length=20), nullable=False, server_default='BORRADOR'),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.Column('total_estimado', sa.Float(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ),
        sa.ForeignKeyConstraint(['tercero_id'], ['terceros.id'], ),
        sa.ForeignKeyConstraint(['bodega_id'], ['bodegas.id'], ),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], )
    )
    op.create_index(op.f('ix_cotizaciones_id'), 'cotizaciones', ['id'], unique=False)

    # 2. Crear tabla 'cotizaciones_detalles'
    op.create_table('cotizaciones_detalles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cotizacion_id', sa.Integer(), nullable=False),
        sa.Column('producto_id', sa.Integer(), nullable=False),
        sa.Column('cantidad', sa.Float(), nullable=False),
        sa.Column('precio_unitario', sa.Float(), nullable=True, server_default='0'),
        sa.Column('cantidad_facturada', sa.Float(), nullable=True, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['cotizacion_id'], ['cotizaciones.id'], ondelete='CASCADE'), # Cascade para limpiar detalles si borran la cabecera
        sa.ForeignKeyConstraint(['producto_id'], ['productos.id'], )
    )
    op.create_index(op.f('ix_cotizaciones_detalles_id'), 'cotizaciones_detalles', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_cotizaciones_detalles_id'), table_name='cotizaciones_detalles')
    op.drop_table('cotizaciones_detalles')
    op.drop_index(op.f('ix_cotizaciones_id'), table_name='cotizaciones')
    op.drop_table('cotizaciones')
