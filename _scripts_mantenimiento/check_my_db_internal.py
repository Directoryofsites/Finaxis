import sys
import os

# Ensure we can import from 'app'
sys.path.append(os.getcwd())

try:
    from app.core.database import engine
    from sqlalchemy import inspect, text

    print("--- INICIANDO VERIFICACIÓN INTERNA (Antigravity) ---")
    
    # Check connection
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Conexión al motor: EXITOSA")
            
            # Use inspector
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            print(f"\n✅ Base de Datos Conectada: {engine.url.database}")
            print(f"✅ Total Tablas Encontradas: {len(tables)}")
            
            if len(tables) > 0:
                print("\nPrimeras 10 tablas:")
                for t in tables[:10]:
                    print(f" - {t}")
            else:
                print("⚠️ La base de datos está vacía (0 tablas).")

    except Exception as e:
        print(f"❌ ERROR DE CONEXIÓN: {e}")

except Exception as e:
    print(f"❌ ERROR DE IMPORTACIÓN: {e}")
