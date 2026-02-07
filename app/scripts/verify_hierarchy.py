import sys
import os
from sqlalchemy import func

# Add project root to path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.empresa import Empresa
import app.models.nomina

def show_chain(child_id):
    db = SessionLocal()
    try:
        current = db.query(Empresa).get(child_id)
        if not current:
            print(f"Company {child_id} not found")
            return

        chain = []
        while current:
            chain.append(f"{current.razon_social} (ID: {current.id})")
            if current.padre_id:
                current = db.query(Empresa).get(current.padre_id)
            else:
                current = None
        
        print(" -> ".join(chain))
        print(f"Total Levels: {len(chain)}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Hierarchy for Pensionbes Gonzalez (ID: 205):")
    show_chain(205)
