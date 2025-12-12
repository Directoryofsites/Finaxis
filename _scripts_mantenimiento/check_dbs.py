import psycopg2
from psycopg2 import sql

# Configuration based on known credentials
DB_HOST = "localhost"
DB_PORT = "5432"
DB_USER = "postgres"
DB_PASS = "Jh_811880_:Panica_33195_/*" # Credentials from config.py

def check_databases():
    try:
        # connect to default 'postgres' db to list others
        conn = psycopg2.connect(
            dbname="postgres",
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        print("--- Bases de Datos Encontradas ---")
        cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        rows = cur.fetchall()
        dbs = [row[0] for row in rows]
        for db in dbs:
            print(f"- {db}")
            
        print("\n--- Análisis de Contenido ---")
        
        target_dbs = ["contapy_db", "finaxis_db_kiro"]
        
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
                    print(f"[{db_name}]: EXISTE. Tiene {count} tablas en esquema 'public'.")
                    
                    if count > 0:
                        # Check specific table like 'usuarios' or 'empresas' to see if it has data
                        try:
                            cur_db.execute("SELECT count(*) FROM empresas;")
                            empresas_count = cur_db.fetchone()[0]
                            print(f"   -> Datos: {empresas_count} empresas registradas.")
                        except:
                            print("   -> No se pudo verificar datos internos (tabla empresas no existe o error).")
                            
                    conn_db.close()
                except Exception as e:
                    print(f"[{db_name}]: Error al conectar: {e}")
            else:
                print(f"[{db_name}]: NO EXISTE.")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error General: {e}")

if __name__ == "__main__":
    check_databases()
