
from sqlalchemy.orm import Session
import sys
import os

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.usuario import Usuario
from app.models.empresa import Empresa
from app.models.produccion import Receta, OrdenProduccion

def fix_support_and_data():
    db = SessionLocal()
    try:
        # 1. Get Support User
        support_user = db.query(Usuario).filter(Usuario.email == "soporte@soporte.com").first()
        if not support_user:
            print("[x] User 'soporte@soporte.com' not found.")
            return

        print(f"User found: {support_user.email} (Current Empresa ID: {support_user.empresa_id})")

        # 2. Get Target Company
        empresa = db.query(Empresa).first()
        if not empresa:
            print("[x] No companies found.")
            return
        
        print(f"Target Company found: {empresa.razon_social} (ID: {empresa.id})")

        # 3. Fix User
        if support_user.empresa_id != empresa.id:
            support_user.empresa_id = empresa.id
            db.add(support_user)
            print(f"[OK] Updated support user to belong to Company {empresa.id}")
        else:
            print("[INFO] Support user already belongs to the target company.")

        # 4. Fix Orphaned Production Data 
        orphaned_recetas = db.query(Receta).filter((Receta.empresa_id == None)).all()
        print(f"Found {len(orphaned_recetas)} orphaned Recetas.")
        for r in orphaned_recetas:
            r.empresa_id = empresa.id
            db.add(r)
        
        orphaned_ordenes = db.query(OrdenProduccion).filter((OrdenProduccion.empresa_id == None)).all()
        print(f"Found {len(orphaned_ordenes)} orphaned Ordenes.")
        for o in orphaned_ordenes:
            o.empresa_id = empresa.id
            db.add(o)

        db.commit()
        print("[OK] Data Fix Completed Successfully.")

        # 5. Verify Content
        count_recetas = db.query(Receta).filter(Receta.empresa_id == empresa.id).count()
        count_ordenes = db.query(OrdenProduccion).filter(OrdenProduccion.empresa_id == empresa.id).count()
        print(f"Final Totals for Company {empresa.id}:")
        print(f"   - Recetas: {count_recetas}")
        print(f"   - Ordenes: {count_ordenes}")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_support_and_data()
