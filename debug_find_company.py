import sys
import os
from sqlalchemy import text

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.usuario import Usuario

def find_verduras():
    db = SessionLocal()
    print("="*60)
    print("BUSQUEDA DE EMPRESA POR NOMBRE: 'Verduras'")
    print("="*60)

    # Buscar empresas que contengan "Verduras" en razon_social
    empresas = db.query(Empresa).filter(Empresa.razon_social.ilike("%Verduras%")).all()

    if not empresas:
        print("(!) NO se encontraron empresas con 'Verduras' en la Razon Social.")
        # Fallback: Listar TODAS las empresas
        print("\nListando TODAS las empresas disponibles:")
        all_empresas = db.query(Empresa).all()
        for e in all_empresas:
             print(f"   > ID: {e.id} | Razon Social: {e.razon_social}")
    
    for e in empresas:
        print(f"\n[ENCONTRADA] ID: {e.id} | Razon Social: '{e.razon_social}'")
        
        # Buscar usuarios asociados a esta empresa
        usuarios = db.query(Usuario).filter(Usuario.empresa_id == e.id).all()
        print(f"   Usuarios asociados ({len(usuarios)}):")
        for u in usuarios:
            print(f"   - ID: {u.id} | Email: {u.email}")

if __name__ == "__main__":
    find_verduras()
