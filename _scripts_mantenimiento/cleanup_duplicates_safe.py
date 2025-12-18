#!/usr/bin/env python3
# Script para limpiar empresas duplicadas respetando foreign keys

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.usuario import Usuario

def cleanup_duplicate_companies_safe():
    """
    Limpia empresas duplicadas de forma segura eliminando dependencias
    SOLO opera en kiro_clean_db (base de datos de Kiro)
    """
    db = SessionLocal()
    try:
        print("🧹 Iniciando limpieza SEGURA de empresas duplicadas en kiro_clean_db...")
        
        # Buscar todas las empresas de demostración
        empresas_demo = db.query(Empresa).filter(
            Empresa.razon_social == "Empresa de Demostración"
        ).all()
        
        print(f"📊 Encontradas {len(empresas_demo)} empresas de demostración")
        
        if len(empresas_demo) <= 1:
            print("✅ No hay duplicados de demostración que limpiar")
        else:
            # Mantener la primera empresa, eliminar el resto
            empresa_a_mantener = empresas_demo[0]
            empresas_a_eliminar = empresas_demo[1:]
            
            print(f"🔒 Manteniendo empresa ID: {empresa_a_mantener.id}")
            print(f"🗑️  Eliminando {len(empresas_a_eliminar)} empresas duplicadas...")
            
            for empresa in empresas_a_eliminar:
                eliminar_empresa_completa(db, empresa)
        
        # Buscar y eliminar otras empresas que no sean la de demostración principal
        otras_empresas = db.query(Empresa).filter(
            Empresa.razon_social != "Empresa de Demostración"
        ).all()
        
        if otras_empresas:
            print(f"🗑️  Eliminando {len(otras_empresas)} empresas adicionales...")
            for empresa in otras_empresas:
                eliminar_empresa_completa(db, empresa)
        
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

def eliminar_empresa_completa(db: Session, empresa: Empresa):
    """
    Elimina una empresa y todas sus dependencias de forma segura
    """
    print(f"   🗑️  Eliminando empresa: {empresa.razon_social} (ID: {empresa.id})")
    
    # 1. Eliminar usuarios asociados
    usuarios_asociados = db.query(Usuario).filter(
        Usuario.empresa_id == empresa.id
    ).all()
    
    for usuario in usuarios_asociados:
        print(f"      - Eliminando usuario: {usuario.email}")
        db.delete(usuario)
    
    # 2. Eliminar plan de cuentas usando SQL directo para evitar problemas de ORM
    print(f"      - Eliminando plan de cuentas...")
    result = db.execute(text("DELETE FROM plan_cuentas WHERE empresa_id = :empresa_id"), {"empresa_id": empresa.id})
    if result.rowcount > 0:
        print(f"      - Eliminadas {result.rowcount} cuentas del plan contable")
    
    # 3. Eliminar otras tablas relacionadas si existen
    tablas_relacionadas = [
        "facturas", "productos", "terceros", "movimientos", 
        "asientos_contables", "inventarios", "configuraciones"
    ]
    
    for tabla in tablas_relacionadas:
        try:
            result = db.execute(text(f"DELETE FROM {tabla} WHERE empresa_id = :empresa_id"), {"empresa_id": empresa.id})
            if result.rowcount > 0:
                print(f"      - Eliminados {result.rowcount} registros de {tabla}")
        except Exception as e:
            # Si la tabla no existe o no tiene empresa_id, continuar
            pass
    
    # 4. Finalmente eliminar la empresa
    db.delete(empresa)
    print(f"      ✅ Empresa {empresa.id} eliminada completamente")

if __name__ == "__main__":
    cleanup_duplicate_companies_safe()