import logging
from sqlalchemy import create_engine, text, inspect
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_schema():
    engine = create_engine(settings.DATABASE_URL)
    
    logger.info("Checking 'empresas' table schema...")
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('empresas')]
    
    if 'modo_operacion' in columns:
        logger.info("Column 'modo_operacion' ALREADY EXISTS. No action needed.")
    else:
        logger.info("Column 'modo_operacion' MISSING. Adding it now...")
        try:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE empresas ADD COLUMN modo_operacion VARCHAR(50) DEFAULT 'STANDARD' NOT NULL"))
                conn.commit()
            logger.info("SUCCESS: Column 'modo_operacion' added successfully via raw SQL.")
        except Exception as e:
            logger.error(f"FAILED to add column: {e}")
            raise e

if __name__ == "__main__":
    update_schema()
