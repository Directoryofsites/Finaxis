# Contenido COMPLETO para: alembic/versions/cf3013120956_asignar_permiso_eliminar_producto_a_rol_.py

from alembic import op
import sqlalchemy as sa
# Importa 'Sequence' y 'Union' si no están ya importados
from typing import Sequence, Union

# --- NO CAMBIES ESTAS LÍNEAS ---
# Identificadores de revisión, generados automáticamente por Alembic.
revision: str = 'cf3013120956' # ID de este archivo
# ID del archivo anterior, extraído de d1f651b78451_implementar_nueva_arquitectura_.py
down_revision: Union[str, Sequence[str], None] = 'd1f651b78451'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
# --- FIN DE LÍNEAS AUTOMÁTICAS ---


# --- NOMBRES CLAVE PARA LA MIGRACIÓN ---
nombre_permiso = 'inventario:eliminar_producto'
nombre_rol = 'administrador'
# --- FIN NOMBRES CLAVE ---


def upgrade() -> None:
    # ### Comandos auto-generados por Alembic - Puedes ignorar esta línea ###
    # op.add_column('usuarios', sa.Column('nueva_columna_ejemplo', sa.String(), nullable=True)) # Ejemplo Alembic
    # ### Fin comandos auto-generados ###

    # --- INICIO: Lógica de Migración de Datos ---
    print(f"INFO: Asegurando que el permiso '{nombre_permiso}' exista...")
    # 1. Crear el permiso si no existe (seguro contra ejecuciones repetidas)
    op.execute(f"""
        INSERT INTO permisos (nombre, descripcion)
        VALUES ('{nombre_permiso}', 'Permite eliminar productos del inventario.')
        ON CONFLICT (nombre) DO NOTHING;
    """)
    print("INFO: Permiso asegurado.")

    print(f"INFO: Asignando permiso '{nombre_permiso}' al rol '{nombre_rol}'...")
    # 2. Asignar el permiso al rol (seguro contra ejecuciones repetidas)
    #    Obtenemos los IDs dinámicamente para evitar hardcodearlos
    op.execute(f"""
        INSERT INTO rol_permisos (rol_id, permiso_id)
        SELECT r.id, p.id
        FROM roles r, permisos p
        WHERE r.nombre = '{nombre_rol}' AND p.nombre = '{nombre_permiso}'
        ON CONFLICT (rol_id, permiso_id) DO NOTHING;
    """)
    print("INFO: Permiso asignado.")
    # --- FIN: Lógica de Migración de Datos ---


def downgrade() -> None:
    # ### Comandos auto-generados por Alembic - Puedes ignorar esta línea ###
    # op.drop_column('usuarios', 'nueva_columna_ejemplo') # Ejemplo Alembic
    # ### Fin comandos auto-generados ###

    # --- INICIO: Lógica para Revertir (Opcional pero recomendado) ---
    print(f"INFO: Desasignando permiso '{nombre_permiso}' del rol '{nombre_rol}'...")
    # Eliminar la asignación entre el rol y el permiso
    op.execute(f"""
        DELETE FROM rol_permisos
        WHERE rol_id = (SELECT id FROM roles WHERE nombre = '{nombre_rol}')
          AND permiso_id = (SELECT id FROM permisos WHERE nombre = '{nombre_permiso}');
    """)
    print("INFO: Permiso desasignado.")

    # Opcional: Eliminar el permiso si sabes que fue creado aquí.
    # Es más seguro no eliminarlo automáticamente para evitar problemas si
    # otros roles lo usan. Se deja comentado como referencia.
    # print(f"INFO: Eliminando permiso '{nombre_permiso}'...")
    # op.execute(f"""
    #     DELETE FROM permisos WHERE nombre = '{nombre_permiso}';
    # """)
    # print("INFO: Permiso eliminado.")
    # --- FIN: Lógica para Revertir ---