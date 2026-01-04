import sys
from sqlalchemy.orm import sessionmaker

# Add app to path
sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.models.conciliacion_bancaria import BankMovement

def release_stuck_movements():
    db = SessionLocal()
    try:
        # Find all movements with status 'ADJUSTED' (orphaned from previous test)
        movements = db.query(BankMovement).filter(
            BankMovement.status == 'ADJUSTED'
        ).all()
        
        print(f"Found {len(movements)} ADJUSTED movements.")
        
        count = 0
        for mov in movements:
            print(f"Resetting Movement ID {mov.id} ({mov.description}, {mov.amount}) -> PENDING")
            mov.status = 'PENDING'
            count += 1
            
        if count > 0:
            db.commit()
            print("Successfully released movements.")
        else:
            print("No movements to release.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    release_stuck_movements()
