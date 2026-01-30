from app.core.database import SessionLocal
from app.models.usuario import Usuario
from app.models.empresa import Empresa

session = SessionLocal()

def relink_user_to_company():
    USER_ID = 48
    COMPANY_NAME = "Moyano"
    
    print(f"--- Relinking User {USER_ID} to Company '{COMPANY_NAME}' ---")
    
    # 1. Find Company
    comp = session.query(Empresa).filter(Empresa.razon_social == COMPANY_NAME).first()
    if not comp:
        print(f"Company '{COMPANY_NAME}' not found.")
        return
        
    print(f"Found Company: {comp.razon_social} (ID: {comp.id})")
    
    # 2. Find User
    user = session.query(Usuario).filter(Usuario.id == USER_ID).first()
    if not user:
        print(f"User {USER_ID} not found.")
        return
        
    print(f"User: {user.email} currently has empresa_id={user.empresa_id}")
    
    # 3. Update
    user.empresa_id = comp.id
    session.add(user)
    session.commit()
    print(f"Updated User {USER_ID} -> empresa_id={comp.id}")

if __name__ == "__main__":
    relink_user_to_company()
