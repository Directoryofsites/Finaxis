from app.core.database import SessionLocal
from app.models.usuario import Usuario, usuario_empresas
from app.models.empresa import Empresa
from app.services.empresa import delete_empresa, create_empresa_con_usuarios
from app.schemas.empresa import EmpresaConUsuariosCreate
from datetime import date

db = SessionLocal()

try:
    print("--- VERIFYING FIX ---")
    
    # 1. Create Dummy Owner (if not exists)
    owner = db.query(Usuario).filter(Usuario.email == "test_owner@verif.com").first()
    if not owner:
        print("Creating Test Owner...")
        # Assume we can create a simple user or just pick one existing... 
        # Actually safer to create one to avoid messing up real data.
        # But creating user requires password hash etc.
        # Let's borrow an existing admin for the test, stripping them later?
        # Better: use 'Moyano' since we know he exists.
        owner = db.query(Usuario).filter(Usuario.nombre_completo.ilike("%Moyano%")).first()
        
    print(f"Using Owner: {owner.email} (ID: {owner.id})")
    
    # 2. Create Dummy Company
    print("Creating Test Company...")
    # Create dummy user structure that matches the schema expectation
    # Schema expects objs with email, password, roles (or at least email/password for creation logic)
    # Fetch a valid role
    from app.models.permiso import Rol
    rol = db.query(Rol).first()
    if not rol: raise Exception("No roles in DB")
    
    # Pass as dict
    emp_data = EmpresaConUsuariosCreate(
        razon_social="Test Delete Me",
        nit="999999999",
        fecha_inicio_operaciones=date.today(),
        email="test@test.com",
        direccion="Test Dir",
        telefono="123",
        usuarios=[{"email": "dummy@test.com", "password": "password123", "roles_ids": [rol.id]}] 
    )
    
    # Manually create to ensure we control the linking
    try:
        new_emp = create_empresa_con_usuarios(db, emp_data, owner_id=owner.id)
        print(f"Created Company: {new_emp.razon_social} (ID: {new_emp.id})")
        
        # 3. VERIFY LINK EXISTS
        from sqlalchemy import text
        stmt = text("SELECT * FROM usuario_empresas WHERE empresa_id = :eid AND usuario_id = :uid")
        link = db.execute(stmt, {"eid": new_emp.id, "uid": owner.id}).fetchone()
        
        if link:
            print("Verified: Owner is linked in usuario_empresas.")
        else:
            print("WARNING: Owner NOT linked automatically (maybe logic differs). Force linking...")
            stmt_ins = text("INSERT INTO usuario_empresas (usuario_id, empresa_id, is_owner) VALUES (:uid, :eid, 1)")
            db.execute(stmt_ins, {"uid": owner.id, "eid": new_emp.id})
            db.commit()
            print("Forced link created.")
            
        # 4. ATTEMPT DELETE
        print("Attempting Delete...")
        result = delete_empresa(db, new_emp.id)
        
        if result:
            print("Delete returned True.")
            # Check DB
            check = db.query(Empresa).filter(Empresa.id == new_emp.id).first()
            if not check:
                print("SUCCESS: Company is gone from DB.")
                
                # Check link
                link_check = db.execute(stmt, {"eid": new_emp.id, "uid": owner.id}).fetchone()
                if not link_check:
                     print("SUCCESS: Link is gone from DB.")
                else:
                     print("FAILURE: Link still exists!")
            else:
                print("FAILURE: Company still exists in DB!")
        else:
            print("FAILURE: Delete returned False.")
            
    except Exception as e:
        print(f"CREATION/TEST ERROR: {e}")
        # Cleanup if needed
        import traceback
        traceback.print_exc()

finally:
    # Cleanup if needed (if delete failed, manual cache cleanup)
    pass
    db.close()
