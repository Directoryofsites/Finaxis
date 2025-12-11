#!/usr/bin/env python3
# Script para verificar el estado final de la base de datos

from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.usuario import Usuario

def check_database_state():
    """Verificar el estado final de la base de datos"""
    db = SessionLocal()
    try:
        # Contar empresas
        empresas = db.query(Empresa).all()
        print(f"📊 Empresas: {len(empresas)}")
        for empresa in empresas:
            print(f"   - {empresa.razon_social} (ID: {empresa.id})")
        
        # Contar usuarios
        usuarios = db.query(Usuario).all()
        print(f"👥 Usuarios: {len(usuarios)}")
        for usuario in usuarios:
            empresa_nombre = usuario.empresa.razon_social if usuario.empresa else "Sin empresa"
            print(f"   - {usuario.email} ({empresa_nombre})")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_database_state()