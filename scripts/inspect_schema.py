# scripts/inspect_schema.py
import sys
import os
from sqlalchemy import text

# Añadir directorio raíz al path
sys.path.append(os.getcwd())

from app.core.database import engine

def inspect_table():
    print("--- INSPECCIONANDO TABLA EMPRESAS ---")
    with engine.connect() as connection:
        result = connection.execute(text(
            "SELECT column_name, data_type, character_maximum_length "
            "FROM information_schema.columns "
            "WHERE table_name = 'empresas';"
        ))
        for row in result:
            print(f"{row.column_name}: {row.data_type} ({row.character_maximum_length})")

if __name__ == "__main__":
    inspect_table()
