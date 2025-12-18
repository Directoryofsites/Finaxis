
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.usuario import Usuario
from sqlalchemy import text

def check_db_and_users():
    print(f"--- Database Configuration ---")
    # Using config settings which should now load from the updated .env or default
    # Note: changes to .env might need reload if internal caching, but new process (run_command) should pick it up.
    
    db_url = settings.DATABASE_URL
    if "@" in db_url:
        prefix = db_url.split("@")[0]
        suffix = db_url.split("@")[1]
        print(f"Full URL (masked): {prefix.split(':')[0]}:****@{suffix}")
        print(f"Target Database: {suffix.split('/')[-1]}")
    else:
        print(f"Database URL: {db_url}")

    print("\n--- Connecting to Database... ---")
    try:
        db = SessionLocal()
        # Verify actual connected DB name
        result = db.execute(text("SELECT current_database()")).scalar()
        print(f"Connected to ACTUAL database: {result}")
        
        print("\n--- Users List ---")
        users = db.query(Usuario).all()
        if users:
            for user in users:
                print(f"ID: {user.id} | Email: {user.email} | Name: {user.nombre_completo} | Empresa: {user.empresa_id}")
        else:
            print("No users found in this database.")
        
        db.close()
    except Exception as e:
        print(f"Error connecting or querying database: {e}")

if __name__ == "__main__":
    check_db_and_users()
