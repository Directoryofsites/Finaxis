
import sys
import os

# Add parent directory to path to import app
sys.path.append(os.getcwd())

from app.core.database import SessionLocal, engine
from sqlalchemy import text

def migrate_schema():
    print("--- STARTING MIGRATION: ADDING ID TO CONTROL_PLAN_MENSUAL ---")
    
    with engine.connect() as connection:
        trans = connection.begin()
        try:
            # 1. Check if column exists
            print("Checking if column 'id' exists...")
            result = connection.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='control_plan_mensual' AND column_name='id'"))
            if result.fetchone():
                print("Column 'id' already exists. Skipping add column.")
            else:
                print("Adding column 'id'...")
                # We add as SERIAL (Auto-increment) but NOT PRIMARY KEY yet to avoid locking issues with existing composite PK
                connection.execute(text("ALTER TABLE control_plan_mensual ADD COLUMN id SERIAL"))
                print("Column 'id' added.")

            # 2. Check Constraint
            # We need to drop the existing primary key constraint (composite) and set ID as PK
            # First, find the PK constraint name
            print("Finding existing PK constraint...")
            # Usually it's 'control_plan_mensual_pkey' but let's be safe (Postgres default)
            pk_name_result = connection.execute(text("SELECT constraint_name FROM information_schema.table_constraints WHERE table_name = 'control_plan_mensual' AND constraint_type = 'PRIMARY KEY'"))
            pk_name_row = pk_name_result.fetchone()
            
            if pk_name_row:
                pk_name = pk_name_row[0]
                print(f"Found PK: {pk_name}. Dropping it...")
                connection.execute(text(f"ALTER TABLE control_plan_mensual DROP CONSTRAINT {pk_name}"))
            else:
                print("No PK found? Proceeding...")

            # 3. Add Unique Constraint for the old PK fields (so we don't lose that logic)
            print("Adding UNIQUE constraint for (empresa_id, anio, mes)...")
            try:
                connection.execute(text("ALTER TABLE control_plan_mensual ADD CONSTRAINT uq_plan_empresa_periodo UNIQUE (empresa_id, anio, mes)"))
            except Exception as e:
                print(f"Constraint might already exist: {e}")

            # 4. Set ID as Primary Key
            print("Setting 'id' as PRIMARY KEY...")
            connection.execute(text("ALTER TABLE control_plan_mensual ADD PRIMARY KEY (id)"))
            
            trans.commit()
            print("--- MIGRATION COMPLETE SUCCESSFUL ---")
            
        except Exception as e:
            trans.rollback()
            print(f"--- MIGRATION FAILED: {e} ---")
            # Don't raise, just print. User might have run it already.

if __name__ == "__main__":
    migrate_schema()
