"""Asignar permisos faltantes para el rol administrador

Revision ID: [EL_NUEVO_ID_QUE_SE_GENERO]
Revises: 86597980417b
Create Date: 2025-10-14 22:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, Integer, and_

# revision identifiers, used by Alembic.
# IMPORTANTE: Reemplaza 'EL_NUEVO_ID_QUE_SE_GENERO' con el ID del nombre de este archivo.
revision = 'fba737e70af0'
down_revision = '86597980417b' # <-- Apunta a la migración inicial correcta.
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Definición de las tablas para manipulación de datos ---
    roles_table = table('roles', column('id', Integer), column('nombre', String))
    permisos_table = table('permisos', column('id', Integer), column('nombre', String))
    rol_permisos_table = table('rol_permisos', column('rol_id', Integer), column('permiso_id', Integer))

    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)

    # Lista de permisos que el rol 'administrador' debe tener
    permisos_requeridos = [
        'utilidades:migracion',
        'inventario:ver_reportes'
    ]

    try:
        # --- Obtener el ID del rol 'administrador' ---
        rol_admin = session.execute(sa.select(roles_table).where(roles_table.c.nombre == 'administrador')).fetchone()
        
        if not rol_admin:
            print("ADVERTENCIA: No se encontró el rol 'administrador'. Abortando asignación de permisos.")
            return

        rol_admin_id = rol_admin.id

        for permiso_nombre in permisos_requeridos:
            # --- Asegurar que el permiso exista ---
            permiso = session.execute(sa.select(permisos_table).where(permisos_table.c.nombre == permiso_nombre)).fetchone()
            
            if not permiso:
                print(f"Creando permiso faltante: '{permiso_nombre}'")
                op.bulk_insert(permisos_table, [{'nombre': permiso_nombre, 'descripcion': f'Permiso para {permiso_nombre}'}])
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
                print(f"Asignando permiso '{permiso_nombre}' al rol 'administrador'.")
                op.bulk_insert(rol_permisos_table, [{'rol_id': rol_admin_id, 'permiso_id': permiso_id}])
            else:
                print(f"El rol 'administrador' ya tiene el permiso '{permiso_nombre}'. No se requiere acción.")

    finally:
        session.close()


def downgrade() -> None:
    # --- Comandos para revertir los cambios ---
    op.execute("""
        DELETE FROM rol_permisos
        WHERE rol_id = (SELECT id FROM roles WHERE nombre = 'administrador')
        AND permiso_id IN (
            SELECT id FROM permisos WHERE nombre IN ('utilidades:migracion', 'inventario:ver_reportes')
        );
    """)