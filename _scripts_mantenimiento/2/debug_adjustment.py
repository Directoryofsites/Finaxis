import sys
import os
from sqlalchemy.orm import sessionmaker

# Add app to path
sys.path.append('c:\\ContaPY2')

from app.core.database import SessionLocal
from app.services.conciliacion_bancaria import AdjustmentEngine, BankMovement
from app.api.conciliacion_bancaria.routes import apply_automatic_adjustments

# Mock classes/functions if needed or run directly
def debug_apply_adjustment():
    db = SessionLocal()
    try:
        # 1. Find a pending COMMISSION movement
        print("Searching for pending commission movements...")
        movement = db.query(BankMovement).filter(
            BankMovement.status == 'PENDING',
            BankMovement.description.ilike('%comision%')
        ).first()

        if not movement:
            print("No pending commission movement found.")
            return

        print(f"Found pending movement: ID {movement.id}, Desc: {movement.description}, Amount: {movement.amount}")

        # 2. Try to apply adjustment using the service logic directly
        engine = AdjustmentEngine(db)
        
        print("Searching for a valid user...")
        from app.models.usuario import Usuario
        user = db.query(Usuario).first()
        if not user:
            print("No user found in DB, implementation cannot proceed.")
            return
        
        user_id = user.id
        print(f"Using mock user: ID {user.id}, Email: {user.email}")
        
        empresa_id = movement.empresa_id
        
        print("Attempting to apply adjustment...")
        result = engine.apply_adjustments([movement.id], user_id, empresa_id)
        
        print("Result:", result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"CRASH: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_apply_adjustment()
