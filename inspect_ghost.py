from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.usuario import usuario_empresas
from sqlalchemy import text

session = SessionLocal()

def inspect_ghost_company():
    COMP_ID = 153 # Iglesia la 33
    USER_ID = 48  # Moyano
    
    print(f"--- Inspecting Ghost Company {COMP_ID} ---")
    
    # 1. Does the company exist?
    comp = session.query(Empresa).filter(Empresa.id == COMP_ID).first()
    if comp:
        print(f"[!] Company FOUND in DB: {comp.razon_social}")
        print(f"    Owner ID: {comp.owner_id}")
        print(f"    Padre ID: {comp.padre_id}")
    else:
        print(f"[OK] Company NOT found in DB (Correctly deleted?).")
        
    # 2. Check the link
    link = session.execute(
        text("SELECT * FROM usuario_empresas WHERE usuario_id=:u AND empresa_id=:e"),
        {"u": USER_ID, "e": COMP_ID}
    ).fetchone()
    
    if link:
        print(f"[!] Link FOUND in usuario_empresas: {link}")
    else:
        print("[OK] Link NOT found in usuario_empresas.")

if __name__ == "__main__":
    inspect_ghost_company()
