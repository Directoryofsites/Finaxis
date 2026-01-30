from app.core.database import SessionLocal
from app.models.usuario import Usuario, usuario_roles
from app.models.permiso import Rol
from app.core.hashing import get_password_hash # If available, or use a known hash helper
from datetime import datetime

session = SessionLocal()

def check_and_restore_user():
    print("--- Checking Status of User 'moyano@moyano.com' ---")
    
    user = session.query(Usuario).filter(Usuario.email == "moyano@moyano.com").first()
    
    if user:
        print(f"User FOUND: {user.email} (ID: {user.id})")
        print(f"Empresa ID: {user.empresa_id}")
    else:
        print("!! User NOT FOUND. Attempting RESTORE...")
        
        # We need to recreate the user. 
        # We might not know the exact password, but we can set a temporary one or try to use a default.
        # Assuming dev environment permissions.
        
        # 1. Get a Role (Contador)
        rol_contador = session.query(Rol).filter(Rol.nombre == "contador").first()
        if not rol_contador:
            print("Role 'contador' not found. Creating it...")
            rol_contador = Rol(nombre="contador", descripcion="Role for accountants")
            session.add(rol_contador)
            session.flush()

        # 2. Create User
        # We need a safe fallback for password. 
        # Since we don't have the hashing lib easily imported without full context, 
        # let's try to assume we can import it or use a placeholder if hashing is handled by model setter (unlikely).
        from app.core.hashing import get_password_hash
        hashed_pw = get_password_hash("123456") # Temporary password
        
        # Restore to a safe Company ID or None?
        # If Company 149 is gone, we should set to None or another company.
        # Let's verify if Company 149 exists
        from app.models.empresa import Empresa
        comp_149 = session.query(Empresa).filter(Empresa.id == 149).first()
        
        target_empresa_id = None
        if comp_149:
             print("Company 149 still exists.")
             target_empresa_id = 149
        else:
             print("Company 149 DELETED. Setting user to No Company.")
             
        new_user = Usuario(
            email="moyano@moyano.com",
            nombre_completo="Moyano (Restored)",
            password_hash=hashed_pw,
            empresa_id=target_empresa_id,
            created_at=datetime.utcnow()
        )
        
        session.add(new_user)
        session.flush()
        print(f"User Restored with ID: {new_user.id}")
        
        # 3. Assign Role using direct insert if relationship fails or via relationship
        # Let's try direct relationship append
        new_user.roles.append(rol_contador)
        
        session.commit()
        print("User RESTORED successfully. Password set to '123456'.")

if __name__ == "__main__":
    check_and_restore_user()
