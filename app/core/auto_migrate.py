
from sqlalchemy import text
from app.core.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_auto_migrations():
    """
    Ejecuta migraciones automáticas simples al iniciar la aplicación.
    Verifica y añade columnas faltantes en tablas clave (empresas y configuracion_fe).
    """
    logger.info("Iniciando auto-migraciones de esquema...")
    
    try:
        # Usamos una conexión limpia para inspeccionar
        with engine.connect() as connection:
            
            # 1. Obtener todas las columnas existentes en las tablas objetivo
            # Esto evita errores de 'transaction aborted' al intentar SELECTs de columnas inexistentes
            def get_existing_columns(table_name):
                sql = text("SELECT column_name FROM information_schema.columns WHERE table_name = :t")
                try:
                    res = connection.execute(sql, {"t": table_name}).fetchall()
                    return {row[0].lower() for row in res}
                except Exception:
                    # Fallback para SQLite o si fallara info_schema
                    return set()

            cols_config_fe = get_existing_columns('configuracion_fe')
            cols_empresas = get_existing_columns('empresas')
            cols_productos = get_existing_columns('productos')
            cols_stock_bodegas = get_existing_columns('stock_bodegas')
            cols_grupos = get_existing_columns('grupos_inventario')
            cols_tasas = get_existing_columns('tasas_impuesto')
            
            # 2. Definir migraciones pendientes
            migrations = []
            
            # configuracion_fe
            if 'factura_rango_id' not in cols_config_fe:
                migrations.append(('configuracion_fe', 'factura_rango_id', 'INTEGER'))
                
            # empresas (is_lite_mode and friends)
            empresa_lite_cols = [
                ("is_lite_mode", "BOOLEAN DEFAULT FALSE"),
                ("saldo_facturas_venta", "INTEGER DEFAULT 0"),
                ("saldo_documentos_soporte", "INTEGER DEFAULT 0"),
                ("saldo_notas_credito", "INTEGER DEFAULT 0"),
                ("fecha_vencimiento_plan", "DATE")
            ]
            for col, col_type in empresa_lite_cols:
                if col not in cols_empresas:
                    migrations.append(('empresas', col, col_type))

            # productos
            producto_cols = [
                ("controlar_inventario", "BOOLEAN DEFAULT TRUE"),
                ("precio_base_manual", "FLOAT"),
                ("impuesto_iva_id", "INTEGER")
            ]
            for col, col_type in producto_cols:
                if col not in cols_productos:
                    migrations.append(('productos', col, col_type))

            # stock_bodegas
            if 'stock_comprometido' not in cols_stock_bodegas:
                migrations.append(('stock_bodegas', 'stock_comprometido', 'FLOAT DEFAULT 0.0'))

            # grupos_inventario
            grupo_cols = [
                ("cuenta_costo_produccion_id", "INTEGER"),
                ("impuesto_predeterminado_id", "INTEGER")
            ]
            for col, col_type in grupo_cols:
                if col not in cols_grupos:
                    migrations.append(('grupos_inventario', col, col_type))

            # tasas_impuesto
            tasa_cols = [
                ("cuenta_id", "INTEGER"),
                ("cuenta_iva_descontable_id", "INTEGER")
            ]
            for col, col_type in tasa_cols:
                if col not in cols_tasas:
                    migrations.append(('tasas_impuesto', col, col_type))

            # 3. Ejecutar migraciones en un bloque BEGIN/COMMIT
            if migrations:
                with engine.begin() as trans_conn:
                    for table, col, col_type in migrations:
                        logger.info(f"Migrando: Añadiendo {col} a {table}...")
                        trans_conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                        logger.info(f"Columna {col} añadida con éxito.")
            else:
                logger.info("No se requieren migraciones de esquema pendientes.")
                
    except Exception as e:
        logger.error(f"Error crítico en auto-migraciones: {e}")
            
    logger.info("Auto-migraciones finalizadas.")
