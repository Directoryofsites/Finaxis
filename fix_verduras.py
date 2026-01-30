from app.core.database import SessionLocal
from app.models.empresa import Empresa

session = SessionLocal()

def fix_company_template_status():
    target_name = "Verduras la 21"
    print(f"Searching for company '{target_name}' to fix...")
    
    company = session.query(Empresa).filter(Empresa.razon_social.ilike(f"%{target_name}%")).first()
    
    if not company:
        print("Company not found!")
        return

    print(f"Found Company: {company.razon_social} (ID: {company.id})")
    print(f"Current 'is_template' status: {company.is_template}")
    
    if company.is_template:
        print("Changing 'is_template' to False details...")
        company.is_template = False
        session.commit()
        print("SUCCESS: Company is now marked as a REAL company.")
    else:
        print("Company is already a REAL company (is_template=False). No changes needed.")

if __name__ == "__main__":
    fix_company_template_status()
