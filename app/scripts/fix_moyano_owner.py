from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.usuario import Usuario

db = SessionLocal()

try:
    # 1. Inspect Company 146
    company = db.query(Empresa).filter(Empresa.id == 146).first()
    print(f"Company Found: {company.razon_social} (ID: {company.id}) - Owner: {company.owner_id}")

    # 2. Find User Moyano
    # Assuming email contains 'moyano' based on context (moyano@moyano.com or similar)
    # 2. Find User Moyano
    # Remove role_id filter as it doesn't exist on User model
    users = db.query(Usuario).filter(Usuario.email.ilike("%moyano%")).all()
    
    selected_user = None
    
    if not users:
        print("User 'Moyano' NOT found. Listing all users:")
        all_users = db.query(Usuario).all()
        for u in all_users:
            print(f"- {u.id}: {u.email}")
    else:
        print(f"Found {len(users)} user(s) matching 'moyano':")
        for u in users:
            role_names = [r.nombre for r in u.roles]
            print(f"- ID: {u.id} | Email: {u.email} | Roles: {role_names}")
            
            # Select the one that is likely the accountant (not support if possible, or usually the one with accountant role)
            # Assuming 'CONTADOR' or similar role
            if 'CONTADOR' in [r.nombre.upper() for r in u.roles]:
                selected_user = u
        
        # Fallback: if only one user found, select it
        if len(users) == 1 and not selected_user:
            selected_user = users[0]

    if selected_user:
        print(f"\nSelecting User: {selected_user.email} (ID: {selected_user.id})")
        
        # 3. Apply Fix
        print(f"Assigning Company {company.id} to User {selected_user.id}...")
        company.owner_id = selected_user.id
        db.commit()
        print("SUCCESS: Owner Updated.")
    else:
        print("\nCOULD NOT IDENTIFY UNIQUE USER. ABORTING.")

finally:
    db.close()
