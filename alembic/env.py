# alembic/env.py (Versión Corregida y Final)

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# --- INICIO DE LA CIRUGÍA ARQUITECTÓNICA ---
# Se asegura que la raíz del proyecto esté en el path de Python
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

# Se importa la Base declarativa de la aplicación
from app.core.database import Base

# Se importan TODOS los modelos para que Alembic los "vea" y pueda
# detectar automáticamente los cambios en la estructura de la base de datos.
# Esta era la pieza que faltaba.
from app.models import (
    Usuario,
    Empresa,
    Tercero,
    PlanCuenta,
    TipoDocumento,
    CentroCosto,
    PlantillaMaestra,
    PlantillaDetalle,
    ConceptoFavorito,
    Documento,
    DocumentoEliminado,
    MovimientoContable,
    MovimientoEliminado,
    LogOperacion,
    PeriodoContableCerrado,
    FormatoImpresion,
    AplicacionPago,
    # Modelos de Permisos
    Rol,
    Permiso,
    UsuarioPermisoExcepcion,
    # Modelos de Inventario
    Bodega,
    GrupoInventario,
    TasaImpuesto,
    Producto,
    StockBodega,
    MovimientoInventario,
    # Cotizaciones
    Cotizacion,
    CotizacionDetalle,
    # Activos Fijos
    ActivoCategoria,
    ActivoFijo,
    ActivoCategoria,
    ActivoFijo,
    ActivoNovedad
)
from app.models.usuario_busqueda import UsuarioBusqueda 
from app.models.nomina import Empleado, Nomina, DetalleNomina, ConfiguracionNomina
from app.models.consumo_registros import ControlPlanMensual, BolsaExcedente, RecargaAdicional, HistorialConsumo
# --- FIN DE LA CIRUGÍA ARQUITECTÓNICA ---


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Se le dice a Alembic que el "objetivo" es el metadata de nuestra Base.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()