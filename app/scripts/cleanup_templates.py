from app.core.database import SessionLocal
from app.models.empresa import Empresa

db = SessionLocal()

def list_templates():
    print("\n--- CURRENT TEMPLATES ---")
    templates = db.query(Empresa).filter(Empresa.is_template == True).all()
    for t in templates:
        print(f"ID: {t.id} | Name: '{t.razon_social}' | Category: {t.template_category} | Owner: {t.owner_id}")
    return templates

def delete_by_ids(ids):
    if not ids: return
    print(f"\nBluetooth deleting IDs: {ids}...")
    db.query(Empresa).filter(Empresa.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    print("Done.")

try:
    tpls = list_templates()
    
    # Identify IDs to delete based on User Request
    # User said: "PLANTILLA RETAIL", "PLANTILLA SERVICIOS", "PLANTILLA PROPIEDAD HORIZONTAL"
    # Keep "Comercio (Plantilla)"
    
    ids_to_delete = []
    for t in tpls:
        name_upper = t.razon_social.upper()
        if "RETAIL" in name_upper or "SERVICIOS" in name_upper or "PROPIEDAD HORIZONTAL" in name_upper:
            # Double check it's not the one we want to keep
            if "COMERCIO (PLANTILLA)" not in name_upper: 
                ids_to_delete.append(t.id)
                
    if ids_to_delete:
        delete_by_ids(ids_to_delete)
        list_templates()
    else:
        print("\nNo matching templates found to delete.")

finally:
    db.close()
