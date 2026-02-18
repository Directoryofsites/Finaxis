
from sqlalchemy import text
from app.core.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_auto_migrations():
    """
    Ejecuta migraciones automáticas simples al iniciar la aplicación.
    Específicamente verifica y añade columnas faltantes en tablas clave.
    """
    logger.info("Iniciando auto-migraciones de esquema...")
    
    try:
        with engine.begin() as connection:
            # MIGRACIÓN 1: Añadir factura_rango_id a configuracion_fe
            try:
                # Verificar si la columna existe
                # Consulta compatible con PostgreSQL y SQLite (aunque la tabla schema es de PG)
                check_sql = text("SELECT column_name FROM information_schema.columns WHERE table_name='configuracion_fe' AND column_name='factura_rango_id';")
                
                # Intentamos ejecutar, si falla (ej: SQLite no tiene info_schema), intentamos fallback o ignoramos
                try:
                    result = connection.execute(check_sql).fetchone()
                    column_exists = result is not None
                except Exception:
                    # Fallback simple para SQLite o si falla la anterior
                    logger.warning("No se pudo verificar vía information_schema, intentando método alternativo.")
                    column_exists = False
                    # Podríamos hacer un query de prueba 'SELECT factura_rango_id FROM configuracion_fe LIMIT 0'
                    try:
                        connection.execute(text("SELECT factura_rango_id FROM configuracion_fe LIMIT 0"))
                        column_exists = True
                    except Exception:
                        column_exists = False
                
                if not column_exists:
                    logger.info("Columna 'factura_rango_id' no encontrada. Creándola...")
                    add_column_sql = text("ALTER TABLE configuracion_fe ADD COLUMN factura_rango_id INTEGER;")
                    connection.execute(add_column_sql)
                    logger.info("Columna 'factura_rango_id' añadida exitosamente.")
                else:
                    logger.info("Columna 'factura_rango_id' ya existe o fue detectada.")

                # MIGRACIÓN 2: Columnas de Lite Mode en empresas
                columns_to_add = [
                    ("is_lite_mode", "BOOLEAN DEFAULT FALSE"),
                    ("saldo_facturas_venta", "INTEGER DEFAULT 0"),
                    ("saldo_documentos_soporte", "INTEGER DEFAULT 0"),
                    ("saldo_notas_credito", "INTEGER DEFAULT 0"),
                    ("fecha_vencimiento_plan", "DATE")
                ]

                for col_name, col_type in columns_to_add:
                    try:
                        # Verificación rápida
                        connection.execute(text(f"SELECT {col_name} FROM empresas LIMIT 0"))
                    except Exception:
                        logger.info(f"Columna '{col_name}' no encontrada en 'empresas'. Creándola...")
                        # NOTA: En Postgres, Boolean se añade así. Si es SQLite (local), también.
                        # Para evitar errores de nullable sin default en columnas existentes:
                        cmd = f"ALTER TABLE empresas ADD COLUMN {col_name} {col_type};"
                        connection.execute(text(cmd))
                        logger.info(f"Columna '{col_name}' añadida exitosamente.")
                    
            except Exception as e:
                logger.error(f"Error específico en migraciones: {e}")
                
    except Exception as e:
        logger.error(f"CRÍTICO: Error al conectar para auto-migraciones: {e}")
            
    logger.info("Auto-migraciones finalizadas.")
