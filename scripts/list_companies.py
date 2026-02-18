# scripts/list_companies.py
import sys
import os
from sqlalchemy import text

sys.path.append(os.getcwd())
from app.core.database import engine

def list_companies():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT id, nit, razon_social FROM empresas LIMIT 10;"))
        for row in result:
            print(f"ID: {row.id} | NIT: {row.nit} | Nombre: {row.razon_social}")

if __name__ == "__main__":
    list_companies()
