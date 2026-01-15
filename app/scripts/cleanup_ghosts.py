from app.core.database import SessionLocal
from app.models.consumo_registros import HistorialConsumo
from sqlalchemy import text

def cleanup():
    db = SessionLocal()
    try:
        print("Starting cleanup of ghost reversions...")
        
        # Count target records
        query = db.query(HistorialConsumo).filter(
            HistorialConsumo.tipo_operacion.in_(['REVERSION', 'CONSUMO']),
            HistorialConsumo.documento_id == None
        )
        count = query.count()
        print(f"Found {count} ghost reversions to delete.")
        
        if count > 0:
            # Delete them
            query.delete(synchronize_session=False)
            db.commit()
            print("Deletion complete and committed.")
        else:
            print("No ghost reversions found.")
            
    except Exception as e:
        db.rollback()
        print(f"Error during cleanup: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    cleanup()
