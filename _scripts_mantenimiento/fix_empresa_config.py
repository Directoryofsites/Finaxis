from app.core.database import engine
from sqlalchemy import text

def run_fix():
    print("Connecting to DB...")
    with engine.connect() as connection:
        print("Executing ALTER TABLE for settings...")
        connection.execute(text("ALTER TABLE empresas ADD COLUMN IF NOT EXISTS prefijo_cxc VARCHAR(10) DEFAULT '13';"))
        connection.execute(text("ALTER TABLE empresas ADD COLUMN IF NOT EXISTS prefijo_cxp VARCHAR(10) DEFAULT '2';"))
        connection.commit()
    print("Done!")

if __name__ == "__main__":
    run_fix()
