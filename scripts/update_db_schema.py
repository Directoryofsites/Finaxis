# scripts/update_db_schema.py
import sys
import os
from sqlalchemy import text

# Añadir directorio raíz al path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal, engine

def update_schema():
    print("--- ACTUALIZANDO SCHEMA PARA MODO EXPRESS ---")
    with engine.connect() as connection:
        # Transacción
        with connection.begin():
            # 1. Tabla EMPRESAS
            print("Actualizando tabla 'empresas'...")
            try:
                connection.execute(text("ALTER TABLE empresas ADD COLUMN IF NOT EXISTS is_lite_mode BOOLEAN DEFAULT FALSE;"))
                connection.execute(text("ALTER TABLE empresas ADD COLUMN IF NOT EXISTS saldo_facturas_venta INTEGER DEFAULT 0;"))
                connection.execute(text("ALTER TABLE empresas ADD COLUMN IF NOT EXISTS saldo_documentos_soporte INTEGER DEFAULT 0;"))
                connection.execute(text("ALTER TABLE empresas ADD COLUMN IF NOT EXISTS fecha_vencimiento_plan DATE;"))
                print("Columnas en 'empresas' verificadas/añadidas.")
            except Exception as e:
                print(f"Error en tabla empresas: {e}")

            # 2. Tabla PRODUCTOS
            print("Actualizando tabla 'productos'...")
            try:
                connection.execute(text("ALTER TABLE productos ADD COLUMN IF NOT EXISTS controlar_inventario BOOLEAN DEFAULT TRUE;"))
                print("Columnas en 'productos' verificadas/añadidas.")
            except Exception as e:
                print(f"Error en tabla productos: {e}")

    print("--- ACTUALIZACIÓN COMPLETADA ---")

if __name__ == "__main__":
    update_schema()
