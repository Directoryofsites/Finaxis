# Contenido COMPLETO para: alembic/versions/09abbc450ae9_asignar_permiso_super_informe_.py

from alembic import op
import sqlalchemy as sa
from typing import Sequence, Union

# --- NO CAMBIES ESTAS LÍNEAS ---
# Identificadores de revisión, generados automáticamente por Alembic.
revision: str = '09abbc450ae9' # ID de este archivo
# ID del archivo anterior (la migración 'merge' que hicimos)
down_revision: Union[str, Sequence[str], None] = 'd95a5034a124'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
# --- FIN DE LÍNEAS AUTOMÁTICAS ---


# --- NOMBRES CLAVE PARA LA MIGRACIÓN ---
nombre_permiso = 'inventario:ver_super_informe'
roles_a_asignar = ['administrador', 'soporte']
# --- FIN NOMBRES CLAVE ---


def upgrade() -> None:
    # ### Comandos auto-generados por Alembic - Puedes ignorar esta línea ###
    # op.add_column('usuarios', sa.Column('nueva_columna_ejemplo', sa.String(), nullable=True))
    # ### Fin comandos auto-generados ###

    # --- INICIO: Lógica de Migración de Datos ---
    print(f"INFO: Asegurando que el permiso '{nombre_permiso}' exista...")
    # 1. Crear el permiso si no existe
    op.execute(f"""
        INSERT INTO permisos (nombre, descripcion)
        VALUES ('{nombre_permiso}', 'Permite ver y usar el Super Informe de Inventarios.')
        ON CONFLICT (nombre) DO NOTHING;
    """)
    print("INFO: Permiso asegurado.")

    print(f"INFO: Asignando permiso '{nombre_permiso}' a los roles: {roles_a_asignar}...")
    # 2. Asignar el permiso a los roles
    # Usamos un bucle para manejar múltiples roles de forma limpia
    for nombre_rol in roles_a_asignar:
        op.execute(f"""
            INSERT INTO rol_permisos (rol_id, permiso_id)
            SELECT r.id, p.id
            FROM roles r, permisos p
            WHERE r.nombre = '{nombre_rol}' AND p.nombre = '{nombre_permiso}'
            ON CONFLICT (rol_id, permiso_id) DO NOTHING;
        """)
    
    print(f"INFO: Permisos asignados a los roles {roles_a_asignar}.")
    # --- FIN: Lógica de Migración de Datos ---


def downgrade() -> None:
    # ### Comandos auto-generados por Alembic - Puedes ignorar esta línea ###
    # op.drop_column('usuarios', 'nueva_columna_ejemplo')
    # ### Fin comandos auto-generados ###

    # --- INICIO: Lógica para Revertir ---
    print(f"INFO: Desasignando permiso '{nombre_permiso}' de los roles: {roles_a_asignar}...")
    # Eliminar las asignaciones
    for nombre_rol in roles_a_asignar:
        op.execute(f"""
            DELETE FROM rol_permisos
            WHERE rol_id = (SELECT id FROM roles WHERE nombre = '{nombre_rol}')
              AND permiso_id = (SELECT id FROM permisos WHERE nombre = '{nombre_permiso}');
        """)
    
    print(f"INFO: Permiso desasignado de los roles {roles_a_asignar}.")
    
    # NOTA: No eliminamos el permiso en sí mismo en el downgrade,
    # solo la asignación, para evitar borrar datos si otro rol lo usa.
    # --- FIN: Lógica para Revertir ---