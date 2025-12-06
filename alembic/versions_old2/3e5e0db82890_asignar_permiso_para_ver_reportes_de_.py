"""Asignar permiso para ver reportes de inventario al rol admin

Revision ID: 3e5e0db82890
Revises: fba737e70af0
Create Date: 2025-10-15 10:29:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, Integer, and_

# revision identifiers, used by Alembic.
revision = '3e5e0db82890'
down_revision = 'fba737e70af0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Definición de las tablas para manipulación de datos ---
    roles_table = table('roles', column('id', Integer), column('nombre', String))
    permisos_table = table('permisos', column('id', Integer), column('nombre', String))
    rol_permisos_table = table('rol_permisos', column('rol_id', Integer), column('permiso_id', Integer))

    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)

    permiso_nombre = 'inventario:ver_reportes'
    rol_nombre = 'administrador'

    try:
        # --- Obtener el ID del rol 'administrador' ---
        rol_admin = session.execute(sa.select(roles_table).where(roles_table.c.nombre == rol_nombre)).fetchone()
        
        if not rol_admin:
            print(f"ADVERTENCIA: No se encontró el rol '{rol_nombre}'. Abortando asignación de permisos.")
            return

        rol_admin_id = rol_admin.id

        # --- Asegurar que el permiso exista ---
        permiso = session.execute(sa.select(permisos_table).where(permisos_table.c.nombre == permiso_nombre)).fetchone()
        
        if not permiso:
            print(f"Creando permiso faltante: '{permiso_nombre}'")
            op.bulk_insert(permisos_table, [{'nombre': permiso_nombre, 'descripcion': 'Permite ver los reportes del módulo de inventarios.'}])
            permiso_id = session.execute(sa.select(permisos_table.c.id).where(permisos_table.c.nombre == permiso_nombre)).scalar_one()
        else:
            permiso_id = permiso.id

        # --- Asignar el permiso al rol si no lo tiene ya ---
        vinculo_existente = session.execute(
            sa.select(rol_permisos_table).where(
                and_(rol_permisos_table.c.rol_id == rol_admin_id, rol_permisos_table.c.permiso_id == permiso_id)
            )
        ).first()

        if not vinculo_existente:
            print(f"Asignando permiso '{permiso_nombre}' al rol '{rol_nombre}'.")
            op.bulk_insert(rol_permisos_table, [{'rol_id': rol_admin_id, 'permiso_id': permiso_id}])
        else:
            print(f"El rol '{rol_nombre}' ya tiene el permiso '{permiso_nombre}'. No se requiere acción.")

    finally:
        session.close()


def downgrade() -> None:
    # --- Comandos para revertir los cambios ---
    op.execute("""
        DELETE FROM rol_permisos
        WHERE rol_id = (SELECT id FROM roles WHERE nombre = 'administrador')
        AND permiso_id = (SELECT id FROM permisos WHERE nombre = 'inventario:ver_reportes');
    """)