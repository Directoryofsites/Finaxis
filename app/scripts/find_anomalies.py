from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import empresa as empresa_model
from app.models import usuario as usuario_model
from sqlalchemy import or_

def list_candidates():
    db: Session = SessionLocal()
    try:
        print("--- BUSQUEDA DIAGNOSTICA AMPLIA ---")
        
        # 1. Buscar Empresas (Broad search)
        print("\n[EMPRESAS]")
        empresas = db.query(empresa_model.Empresa).filter(
            or_(
                empresa_model.Empresa.razon_social.ilike("%pan%"),
                empresa_model.Empresa.razon_social.ilike("%20%"),
                empresa_model.Empresa.nit.ilike("%prueba%")
            )
        ).all()
        
        if empresas:
            for e in empresas:
                print(f"ID: {e.id} | NIT: {e.nit} | Nombre: '{e.razon_social}' | Owner: {e.owner_id}")
        else:
            print("No se encontraron empresas con 'pan', '20' o 'prueba'.")

        # 2. Buscar Usuarios (Broad search)
        print("\n[USUARIOS]")
        usuarios = db.query(usuario_model.Usuario).filter(
            or_(
                usuario_model.Usuario.nombre_completo.ilike("%prueba%"),
                usuario_model.Usuario.email.ilike("%prueba%"),
                usuario_model.Usuario.nombre_completo.ilike("%contador%")
            )
        ).all()
        
        if usuarios:
            for u in usuarios:
                print(f"ID: {u.id} | Email: {u.email} | Nombre: '{u.nombre_completo}'")
        else:
            print("No se encontraron usuarios con 'prueba' o 'contador'.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    list_candidates()
