from app.core.database import SessionLocal
from app.models.empresa import Empresa
from sqlalchemy import or_

db = SessionLocal()

print("\n--- SEARCHING FOR 'MOYANO' ---")
# Search by name loosely
companies = db.query(Empresa).filter(Empresa.razon_social.ilike(f"%Moyano%")).all()

if not companies:
    print("No company found with name containing 'Moyano'.")
else:
    for c in companies:
        print(f"ID: {c.id}")
        print(f"Name: {c.razon_social}")
        print(f"NIT: {c.nit}")
        print(f"Owner ID: {c.owner_id}")
        print(f"Is Template?: {c.is_template}")
        print(f"Template Category: {c.template_category}")
        print(f"Created At: {c.created_at}")
        print("-" * 20)

db.close()
