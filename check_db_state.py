from sqlalchemy import create_engine, inspect
import sys

try:
    engine = create_engine('postgresql://postgres:mysecretpassword@localhost:5432/contapy_db')
    inspector = inspect(engine)
    
    tables = inspector.get_table_names()
    print(f"EXISTS_PRODUCCION_CONFIGURACION: {'produccion_configuracion' in tables}")
    
    if 'ordenes_produccion' in tables:
        cols = [c['name'] for c in inspector.get_columns('ordenes_produccion')]
        print(f"HAS_ARCHIVAD: {'archivada' in cols}")
        print(f"HAS_MOTIVO: {'motivo_anulacion' in cols}")
        
except Exception as e:
    print(f"ERROR: {e}")
