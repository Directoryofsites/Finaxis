import psycopg2
import os

DB_HOST = "localhost"
DB_USER = "postgres"
DB_PASS = "mysecretpassword"

dbs_to_check = ["contapy_db", "kiro_clean_db"]
target_nit = "11007877"

def find_ghost_tercero(db_name):
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            dbname=db_name
        )
        cursor = conn.cursor()
        
        print(f"\n--- BUSCANDO EN {db_name} ---")
        
        # Buscar por NIT
        query = f"SELECT id, razon_social FROM terceros WHERE numero_identificacion = '{target_nit}'"
        cursor.execute(query)
        res = cursor.fetchone()
        
        if res:
            print(f"🚨 ¡ENCONTRADO en {db_name}!")
            print(f"   ID: {res[0]}")
            print(f"   Nombre: {res[1]}")
        else:
            print(f"✅ No existe en {db_name}")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Error conectando a {db_name}: {e}")

if __name__ == "__main__":
    print(f"Buscando al tercero 'aaaall' (NIT {target_nit})...")
    for db in dbs_to_check:
        find_ghost_tercero(db)
