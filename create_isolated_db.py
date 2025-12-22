import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configuración
DB_HOST = "localhost"
DB_USER = "postgres"
DB_PASS = "mysecretpassword"
NEW_DB_NAME = "contapy_antigravity"

try:
    # Conectar a la base de datos 'postgres' por defecto para crear la nueva
    conn = psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        dbname="postgres"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # Verificar si existe
    cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{NEW_DB_NAME}'")
    exists = cursor.fetchone()
    
    if not exists:
        cursor.execute(f"CREATE DATABASE {NEW_DB_NAME}")
        print(f"✅ Base de datos '{NEW_DB_NAME}' creada exitosamente.")
    else:
        print(f"⚠️ La base de datos '{NEW_DB_NAME}' ya existe.")
        
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error creando base de datos: {e}")
