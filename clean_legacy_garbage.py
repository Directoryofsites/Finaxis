
import psycopg2
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connection parameters
DB_PARAMS = {
    "dbname": "contapy2_db",
    "user": "postgres",
    "password": "your_password", # Assuming localhost dev env from context
    "host": "localhost",
    "port": "5432"
}
# Actually, the user connection string was postgres:postgres@localhost:5432/contapy2_db
# Let's use that.

def clean_garbage():
    conn = None
    try:
        logger.info("Starting cleanup of Legacy Garbage (Direct SQL)...")
        conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/contapy2_db")
        cur = conn.cursor()
        
        # 1. Get IDs
        cur.execute("SELECT id FROM tipos_documento WHERE codigo IN ('CD-L', 'CD-LEGACY')")
        rows = cur.fetchall()
        
        if rows:
            type_ids = tuple(r[0] for r in rows)
            logger.info(f"Found Legacy Types: {type_ids}")
            
            # Delete Movimientose
            cur.execute(f"DELETE FROM movimientos_contables WHERE documento_id IN (SELECT id FROM documentos WHERE tipo_documento_id IN %s)", (type_ids,))
            
            # Delete Documents
            cur.execute(f"DELETE FROM documentos WHERE tipo_documento_id IN %s", (type_ids,))
            logger.info("Documents deleted.")

        # 2. Garbage Accounts
        cur.execute("DELETE FROM plan_cuentas WHERE nombre LIKE '%ÿ%'")
        logger.info(f"Deleted {cur.rowcount} garbage accounts.")
        
        # 3. Garbage Third Parties
        cur.execute("DELETE FROM terceros WHERE razon_social LIKE '%ÿ%'")
        logger.info(f"Deleted {cur.rowcount} garbage third parties.")

        conn.commit()
        logger.info("Cleanup Complete.")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    clean_garbage()

if __name__ == "__main__":
    clean_garbage()
