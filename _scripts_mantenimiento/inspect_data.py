import sys
import os

# Ensure we can import from 'app'
sys.path.append(os.getcwd())

try:
    from app.core.database import engine
    from sqlalchemy import text

    print("--- INSPECTOR DE CONTENIDO (Antigravity) ---")
    
    with engine.connect() as connection:
        print(f"Conectado a DB: {engine.url.database}")
        
        # 1. Contar Empresas
        try:
            result = connection.execute(text("SELECT id, razon_social, nit FROM empresas"))
            rows = result.fetchall()
            print(f"\n[TABLA EMPRESAS]: {len(rows)} registros encontrados.")
            for row in rows:
                print(f" - ID: {row[0]} | {row[1]} (NIT: {row[2]})")
        except Exception as e:
            print(f"Error leyendo empresas: {e}")

        # 2. Contar Usuarios
        try:
            result = connection.execute(text("SELECT count(*) FROM usuarios"))
            count = result.scalar()
            print(f"\n[TABLA USUARIOS]: {count} usuarios totales.")
        except:
             pass

except Exception as e:
    print(f"❌ ERROR CRÍTICO: {e}")
