from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, SessionLocal
from app.models.empresa import Empresa
from app.models.usuario import Usuario

# Setup DB connection
# Assuming get_db_url works, or we can construct it if needed.
# Since I am in the environment, I can probably import models.

from app.core.database import SessionLocal

session = SessionLocal()

def debug_company():
    nit = "4548878787"
    print(f"Searching for company with NIT: {nit}")
    
    moyano = session.query(Empresa).filter(Empresa.nit == nit).first()
    
    if not moyano:
        print("Company 'Moyano' not found!")
        return

    print(f"Found Company: {moyano.razon_social} (ID: {moyano.id})")
    print(f"Owner ID: {moyano.owner_id}")
    print(f"Padre ID: {moyano.padre_id}")

    # Find users associated with this company
    users = session.query(Usuario).filter(Usuario.empresa_id == moyano.id).all()
    print(f"\nUsers linked to company {moyano.id} via empresa_id:")
    for u in users:
        print(f" - {u.email} (ID: {u.id}) | Roles: {[r.nombre for r in u.roles]}")
        
        # Check if this user owns other companies
        owned = session.query(Empresa).filter(Empresa.owner_id == u.id).all()
        print(f"   > Owns {len(owned)} companies:")
        for o in owned:
            print(f"     - {o.razon_social} (ID: {o.id})")

    # Check companies where Moyano is the parent
    children = session.query(Empresa).filter(Empresa.padre_id == moyano.id).all()
    print(f"\nCompanies with Parent ID {moyano.id}:")
    for c in children:
        print(f" - {c.razon_social} (ID: {c.id})")

    print("\n--- Last 5 Created Companies ---")
    last_companies = session.query(Empresa).order_by(Empresa.created_at.desc()).limit(5).all()
    for c in last_companies:
        print(f"ID: {c.id} | Name: {c.razon_social} | Owner: {c.owner_id} | Padre: {c.padre_id} | Created: {c.created_at}")


if __name__ == "__main__":
    debug_company()
