from app.core.database import SessionLocal
from app.models.empresa import Empresa

session = SessionLocal()

def analyze_hierarchy():
    print("--- Hierarchy Analysis ---")
    
    # 1. Moyano (The Accountant's Holding) - Created by Support
    moyano = session.query(Empresa).filter(Empresa.razon_social.ilike("Moyano%")).first()
    if moyano:
        print(f"HOLDING: {moyano.razon_social} (ID: {moyano.id})")
        print(f"  > Padre ID: {moyano.padre_id}")
        print(f"  > Owner ID: {moyano.owner_id}")
    else:
        print("HOLDING 'Moyano' not found.")

    # 2. Merca Fruver (The Client) - Created by Accountant
    client = session.query(Empresa).filter(Empresa.razon_social.ilike("Merca Fruver%")).first()
    if client:
        print(f"CLIENT: {client.razon_social} (ID: {client.id})")
        print(f"  > Padre ID: {client.padre_id}")
        print(f"  > Owner ID: {client.owner_id}")
    else:
        print("CLIENT 'Merca Fruver' not found.")
        
    # 3. Verduras la 21
    verduras = session.query(Empresa).filter(Empresa.razon_social.ilike("Verduras la 21%")).first()
    if verduras:
        print(f"CLIENT: {verduras.razon_social} (ID: {verduras.id})")
        print(f"  > Padre ID: {verduras.padre_id}")
        print(f"  > Owner ID: {verduras.owner_id}")
    else:
        print("CLIENT 'Verduras la 21' not found.")

if __name__ == "__main__":
    analyze_hierarchy()
