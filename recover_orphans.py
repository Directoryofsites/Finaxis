from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.usuario import Usuario, usuario_empresas
from sqlalchemy import text

session = SessionLocal()

def recover_companies():
    # New User ID from previous step is 48
    NEW_USER_ID = 48
    OLD_USER_ID = 34
    
    print(f"--- Recovering Companies for User {NEW_USER_ID} (Replacing Old {OLD_USER_ID}) ---")
    
    # 1. Find Companies that were owned by Old ID 
    # (assuming owner_id wasn't set to NULL by some cascade, but usually it might set NULL or stay)
    # Let's check both ID 34 and NULL but created recently or matching expected profile?
    # Or maybe the deletion logic cleared 'owner_id' for shared users?
    # In my previous fix, I set `u.empresa_id = None` on the USER, but I didn't touch the Company Owner ID logic 
    # unless companies were deleted.
    # But wait, user was DELETED originally. If user was deleted, what happened to `owner_id` in companies?
    # If `owner_id` is a FK with Set Null, they are now None.
    # If No Action, they might still be 34 (orphan) or failed.
    
    # Let's search for companies with owner_id = 34
    orphaned_by_id = session.query(Empresa).filter(Empresa.owner_id == OLD_USER_ID).all()
    
    # Also search for companies with owner_id = None that might belong to him?
    # This is risky. Let's start with ID 34.
    
    print(f"Found {len(orphaned_by_id)} orphaned companies (owner_id={OLD_USER_ID}).")
    
    
    # 2. Update Owner ID to New User
    if orphaned_by_id:
        for emp in orphaned_by_id:
            print(f" -> Reclaiming: {emp.razon_social} (ID: {emp.id})")
            emp.owner_id = NEW_USER_ID
            
            # 3. Add to usuario_empresas (dashboard visibility)
            # Check if link exists
            exists = session.execute(
                text("SELECT 1 FROM usuario_empresas WHERE usuario_id=:u and empresa_id=:e"),
                {"u": NEW_USER_ID, "e": emp.id}
            ).fetchone()
            
            if not exists:
                session.execute(
                    text("INSERT INTO usuario_empresas (usuario_id, empresa_id, is_owner) VALUES (:u, :e, :o)"),
                    {"u": NEW_USER_ID, "e": emp.id, "o": True}
                )
                print("    [+] Link added to dashboard.")
                
        session.commit()
    else:
        print("No orphaned companies found by ID 34. Searching for owner_id IS NULL...")
        orphans_null = session.query(Empresa).filter(Empresa.owner_id == None).all()
        print(f"Found {len(orphans_null)} potential companies:")
        
        target_names = ["Moya", "Merca", "Iglesia", "Verduras"] # Keywords based on user context
        
        candidates = []
        for c in orphans_null:
             # Heuristic: Filter by likely names or system templates
             # If it's a template, we skip? No, maybe he owned templates.
             print(f" - {c.razon_social} (ID: {c.id}) [Is Template: {c.is_template}]")
             
             # If it looks like a user company, add to candidates
             # Assume NON-TEMPLATE + NULL OWNER = Orphaned User Company (System companies usually have special flag or name)
             if not c.is_template:
                 candidates.append(c)
        
        if candidates:
            print(f"\nReclaiming {len(candidates)} companies for User {NEW_USER_ID}...")
            for c in candidates:
                c.owner_id = NEW_USER_ID
                exists = session.execute(
                    text("SELECT 1 FROM usuario_empresas WHERE usuario_id=:u and empresa_id=:e"),
                    {"u": NEW_USER_ID, "e": c.id}
                ).fetchone()
                if not exists:
                    session.execute(
                        text("INSERT INTO usuario_empresas (usuario_id, empresa_id, is_owner) VALUES (:u, :e, :o)"),
                        {"u": NEW_USER_ID, "e": c.id, "o": True}
                    )
            session.commit()
            print("Done.")

if __name__ == "__main__":
    recover_companies()
