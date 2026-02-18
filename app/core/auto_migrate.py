
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
                # Usamos LOWER(table_name) para mayor seguridad en PostgreSQL
                sql = text("SELECT column_name FROM information_schema.columns WHERE LOWER(table_name) = LOWER(:t)")
                try:
                    res = connection.execute(sql, {"t": table_name}).fetchall()
                    return {row[0].lower() for row in res}
                except Exception as e:
                    logger.warning(f"Error inspeccionando tabla {table_name}: {e}")
                    return set()

            cols_config_fe = get_existing_columns('configuracion_fe')
            cols_empresas = get_existing_columns('empresas')
            cols_productos = get_existing_columns('productos')
            cols_stock_bodegas = get_existing_columns('stock_bodegas')
            cols_grupos = get_existing_columns('grupos_inventario')
            cols_tasas = get_existing_columns('tasas_impuesto')
            cols_documentos = get_existing_columns('documentos')
            cols_terceros = get_existing_columns('terceros')
            
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

            # documentos (FACTURACIÓN ELECTRÓNICA Y OTROS)
            documento_cols = [
                ("dian_estado", "VARCHAR(20)"),
                ("dian_cufe", "VARCHAR(255)"),
                ("dian_xml_url", "VARCHAR(500)"),
                ("dian_error", "TEXT"),
                ("provider_id", "VARCHAR(255)"),
                ("reconciliation_reference", "VARCHAR(255)"),
                ("documento_referencia_id", "INTEGER"),
                ("descuento_global_valor", "NUMERIC(15, 2) DEFAULT 0"),
                ("cargos_globales_valor", "NUMERIC(15, 2) DEFAULT 0"),
                ("unidad_ph_id", "INTEGER")
            ]
            for col, col_type in documento_cols:
                if col not in cols_documentos:
                    migrations.append(('documentos', col, col_type))

            # terceros
            tercero_cols = [
                ("tipo_documento", "VARCHAR(5) DEFAULT '13'"),
                ("tipo_persona", "VARCHAR(1) DEFAULT '2'"),
                ("municipio_dane", "VARCHAR(10)"),
                ("codigo_postal", "VARCHAR(10)"),
                ("regimen_fiscal", "VARCHAR(5)"),
                ("responsabilidad_fiscal", "VARCHAR(20)"),
                ("lista_precio_id", "INTEGER")
            ]
            for col, col_type in tercero_cols:
                if col not in cols_terceros:
                    migrations.append(('terceros', col, col_type))

            # 3. Ejecutar migraciones en un bloque BEGIN/COMMIT
            if migrations:
                with engine.begin() as trans_conn:
                    for table, col, col_type in migrations:
                        logger.info(f"Migrando: Añadiendo {col} a {table}...")
                        try:
                            trans_conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                            logger.info(f"Columna {col} añadida con éxito.")
                        except Exception as e:
                            logger.error(f"Error añadiendo {col} a {table}: {e}")
            else:
                logger.info("No se requieren migraciones de esquema pendientes.")
                
    except Exception as e:
        logger.error(f"Error crítico en auto-migraciones: {e}")
            
    logger.info("Auto-migraciones finalizadas.")
