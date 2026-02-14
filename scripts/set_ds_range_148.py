
import psycopg2
import os

# --- HARDCODED CONNECTION STRING FOR SAFETY ---
DATABASE_URL = "postgresql://postgres:mysecretpassword@localhost:5432/contapy_db"

def update_ds_range():
    print(f"Connecting to {DATABASE_URL}...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # ID 148 is 'Documento Soporte' (Prefix: SEDS)
        DS_RANGE_ID = 148 
        
        print(f"Updating ds_rango_id to {DS_RANGE_ID} for enabled companies...")
        
        cursor.execute(f"UPDATE configuracion_fe SET ds_rango_id = {DS_RANGE_ID} WHERE habilitado = true;") 
        
        if cursor.rowcount > 0:
            print(f"SUCCESS: Updated {cursor.rowcount} configuration rows.")
        else:
            print("INFO: No rows updated (maybe already set or no enabled configs).")
            
        # Optional: Verify
        cursor.execute(f"SELECT empresa_id, ds_rango_id FROM configuracion_fe WHERE ds_rango_id = {DS_RANGE_ID};")
        rows = cursor.fetchall()
        print("Current State:", rows)
        
    except Exception as e:
        print(f"FATAL ERROR: {e}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    update_ds_range()
