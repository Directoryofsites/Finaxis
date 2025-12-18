
from app.core.database import engine
from sqlalchemy import text

def dump_users_sql():
    print("--- Executing Raw SQL: SELECT * FROM usuarios; ---")
    with engine.connect() as connection:
        # We select specific columns to be readable
        try:
            # First, let's just inspect columns to be sure
            result = connection.execute(text("SELECT * FROM usuarios LIMIT 1"))
            print(f"Columns: {result.keys()}")
            
            # Now dump data
            result = connection.execute(text("SELECT id, email, nombre_completo, password_hash FROM usuarios"))
            rows = result.fetchall()
            if not rows:
                print("No users found.")
            for row in rows:
                print(f"User: {row}")
        except Exception as e:
            print(f"Error executing SQL: {e}")

if __name__ == "__main__":
    dump_users_sql()
