from app.core.database import SessionLocal
from app.services.empresa import delete_empresa_y_usuarios
from fastapi import HTTPException

session = SessionLocal()

def verify_deletion_blocker():
    COMP_ID = 153
    print(f"--- Attempting Deletion of ID {COMP_ID} ---")
    
    try:
        # We call the service function directly. 
        # Note: This will COMMIT if successful.
        result = delete_empresa_y_usuarios(session, COMP_ID)
        print("Deletion SUCCESSFUL (Unexpected if user says it failed).")
    except HTTPException as e:
        print(f"Deletion FAILED with HTTP Exception:")
        print(f"Status Code: {e.status_code}")
        print(f"Detail: {e.detail}")
    except Exception as e:
        print(f"Deletion FAILED with Unexpected Error: {str(e)}")

if __name__ == "__main__":
    verify_deletion_blocker()
