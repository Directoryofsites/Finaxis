
import sys
sys.path.append('c:\\ContaPY2')
from app.core.database import SessionLocal
from app.models.permiso import Rol
from app.models.usuario import usuario_roles  # Tabla intermedia
from sqlalchemy import text

def consolidate_admin_roles():
    session = SessionLocal()
    try:
        # IDs conocidos por diagnóstico previo
        MAIN_ADMIN_ID = 16  # "Administrador" (Target)
        DUPLICATE_ADMIN_ID = 24  # "administrador" (To Delete)

        print(f"--- Iniciando migración de ID {DUPLICATE_ADMIN_ID} (Old) a ID {MAIN_ADMIN_ID} (New) ---")

        # 1. Obtener usuarios con el rol antiguo
        # Consultamos directamente la tabla intermedia
        query_users_old = text("SELECT usuario_id FROM usuario_roles WHERE rol_id = :rid")
        users_old = session.execute(query_users_old, {"rid": DUPLICATE_ADMIN_ID}).fetchall()
        
        users_to_migrate = [row[0] for row in users_old]
        print(f"Usuarios encontrados en rol antiguo: {len(users_to_migrate)}")

        migrated_count = 0
        for uid in users_to_migrate:
            # Verificar si ya tienen el rol nuevo
            check_new = text("SELECT count(*) FROM usuario_roles WHERE usuario_id = :uid AND rol_id = :rid")
            count_new = session.execute(check_new, {"uid": uid, "rid": MAIN_ADMIN_ID}).scalar()
            
            if count_new == 0:
                # Insertar nuevo rol
                insert_stmt = text("INSERT INTO usuario_roles (usuario_id, rol_id) VALUES (:uid, :rid)")
                session.execute(insert_stmt, {"uid": uid, "rid": MAIN_ADMIN_ID})
                migrated_count += 1
                # print(f"Usuario {uid} migrado.")
            else:
                # print(f"Usuario {uid} ya tenía el rol nuevo.")
                pass

        session.commit()
        print(f"Se migraron {migrated_count} usuarios al rol 'Administrador'.")

        # 2. Borrar asociaciones del rol antiguo
        # A) Tabla intermedia usuario_roles
        delete_assoc_stmt = text("DELETE FROM usuario_roles WHERE rol_id = :rid")
        session.execute(delete_assoc_stmt, {"rid": DUPLICATE_ADMIN_ID})
        
        # B) Tabla intermedia rol_permisos (Causa del error FK)
        delete_perm_stmt = text("DELETE FROM rol_permisos WHERE rol_id = :rid")
        session.execute(delete_perm_stmt, {"rid": DUPLICATE_ADMIN_ID})
        
        # 3. Borrar el rol antiguo
        delete_role_stmt = text("DELETE FROM roles WHERE id = :rid")
        session.execute(delete_role_stmt, {"rid": DUPLICATE_ADMIN_ID})
        
        session.commit()
        print(f"✅ Rol ID {DUPLICATE_ADMIN_ID} ('administrador') eliminado correctamente.")

    except Exception as e:
        print(f"❌ Error durante la consolidación: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    consolidate_admin_roles()
