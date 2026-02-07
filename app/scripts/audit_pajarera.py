from app.core.database import SessionLocal
from sqlalchemy import text

def audit():
    db = SessionLocal()
    try:
        # RAW SQL to avoid ORM Mapper headaches
        print("--- RUNNING RAW SQL AUDIT ---")
        sql = text("SELECT id, razon_social, padre_id FROM empresas WHERE razon_social ILIKE :term")
        result = db.execute(sql, {"term": "%pajarera%"})
        rows = result.fetchall()
        
        print(f"Found {len(rows)} companies matching 'pajarera'")
        for row in rows:
            print(f"ID: {row[0]} | Name: {row[1]}")
            curr_id = row[2]
            level = 1
            while curr_id:
                sql_p = text("SELECT id, razon_social, padre_id FROM empresas WHERE id = :pid")
                parent = db.execute(sql_p, {"pid": curr_id}).fetchone()
                if parent:
                    print(f"   Level {level} Parent: {parent[1]} (ID: {parent[0]})")
                    curr_id = parent[2]
                    level += 1
                else:
                    print(f"   Level {level} Parent ID {curr_id} NOT FOUND")
                    curr_id = None
            
            if level == 1:
                print("   -> ORPHAN (No Parent)")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    audit()
