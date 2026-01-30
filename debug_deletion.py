from app.core.database import SessionLocal
from app.models.usuario import Usuario, usuario_empresas
from app.models.empresa import Empresa

session = SessionLocal()

def inspect_foreign_key_issue():
    print("--- Inspecting Deletion Block ---")
    
    # 1. Check User 34
    user_34 = session.query(Usuario).filter(Usuario.id == 34).first()
    if user_34:
        print(f"User 34: {user_34.email} | Empresa Principal ID: {user_34.empresa_id}")
    else:
        print("User 34 not found.")
        
    # 2. Check Company 149 (The one being deleted)
    comp_149 = session.query(Empresa).filter(Empresa.id == 149).first()
    if comp_149:
        print(f"Company 149: {comp_149.razon_social} | Owner ID: {comp_149.owner_id}")
    else:
        print("Company 149 not found.")
        
    # 3. Check 'usuario_empresas' references for User 34
    # We need raw sql or accessing the relationship if mapped
    # Let's verify what `usuario_empresas` rows exist for this user
    print(f"\nUsuario_Empresas links for User 34:")
    
    # Use raw SQL to see the link table
    from sqlalchemy import text
    result = session.execute(text("SELECT * FROM usuario_empresas WHERE usuario_id = 34"))
    for row in result:
        print(f" - Link: User {row[0]} <-> Company {row[1]} (Is Owner: {row[2]})")

if __name__ == "__main__":
    inspect_foreign_key_issue()
