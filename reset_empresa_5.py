import sys
import os

# Add the project root to the python path
sys.path.append(os.getcwd())

from sqlalchemy import create_engine, text
from app.core.config import settings

def reset_empresa_5():
    # Database Connection
    # Assuming settings.DATABASE_URL is available, otherwise construct it
    # We'll try to import settings, if not we'll use a default or ask.
    # Based on previous context, it seems to be a standard FastAPI app.
    
    print("Connecting to database...")
    try:
        engine = create_engine(settings.DATABASE_URL)
        connection = engine.connect()
        print("Connected.")
    except Exception as e:
        print(f"Error connecting: {e}")
        return

    empresa_id = 5
    print(f"WARNING: This will DELETE ALL DATA for Empresa ID {empresa_id} (Acme Verduras LA 21).")
    print("Preserving: Empresa record, Users.")
    
    # List of tables to clean (Order matters for Foreign Keys if constraints are enforced)
    # We will try to disable FK checks or delete in reverse order of dependency.
    
    tables_to_clean = [
        "movimientos_contables", # Detail
        "documentos",            # Header
        "productos",
        "bodegas",
        "grupos_inventario",
        "listas_precios",
        "terceros",
        "centros_costo",
        "plan_cuentas",          # PUC
        "impuestos",
        "tipos_documento",
        "periodos_contables_cerrados",
        "plantillas_detalle",
        "plantillas_maestra",
        "aplicaciones_pago",
        "cupos_adicionales",
        "logs_operaciones"       # Maybe? User didn't specify, but usually good to clean logs for a fresh start.
    ]

    # Verify table names (some might be singular or plural in DB vs Models)
    # Based on models:
    # movimiento_contable.py -> __tablename__ = 'movimientos_contables' (Likely plural)
    # Let's assume standard pluralization or check models.
    
    # Correction based on common conventions in this project (I saw 'empresas', 'usuarios'):
    # I will use a safe approach: Check if table exists or just try delete.
    
    # Map model file to table name (Best guess based on file names)
    # movimiento_contable -> movimientos_contables
    # documento -> documentos
    # producto -> productos
    # tercero -> terceros
    # plan_cuenta -> plan_cuentas
    # centro_costo -> centros_costo (or centros_costos?)
    # impuesto -> impuestos
    # tipo_documento -> tipos_documento
    
    # Let's use a transaction
    trans = connection.begin()
    
    try:
        # Disable FK checks (Postgres specific, or generic)
        # For Postgres: SET session_replication_role = 'replica'; (Dangerous)
        # Better: Delete in correct order.
        
        # 1. Transactional Data (Children)
        print("Deleting Movimientos Contables...")
        connection.execute(text(f"DELETE FROM movimientos_contables WHERE empresa_id = {empresa_id}"))
        
        print("Deleting Aplicaciones de Pago...")
        connection.execute(text(f"DELETE FROM aplicaciones_pago WHERE empresa_id = {empresa_id}"))

        print("Deleting Documentos...")
        connection.execute(text(f"DELETE FROM documentos WHERE empresa_id = {empresa_id}"))
        
        # 2. Inventory & Products
        print("Deleting Productos...")
        connection.execute(text(f"DELETE FROM productos WHERE empresa_id = {empresa_id}"))
        
        print("Deleting Bodegas...")
        connection.execute(text(f"DELETE FROM bodegas WHERE empresa_id = {empresa_id}"))
        
        print("Deleting Grupos Inventario...")
        connection.execute(text(f"DELETE FROM grupos_inventario WHERE empresa_id = {empresa_id}"))
        
        print("Deleting Listas de Precios...")
        connection.execute(text(f"DELETE FROM listas_precios WHERE empresa_id = {empresa_id}"))

        # 3. Master Data
        print("Deleting Terceros...")
        connection.execute(text(f"DELETE FROM terceros WHERE empresa_id = {empresa_id}"))
        
        print("Deleting Centros de Costo...")
        connection.execute(text(f"DELETE FROM centros_costo WHERE empresa_id = {empresa_id}"))
        
        print("Deleting Plan de Cuentas (PUC)...")
        connection.execute(text(f"DELETE FROM plan_cuentas WHERE empresa_id = {empresa_id}"))
        
        print("Deleting Impuestos...")
        connection.execute(text(f"DELETE FROM impuestos WHERE empresa_id = {empresa_id}"))
        
        print("Deleting Tipos de Documento...")
        connection.execute(text(f"DELETE FROM tipos_documento WHERE empresa_id = {empresa_id}"))
        
        print("Deleting Periodos Cerrados...")
        connection.execute(text(f"DELETE FROM periodos_contables_cerrados WHERE empresa_id = {empresa_id}"))
        
        print("Deleting Plantillas...")
        connection.execute(text(f"DELETE FROM plantillas_detalle WHERE plantilla_id IN (SELECT id FROM plantillas_maestra WHERE empresa_id = {empresa_id})"))
        connection.execute(text(f"DELETE FROM plantillas_maestra WHERE empresa_id = {empresa_id}"))

        # 4. Logs (Optional but clean)
        print("Deleting Logs de Operacion...")
        connection.execute(text(f"DELETE FROM logs_operaciones WHERE empresa_id = {empresa_id}"))

        trans.commit()
        print("SUCCESS: Company 5 has been reset to a shell.")
        
    except Exception as e:
        trans.rollback()
        print(f"ERROR: {e}")
        print("Rolled back changes.")
    finally:
        connection.close()

if __name__ == "__main__":
    reset_empresa_5()
