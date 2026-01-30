from app.core.database import SessionLocal
from app.models.usuario import Usuario
from app.services.empresa import get_empresas_para_usuario

db = SessionLocal()

try:
    print("\n--- DEBUGGING MOYANO VIEW ---")
    moyano = db.query(Usuario).filter(Usuario.nombre_completo.ilike("%Moyano%")).first()
    
    if not moyano:
        print("User Moyano not found!")
    else:
        print(f"User Found: {moyano.nombre_completo} (ID: {moyano.id})")
        print(f"User EmpresaID: {moyano.empresa_id}")
        
        # Call the service function exactly as the API does
        companies = get_empresas_para_usuario(db, moyano)
        
        print(f"\nCompanies visible to Moyano ({len(companies)}):")
        for c in companies:
            print(f"  [ID: {c.id}] Name: '{c.razon_social}' | Owner: {c.owner_id} | Padre: {c.padre_id}")
            
except Exception as e:
    print(f"ERROR: {e}")
finally:
    db.close()
