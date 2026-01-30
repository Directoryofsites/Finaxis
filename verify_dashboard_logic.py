from app.core.database import SessionLocal
from app.services import soporte as services_soporte

session = SessionLocal()

def verify_new_logic():
    print("--- Verifying New Hierarchy Logic ---")
    
    # 1. Test "Mis Empresas" (ADMIN) - Should see Moyano & Verduras
    print("\n[TEST 1] Fetching 'Mis Empresas' (ADMIN)...")
    res_admin = services_soporte.search_empresas(session, role_filter='ADMIN', page=1, size=100)
    
    admin_names = [e.razon_social for e in res_admin.items]
    print(f"Found {res_admin.total} companies.")
    
    if "Moyano" in admin_names:
        print("SUCCESS: 'Moyano' found in ADMIN list.")
    else:
        print("FAILURE: 'Moyano' MISSING from ADMIN list.")
        
    if "Verduras la 21" in admin_names:
        print("SUCCESS: 'Verduras la 21' found in ADMIN list.")
    else:
        print("FAILURE: 'Verduras la 21' MISSING from ADMIN list.")

    # 2. Test "De Contadores" (CONTADOR) - Should see Merca Fruver
    print("\n[TEST 2] Fetching 'De Contadores' (CONTADOR)...")
    res_contador = services_soporte.search_empresas(session, role_filter='CONTADOR', page=1, size=100)
    
    contador_names = [e.razon_social for e in res_contador.items]
    print(f"Found {res_contador.total} companies.")
    
    if "Merca Fruver la 45" in contador_names:
        print("SUCCESS: 'Merca Fruver la 45' found in CONTADOR list.")
    else:
        print("FAILURE: 'Merca Fruver la 45' MISSING from CONTADOR list.")
        
if __name__ == "__main__":
    verify_new_logic()
