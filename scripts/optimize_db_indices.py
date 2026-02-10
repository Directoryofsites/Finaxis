from sqlalchemy import create_engine, text
import os
import sys

# Add parent directory to path to import app modules if needed (or just use raw connection)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def optimize_indices():
    print(f"Connecting to database...")
    engine = create_engine(settings.DATABASE_URL)
    
    indices_to_create = [
        {
            "name": "idx_mov_inv_fecha",
            "table": "movimientos_inventario",
            "column": "fecha",
            "sql": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_mov_inv_fecha ON movimientos_inventario (fecha);"
        },
        {
            "name": "idx_mov_inv_producto",
            "table": "movimientos_inventario",
            "column": "producto_id",
            "sql": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_mov_inv_producto ON movimientos_inventario (producto_id);"
        },
        {
             "name": "idx_mov_inv_bodega",
             "table": "movimientos_inventario",
             "column": "bodega_id",
             "sql": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_mov_inv_bodega ON movimientos_inventario (bodega_id);"
        },
        {
             "name": "idx_mov_inv_documento",
             "table": "movimientos_inventario",
             "column": "documento_id",
             "sql": "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_mov_inv_documento ON movimientos_inventario (documento_id);"
        }
    ]

    with engine.connect() as connection:
        # Enable usage of CONCURRENTLY which cannot run in a transaction block
        connection.execution_options(isolation_level="AUTOCOMMIT")
        
        for idx in indices_to_create:
            print(f"Checking index: {idx['name']} on {idx['table']}...")
            try:
                # Check if exists
                check_sql = text(f"SELECT 1 FROM pg_indexes WHERE indexname = '{idx['name']}'")
                result = connection.execute(check_sql).fetchone()
                
                if result:
                    print(f" -> Index {idx['name']} ALREADY EXISTS.")
                else:
                    print(f" -> Creating index {idx['name']}...")
                    connection.execute(text(idx['sql']))
                    print(f" -> Index {idx['name']} CREATED successfully.")
            except Exception as e:
                print(f"Error creating index {idx['name']}: {e}")

if __name__ == "__main__":
    optimize_indices()
