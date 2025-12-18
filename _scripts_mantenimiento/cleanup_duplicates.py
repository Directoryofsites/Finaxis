#!/usr/bin/env python3
# Script para limpiar empresas duplicadas en kiro_clean_db

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.usuario import Usuario

def cleanup_duplicate_companies():
    """
    Limpia empresas duplicadas dejando solo 1 'Empresa de Demostración'
    SOLO opera en kiro_clean_db (base de datos de Kiro)
    """
    db = SessionLocal()
    try:
        print("🧹 Iniciando limpieza de empresas duplicadas en kiro_clean_db...")
        
        # Buscar todas las empresas de demostración
        empresas_demo = db.query(Empresa).filter(
            Empresa.razon_social == "Empresa de Demostración"
        ).all()
        
        print(f"📊 Encontradas {len(empresas_demo)} empresas de demostración")
        
        if len(empresas_demo) <= 1:
            print("✅ No hay duplicados que limpiar")
            return
        
        # Mantener la primera empresa, eliminar el resto
        empresa_a_mantener = empresas_demo[0]
        empresas_a_eliminar = empresas_demo[1:]
        
        print(f"🔒 Manteniendo empresa ID: {empresa_a_mantener.id}")
        print(f"🗑️  Eliminando {len(empresas_a_eliminar)} empresas duplicadas...")
        
        # Eliminar usuarios asociados a las empresas duplicadas
        for empresa in empresas_a_eliminar:
            usuarios_asociados = db.query(Usuario).filter(
                Usuario.empresa_id == empresa.id
            ).all()
            
            print(f"   - Eliminando {len(usuarios_asociados)} usuarios de empresa ID {empresa.id}")
            for usuario in usuarios_asociados:
                db.delete(usuario)
            
            print(f"   - Eliminando empresa ID {empresa.id}: {empresa.razon_social}")
            db.delete(empresa)
        
        # Buscar y eliminar otras empresas que no sean la de demostración principal
        otras_empresas = db.query(Empresa).filter(
            Empresa.razon_social != "Empresa de Demostración"
        ).all()
        
        if otras_empresas:
            print(f"🗑️  Eliminando {len(otras_empresas)} empresas adicionales...")
            for empresa in otras_empresas:
                # Eliminar usuarios asociados
                usuarios_asociados = db.query(Usuario).filter(
                    Usuario.empresa_id == empresa.id
                ).all()
                
                for usuario in usuarios_asociados:
                    print(f"   - Eliminando usuario: {usuario.email}")
                    db.delete(usuario)
                
                print(f"   - Eliminando empresa: {empresa.razon_social}")
                db.delete(empresa)
        
        db.commit()
        
        # Verificar resultado final
        empresas_restantes = db.query(Empresa).all()
        usuarios_restantes = db.query(Usuario).all()
        
        print("\n✅ Limpieza completada!")
        print(f"📊 Empresas restantes: {len(empresas_restantes)}")
        for empresa in empresas_restantes:
            print(f"   - {empresa.razon_social} (ID: {empresa.id})")
        
        print(f"👥 Usuarios restantes: {len(usuarios_restantes)}")
        for usuario in usuarios_restantes:
            empresa_nombre = usuario.empresa.razon_social if usuario.empresa else "Sin empresa"
            print(f"   - {usuario.email} ({empresa_nombre})")
            
    except Exception as e:
        print(f"❌ ERROR durante la limpieza: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_duplicate_companies()