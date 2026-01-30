from app.core.database import SessionLocal
from app.models.usuario import Usuario
from app.models.empresa import Empresa

session = SessionLocal()

def verify_access_logic():
    print("--- Verifying Switch Company Logic ---")
    
    # 1. Get User Moyano (The Accountant)
    moyano = session.query(Usuario).filter(Usuario.email.like("moyano%")).first()
    if not moyano:
        print("User Moyano not found")
        return

    print(f"User: {moyano.email} (ID: {moyano.id})")
    print(f"User Company ID: {moyano.empresa_id}")
    
    # 2. Get a target company that is failing (e.g. Merca Fruver which is a child)
    # or one of the new ones created by him.
    # Let's check all companies he owns or is parent of.
    
    # Owned companies
    owned = session.query(Empresa).filter(Empresa.owner_id == moyano.id).all()
    print(f"\nOwned Companies ({len(owned)}):")
    for c in owned:
        print(f" - {c.razon_social} (ID: {c.id})")
        
    # Child companies
    children = []
    if moyano.empresa_id:
        children = session.query(Empresa).filter(Empresa.padre_id == moyano.empresa_id).all()
        print(f"\nChild Companies of Account ({moyano.empresa_id}):")
        for c in children:
            print(f" - {c.razon_social} (ID: {c.id})")

    # 3. Simulate Logic from auth/routes.py
    print("\n--- Simulating Backend Check ---")
    
    # Let's pick a target that is NOT in assigned
    target = None
    if children: target = children[0]
    elif owned: target = owned[0]
    
    if not target:
        print("No target company found to test.")
        return

    print(f"Testing Access to: {target.razon_social} (ID: {target.id})")
    
    # Logic in Route:
    access_found = False
    
    # A. Propia
    if moyano.empresa_id == target.id:
        print(f" [PASS] Own Company ID matched.")
        access_found = True
        
    # B. Asignadas
    if not access_found:
        assigned_ids = [e.id for e in moyano.empresas_asignadas]
        print(f" Assigned IDs: {assigned_ids}")
        if target.id in assigned_ids:
            print(f" [PASS] Found in Assigned Companies.")
            access_found = True
            
    if not access_found:
        print(" [FAIL] 403 Forbidden would be returned.")
        
    # C. Missing Logic (Verification)
    print("\n--- Logic That Should Be Added ---")
    should_pass = False
    
    # Owner Check
    if target.owner_id == moyano.id:
        print(" [WOULD PASS] User is Owner.")
        should_pass = True
        
    # Hierarchy Check
    if moyano.empresa_id and target.padre_id == moyano.empresa_id:
        print(" [WOULD PASS] User's company is Parent.")
        should_pass = True
        
    if should_pass and not access_found:
        print(">> CONFIRMED: Logic gap identified.")
    elif not should_pass:
        print(">> WARNING: Even with new logic this might fail? Check data.")

if __name__ == "__main__":
    verify_access_logic()
