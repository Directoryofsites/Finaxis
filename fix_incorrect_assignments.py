from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.usuario import usuario_empresas
from sqlalchemy import text

session = SessionLocal()

def fix_assignments():
    MOYANO_USER_ID = 48
    ALLOWED_IDS = [152, 153] # bILLARES LA 40, Iglesia la 33
    
    print(f"--- Fixing Assignments for User {MOYANO_USER_ID} ---")
    print(f"Keeping STRICTLY: {ALLOWED_IDS}")
    
    # 1. Find companies currently owned by Moyano
    owned = session.query(Empresa).filter(Empresa.owner_id == MOYANO_USER_ID).all()
    
    count_fixed = 0
    for emp in owned:
        if emp.id not in ALLOWED_IDS:
            print(f" -> UNLINKING: {emp.razon_social} (ID: {emp.id})")
            
            # A. Remove Ownership
            emp.owner_id = None
            
            # B. Remove from Dashboard (usuario_empresas)
            session.execute(
                text("DELETE FROM usuario_empresas WHERE usuario_id=:u AND empresa_id=:e"),
                {"u": MOYANO_USER_ID, "e": emp.id}
            )
            count_fixed += 1
        else:
            print(f" -> KEEPING: {emp.razon_social} (ID: {emp.id})")
            
    session.commit()
    print(f"Fixed {count_fixed} companies. They should now appear in 'Mis Empresas' (Support) and NOT in the Accountant's list.")

if __name__ == "__main__":
    fix_assignments()
