from app.core.database import SessionLocal
from app.models.usuario import usuario_empresas
from sqlalchemy import text

session = SessionLocal()

def clean_dashboard_links():
    MOYANO_USER_ID = 48
    ALLOWED_IDS = [152, 153] # bILLARES LA 40, Iglesia la 33
    
    print(f"--- Cleaning Dashboard Links for User {MOYANO_USER_ID} ---")
    
    # 1. Fetch current links
    result = session.execute(
        text("SELECT empresa_id FROM usuario_empresas WHERE usuario_id = :u"),
        {"u": MOYANO_USER_ID}
    ).fetchall()
    
    current_ids = [row[0] for row in result]
    print(f"Current Dashboard Companies: {current_ids}")
    
    # 2. Identify Extras
    extras = [eid for eid in current_ids if eid not in ALLOWED_IDS]
    
    if extras:
        print(f"Found {len(extras)} EXTRA companies to remove: {extras}")
        
        # 3. Remove Extras
        if extras:
            # SQLAlchemy text needs tuple or list handling carefully
            # We'll just loop for safety and clarity
            for eid in extras:
                print(f" -> Removing Link to Company ID {eid}...")
                session.execute(
                    text("DELETE FROM usuario_empresas WHERE usuario_id=:u AND empresa_id=:e"),
                    {"u": MOYANO_USER_ID, "e": eid}
                )
            session.commit()
            print("Cleanup Complete.")
    else:
        print("No extra links found. Dashboard should match.")

if __name__ == "__main__":
    clean_dashboard_links()
