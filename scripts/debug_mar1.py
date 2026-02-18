# scripts/debug_mar1.py
import sys
import os

sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.usuario import Usuario
from app.models.empresa import Empresa
from app.schemas.usuario import User as UserSchema

def debug_mar1():
    db = SessionLocal()
    try:
        email = "mar1@mar.com"
        target_nit = "115588"
        
        print(f"--- DEBUGGING USER: {email} ---")
        
        # 1. Get User
        user = db.query(Usuario).filter(Usuario.email == email).first()
        if not user:
            print("User not found!")
            return

        print(f"User ID: {user.id}")
        print(f"Direct Company ID: {user.empresa_id}")
        
        # 2. Get Target Company
        target_company = db.query(Empresa).filter(Empresa.nit == target_nit).first()
        if not target_company:
            print(f"Target Company NIT {target_nit} not found!")
            return
            
        print(f"Target Company: {target_company.razon_social} (ID: {target_company.id})")
        print(f"Target is_lite_mode (DB): {target_company.is_lite_mode}")

        # 3. Check Access/Link
        # Is direct?
        if user.empresa_id == target_company.id:
            print("Access Type: DIRECT (User.empresa_id matches)")
        else:
            # Check Owner
            if target_company.owner_id == user.id:
                print("Access Type: OWNER")
            else:
                # Check Assignments
                assigned = [e.id for e in user.empresas_asignadas]
                if target_company.id in assigned:
                    print("Access Type: ASSIGNED (Multi-tenant)")
                else:
                    print("WARNING: User does not seem to have clear access to this company.")

        # 4. Simulate Context Switch & Serialization
        print("\n--- SIMULATING CONTEXT SWITCH ---")
        user.empresa_id = target_company.id
        user.empresa = target_company
        
        user_pydantic = UserSchema.model_validate(user)
        dump = user_pydantic.model_dump()
        
        emp_data = dump.get('empresa', {})
        print(f"Serialized is_lite_mode: {emp_data.get('is_lite_mode')}")
        
        if emp_data.get('is_lite_mode') is True:
            print("BACKEND CHECK: PASS")
        else:
            print("BACKEND CHECK: FAIL")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_mar1()
