import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.permiso import Rol, Permiso

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_permissions():
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 1. Find the 'administrador' role
        admin_role = db.query(Rol).filter(Rol.nombre == "administrador").first()
        if not admin_role:
            logger.error("Role 'administrador' not found!")
            return

        logger.info(f"Role 'administrador' found. Current permissions count: {len(admin_role.permisos)}")

        # 2. Get ALL available permissions
        all_perms = db.query(Permiso).all()
        logger.info(f"Total available system permissions: {len(all_perms)}")

        # 3. Grant all permissions to admin role
        current_perm_ids = {p.id for p in admin_role.permisos}
        added_count = 0
        
        for perm in all_perms:
            if perm.id not in current_perm_ids:
                admin_role.permisos.append(perm)
                added_count += 1
        
        db.commit()
        logger.info(f"SUCCESS: Added {added_count} new permissions to 'administrador' role.")

    except Exception as e:
        logger.error(f"Error updating permissions: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_permissions()
