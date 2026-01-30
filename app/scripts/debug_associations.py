from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.usuario import Usuario, usuario_empresas
from app.models.empresa import Empresa

def debug_associations():
    db = SessionLocal()
    try:
        user = db.query(Usuario).filter(Usuario.email == 'contador@ejemplo.com').first()
        if not user:
            print("User contador not found")
            return

        print(f"User: {user.email} (ID: {user.id})")
        print(f"Roles: {[r.nombre for r in user.roles]}")
        print(f"Empresa ID (Main): {user.empresa_id}")
        
        # --- FIX: REPARAR ASOCIACIONES PERDIDAS ---
        print("\n--- REPARANDO ASOCIACIONES ---")
        companies_to_fix = [144, 145] # Ferreteria y Panaderia
        
        for cid in companies_to_fix:
            emp = db.query(Empresa).filter(Empresa.id == cid).first()
            if emp:
                print(f"Reparando empresa {emp.razon_social}...")
                # 1. Update Owner
                emp.owner_id = user.id
                db.add(emp)
                
                # 2. Insert into Association Table (if not exists)
                exists = db.execute(usuario_empresas.select().where(
                    (usuario_empresas.c.usuario_id == user.id) &
                    (usuario_empresas.c.empresa_id == cid)
                )).first()
                
                if not exists:
                     stmt = usuario_empresas.insert().values(usuario_id=user.id, empresa_id=cid, is_owner=True)
                     db.execute(stmt)
                     print(" -> Link creado.")
                else:
                     print(" -> Link ya existía.")
        
        db.commit()
        print("--- REPARACIÓN COMPLETADA ---")

        print("\n--- Empresas Asignadas (ORM) ---")
        db.refresh(user) # Refresh to see changes
        for emp in user.empresas_asignadas:
            print(f"- {emp.razon_social} (ID: {emp.id})")
            
        print("\n--- Tabla Intermedia (Raw) ---")
        rows = db.execute(usuario_empresas.select()).fetchall()
        for row in rows:
            print(row)
            
        print("\n--- Todas las Empresas ---")
        all_emps = db.query(Empresa).all()
        for e in all_emps:
            print(f"ID: {e.id}, Razon: {e.razon_social}, OwnerID: {e.owner_id}, PadreID: {e.padre_id}")
            
    finally:
        db.close()

if __name__ == "__main__":
    debug_associations()
