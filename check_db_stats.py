import psycopg2
import os

DB_HOST = "localhost"
DB_USER = "postgres"
DB_PASS = "mysecretpassword"

dbs_to_check = ["contapy_db", "kiro_clean_db"]

def check_db_data(db_name):
    try:
        print(f"\n--- Checking {db_name} ---")
        conn = psycopg2.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            dbname=db_name
        )
        cursor = conn.cursor()
        
        # Check Tables existence first
        cursor.execute("SELECT to_regclass('public.empresas');")
        if not cursor.fetchone()[0]:
             print(f"DATABASE {db_name} seems to have no 'empresas' table (Empty/New).")
             return

        # Count Empresas
        cursor.execute("SELECT count(*) FROM empresas")
        empresas_count = cursor.fetchone()[0]
        
        # Count Users
        cursor.execute("SELECT count(*) FROM usuarios")
        users_count = cursor.fetchone()[0]
        
        print(f"STATS FOR {db_name}:")
        print(f"   - Empresas: {empresas_count}")
        print(f"   - Usuarios: {users_count}")
        
        cursor.close()
        conn.close()
    except psycopg2.OperationalError:
        print(f"COULD NOT CONNECT to {db_name} (Maybe it doesn't exist yet).")
    except Exception as e:
        print(f"ERROR checking {db_name}: {e}")

if __name__ == "__main__":
    for db in dbs_to_check:
        check_db_data(db)
