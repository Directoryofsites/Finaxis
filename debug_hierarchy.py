from app.core.database import SessionLocal
from app.models.usuario import Usuario
from app.models.empresa import Empresa

session = SessionLocal()

def check_hierarchy():
    print("--- Checking Hierarchy for User 48 ---")
    
    # 1. Check User 48
    user = session.query(Usuario).filter(Usuario.id == 48).first()
    if not user:
        print("User 48 not found.")
        return
        
    print(f"User: {user.email} (ID: {user.id})")
    print(f"User Company ID: {user.empresa_id}")
    
    if user.empresa_id:
        user_company = session.query(Empresa).filter(Empresa.id == user.empresa_id).first()
        print(f"User Belongs to Company: {user_company.razon_social} (ID: {user_company.id})")
    
    # 2. Check Unwanted Companies (e.g., Verduras la 21 - ID 134)
    check_ids = [134, 146, 152] # Verduras, Moyano, Billares
    
    print("\n--- Inspecting Companies ---")
    for eid in check_ids:
        c = session.query(Empresa).filter(Empresa.id == eid).first()
        if c:
            print(f"Company: {c.razon_social} (ID: {c.id})")
            print(f" - Owner ID: {c.owner_id}")
            print(f" - Padre ID: {c.padre_id}")
            
            # Simulate Logic
            if user.empresa_id and c.padre_id == user.empresa_id:
                print("   [!] LINKED VIA HIERARCHY (Child of User's Company)")
            
            if c.owner_id == user.id:
                 print("   [!] LINKED VIA OWNERSHIP")
                 
    # 3. Check what get_empresas_para_usuario WOULD return
    # Mimic the logic roughly
    print("\n--- Mimicking Service Logic ---")
    found_ids = set()
    
    # A. Owned
    owned = session.query(Empresa).filter(Empresa.owner_id == user.id).all()
    print(f"Owned Count: {len(owned)}")
    for x in owned: found_ids.add(x.id)
    
    # B. Assigned
    print(f"Assigned Count: {len(user.empresas_asignadas)}")
    for x in user.empresas_asignadas: found_ids.add(x.id)
    
    # C. Children
    if user.empresa_id:
        children = session.query(Empresa).filter(Empresa.padre_id == user.empresa_id).all()
        print(f"Children Count: {len(children)}")
        for x in children: found_ids.add(x.id)
        
    print(f"\nTotal Visible IDs: {found_ids}")

if __name__ == "__main__":
    check_hierarchy()
