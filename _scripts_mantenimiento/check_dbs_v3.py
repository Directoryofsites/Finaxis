import sys
import psycopg2

# Configuration
DB_HOST = "localhost"
DB_PORT = "5432"
DB_USER = "postgres"

# Candidate Passwords
PASSWORDS = [
    "Jh_811880_:Panica_33195_/*",  # From config.py
    "mysecretpassword",            # From alembic.ini
    "admin",
    "postgres",
    "root"
]

def check_databases():
    print(f"Iniciando escaneo de DB en {DB_HOST}:{DB_PORT}...")
    
    conn = None
    active_pass = None

    # 1. Intentar conectar
    for pwd in PASSWORDS:
        try:
            print(f"Probando password: {pwd[:3]}*** ...")
            c = psycopg2.connect(
                dbname="postgres",
                user=DB_USER,
                password=pwd,
                host=DB_HOST,
                port=DB_PORT
            )
            c.close()
            active_pass = pwd
            print("¡CONEXIÓN EXITOSA!")
            break
        except psycopg2.OperationalError:
            print("  -> Falló.")

    if not active_pass:
        print("\n❌ CRÍTICO: No se pudo conectar con ninguna contraseña conocida.")
        return

    # 2. Proceder con el escaneo
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=DB_USER,
            password=active_pass,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        rows = cur.fetchall()
        dbs = [row[0] for row in rows]
        
        print(f"\n✅ Bases de datos en el servidor:")
        found_target = False
        for db in dbs:
            marker = " <--- TUYA" if db == "contapy_db" else ""
            marker2 = " <--- KIRO" if db == "finaxis_db_kiro" else ""
            print(f"- {db}{marker}{marker2}")
            if db == "finaxis_db_kiro":
                found_target = True

        if found_target:
            try:
                conn_k = psycopg2.connect(
                    dbname="finaxis_db_kiro",
                    user=DB_USER,
                    password=active_pass,
                    host=DB_HOST,
                    port=DB_PORT
                )
                cur_k = conn_k.cursor()
                cur_k.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")
                n_tabs = cur_k.fetchone()[0]
                print(f"\n🔎 ANÁLISIS DE KIRO: La base de datos existe y tiene {n_tabs} tablas.")
                conn_k.close()
            except Exception as e:
                print(f"\n⚠️ La DB de Kiro existe pero no pude leerla: {e}")
        else:
            print("\n❌ LA BASE DE DATOS DE KIRO 'finaxis_db_kiro' NO EXISTE.")

        conn.close()

    except Exception as e:
        print(f"Error durante el escaneo: {e}")


if __name__ == "__main__":
    check_databases()
