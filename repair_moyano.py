from app.core.database import SessionLocal
from app.models.empresa import Empresa

session = SessionLocal()

def repair_companies():
    # IDs from previous debug session
    moyano_user_id = 34
    moyano_company_id = 146
    orphaned_ids = [149, 150] # Merca Fruver la 45, Bingo la 14

    print(f"Repairing companies {orphaned_ids} for Owner {moyano_user_id} and Parent {moyano_company_id}...")

    companies = session.query(Empresa).filter(Empresa.id.in_(orphaned_ids)).all()
    
    count = 0
    for c in companies:
        print(f" -> Updating {c.razon_social} (ID: {c.id})")
        c.owner_id = moyano_user_id
        c.padre_id = moyano_company_id
        count += 1
    
    if count > 0:
        session.commit()
        print(f"Successfully repaired {count} companies.")
    else:
        print("No orphaned companies found with those IDs.")

if __name__ == "__main__":
    repair_companies()
