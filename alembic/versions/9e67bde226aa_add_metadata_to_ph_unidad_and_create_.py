"""add_metadata_to_ph_unidad_and_create_custom_fields

Revision ID: 9e67bde226aa
Revises: 1aaa70741648
Create Date: 2026-05-02 20:25:28.418738

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9e67bde226aa'
down_revision: Union[str, Sequence[str], None] = '1aaa70741648'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Agregar columna metadatos_extra a ph_unidades
    # Usamos execute para manejar el IF NOT EXISTS si es necesario, 
    # o simplemente op.add_column si confiamos en la migración limpia.
    op.add_column('ph_unidades', sa.Column('metadatos_extra', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True))
    
    # 2. Crear tabla ph_campos_personalizados
    op.create_table(
        'ph_campos_personalizados',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('entidad', sa.String(length=50), nullable=False),
        sa.Column('etiqueta', sa.String(length=100), nullable=False),
        sa.Column('llave_json', sa.String(length=100), nullable=False),
        sa.Column('tipo', sa.String(length=50), nullable=True),
        sa.Column('obligatorio', sa.Boolean(), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ph_campos_personalizados_id'), 'ph_campos_personalizados', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ph_campos_personalizados_id'), table_name='ph_campos_personalizados')
    op.drop_table('ph_campos_personalizados')
    op.drop_column('ph_unidades', 'metadatos_extra')
