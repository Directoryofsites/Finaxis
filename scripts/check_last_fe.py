
from sqlalchemy import create_engine, text
import json

DATABASE_URL = "postgresql://postgres:mysecretpassword@localhost:5432/contapy_db"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("SELECT id, numero, dian_estado, dian_error FROM documentos WHERE dian_estado IS NOT NULL ORDER BY id DESC LIMIT 1")).fetchone()
    if result:
        print(f"ID: {result[0]}")
        print(f"Numero: {result[1]}")
        print(f"Estado: {result[2]}")
        try:
            error_json = json.loads(result[3])
            print("Response JSON:")
            print(json.dumps(error_json, indent=2))
        except:
            print(f"Error (Raw): {result[3]}")
    else:
        print("No se encontraron documentos emitidos.")
