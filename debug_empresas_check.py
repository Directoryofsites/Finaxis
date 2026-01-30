
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.usuario import Usuario, usuario_empresas
from app.models.empresa import Empresa
from app.models.permiso import Rol
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def debug_empresas():
    db = SessionLocal()
    try:
        print("\n=== REVISIÓN DE CONTADORES Y SUS EMPRESAS ===\n")
        
        # 1. Encontrar usuarios con rol 'contador'
        contadores = db.query(Usuario).join(Usuario.roles).filter(Rol.nombre.ilike('contador')).all()
        
        if not contadores:
            print("No se encontraron usuarios con rol 'contador'.")
            return

        for c in contadores:
            print(f"Contador: {c.email} (ID: {c.id})")
            print(f"  Empresa Holding (empresa_id): {c.empresa_id}")
            
            # Empresas Asignadas vía usuario_empresas
            asignadas = db.query(Empresa).join(usuario_empresas).filter(usuario_empresas.c.usuario_id == c.id).all()
            print(f"  Empresas Asignadas (N:M): {[ (e.id, e.razon_social) for e in asignadas ]}")
            
            # Empresas donde es Owner
            owned = db.query(Empresa).filter(Empresa.owner_id == c.id).all()
            print(f"  Empresas que POSEE (owner_id): {[ (e.id, e.razon_social) for e in owned ]}")
            
            # Empresas Hijas de su Holding
            if c.empresa_id:
                hijas = db.query(Empresa).filter(Empresa.padre_id == c.empresa_id).all()
                print(f"  Empresas Hijas del Holding: {[ (e.id, e.razon_social) for e in hijas ]}")
            print("-" * 50)
            
        print("\n=== REVISIÓN DE ORIFANATO DE EMPRESAS ===\n")
        # Empresas con owner que es contador pero no están asignadas
        # O simplemente listar todas las empresas y sus owners
        todas = db.query(Empresa).all()
        for e in todas:
            if e.owner_id or e.padre_id:
                print(f"Empresa: {e.razon_social} (ID: {e.id})")
                print(f"  Owner: {e.owner_id} | Padre: {e.padre_id}")
                
    finally:
        db.close()

if __name__ == "__main__":
    debug_empresas()
