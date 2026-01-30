from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.models.permiso import Rol

session = SessionLocal()

def debug_support_dashboard():
    print("--- Debugging Support Dashboard Filtering ---")
    
    # 1. Search for "Verduras la 21"
    target_name = "Verduras la 21" # Or partial match
    print(f"\nSearching for company '{target_name}'...")
    company = session.query(Empresa).filter(Empresa.razon_social.ilike(f"%{target_name}%")).first()
    
    if not company:
        print("Company not found!")
        return

    print(f"Found Company: {company.razon_social} (ID: {company.id})")
    print(f"Owner ID: {company.owner_id}")
    print(f"Is Template: {company.is_template}")

    if company.is_template:
        print(">> RESULT: This company is HIDDEN because 'is_template' is True (viewing REAL companies).")
        return
    
    if company.owner_id:

        owner = session.query(Usuario).filter(Usuario.id == company.owner_id).first()
        if owner:
            roles = [r.nombre for r in owner.roles]
            print(f"Owner Email: {owner.email}")
            print(f"Owner Roles: {roles}")
            
            is_contador = any(r.lower() == 'contador' for r in roles)
            print(f"Is Owner a Accountant? {is_contador}")
            
            if is_contador:
                print(">> RESULT: This company is correctly hidden from 'Mis Empresas' (ADMIN) tab because owner is a Contador.")
            else:
                print(">> RESULT: This company SHOULD appear in 'Mis Empresas' tab (Owner is not Contador).")
        else:
            print("Owner user not found in DB!")
    else:
        print("Owner ID is None. This company implies System/Support ownership.")
        print(">> RESULT: This company SHOULD appear in 'Mis Empresas' tab.")

    # 2. Simulate the Exclusion Query
    print("\n--- Simulating Logic Exclusion ---")
    subquery_contadores = session.query(Empresa.id) \
            .join(Empresa.owner) \
            .join(Usuario.roles) \
            .filter(Rol.nombre.ilike('contador'))
            
    excluded_ids = [r[0] for r in subquery_contadores.all()]
    
    if company.id in excluded_ids:
        print(f"Company ID {company.id} is in the EXCLUDED list (treated as Contador company).")
    else:
        print(f"Company ID {company.id} is NOT in the excluded list (treated as Admin company).")

    # 3. Simulate Pagination Request
    print("\n--- Simulating API Request (Page 1) ---")
    from app.services import soporte as services_soporte
    
    # We need a proper DB session
    response = services_soporte.search_empresas(session, q=None, role_filter='ADMIN', page=1, size=20)
    
    print(f"Total Items Found: {response.total}")
    print(f"Total Pages: {response.pages}")
    
    found_in_page_1 = False
    for item in response.items:
        if item.id == company.id:
            found_in_page_1 = True
            print(f"!! SUCCESS: Company '{item.razon_social}' found in Page 1.")
            break
            
    if not found_in_page_1:
         print(f"?? WARNING: Company '{company.razon_social}' NOT found in Page 1. It might be in another page.")


if __name__ == "__main__":
    debug_support_dashboard()
