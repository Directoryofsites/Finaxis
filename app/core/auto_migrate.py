
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
    
    with engine.connect() as connection:
        # MIGRACIÓN 1: Añadir factura_rango_id a configuracion_fe
        try:
            # Verificar si la columna existe en Postgres
            # Nota: Esta consulta es específica para PostgreSQL, que es lo que se usa en Render usualmente
            # Si se usa SQLite localmente, puede fallar o necesitar ajuste.
            
            check_sql = text("SELECT column_name FROM information_schema.columns WHERE table_name='configuracion_fe' AND column_name='factura_rango_id';")
            result = connection.execute(check_sql).fetchone()
            
            if not result:
                logger.info("Columna 'factura_rango_id' no encontrada. Creándola...")
                # Intentamos añadir la columna
                # En SQLite 'ALTER TABLE ... ADD COLUMN ...' es soportado
                # En Postgres también.
                add_column_sql = text("ALTER TABLE configuracion_fe ADD COLUMN factura_rango_id INTEGER;")
                connection.execute(add_column_sql)
                connection.commit()
                logger.info("Columna 'factura_rango_id' añadida exitosamente.")
            else:
                logger.info("Columna 'factura_rango_id' ya existe. Omitiendo.")
                
        except Exception as e:
            logger.error(f"Error durante la migración de factura_rango_id: {e}")
            # No relanzamos para no detener el arranque, pero logueamos fuerte
            
    logger.info("Auto-migraciones finalizadas.")
