"""Expandir límite de favoritos a 24 posiciones

Revision ID: expand_favoritos_24
Revises: [previous_revision]
Create Date: 2024-12-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'expand_favoritos_24'
down_revision = '9e25fe660694'  # Conectar con la migración más reciente
branch_labels = None
depends_on = None

def upgrade():
    """
    Actualiza la base de datos para soportar hasta 24 favoritos por usuario.
    No se requieren cambios en la estructura de la tabla, solo actualizar
    las validaciones del lado de la aplicación.
    """
    # La tabla usuarios_favoritos ya soporta cualquier valor en el campo 'orden'
    # Solo necesitamos asegurar que no hay restricciones de CHECK que limiten el valor
    pass

def downgrade():
    """
    Revierte los cambios si es necesario.
    """
    # No hay cambios estructurales que revertir
    pass