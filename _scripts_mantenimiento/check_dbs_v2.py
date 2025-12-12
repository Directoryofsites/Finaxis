import sys
import traceback

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("Error: psycopg2 module not found. Please install it.")
    sys.exit(1)

# Configuration based on known credentials
DB_HOST = "localhost"
DB_PORT = "5432"
DB_USER = "postgres"
DB_PASS = "Jh_811880_:Panica_33195_/*" 

def check_databases():
    try:
        print(f"Connecting to {DB_HOST}:{DB_PORT} as {DB_USER}...")
        conn = psycopg2.connect(
            dbname="postgres",
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        print("Connected! Querying databases...")
        cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        rows = cur.fetchall()
        dbs = [row[0] for row in rows]
        
        target_dbs = ["contapy_db", "finaxis_db_kiro"]
        results = {}

        for db_name in target_dbs:
            if db_name in dbs:
                try:
                    conn_db = psycopg2.connect(
                        dbname=db_name,
                        user=DB_USER,
                        password=DB_PASS,
                        host=DB_HOST,
                        port=DB_PORT
                    )
                    cur_db = conn_db.cursor()
                    cur_db.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")
                    count = cur_db.fetchone()[0]
                    
                    data_msg = ""
                    if count > 0:
                        try:
                            cur_db.execute("SELECT count(*) FROM empresas;")
                            empresas_count = cur_db.fetchone()[0]
                            data_msg = f" (Datos confirmados: {empresas_count} empresas)"
                        except:
                            data_msg = " (No se pudo verificar datos)"
                            
                    results[db_name] = f"EXISTE - Tablas: {count}{data_msg}"
                    conn_db.close()
                except Exception as e:
                    results[db_name] = f"EXISTE pero Error conexión: {e}"
            else:
                results[db_name] = "NO EXISTE"

        print("\n" + "="*40)
        print("REPORTE DE BASES DE DATOS")
        print("="*40)
        for name, status in results.items():
            print(f"- {name}: {status}")
        print("="*40)

        cur.close()
        conn.close()

    except Exception:
        print("CRITICAL ERROR:")
        traceback.print_exc()

if __name__ == "__main__":
    check_databases()
