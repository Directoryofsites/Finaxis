#!/usr/bin/env python3
"""
Script específico para diagnosticar el problema del usuario moyano@moyano.com
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker, joinedload
from app.core.database import engine
from app.models.usuario import Usuario, usuario_empresas
from app.models.empresa import Empresa
from app.models.permiso import Rol
from app.services.empresa import get_empresas_para_usuario

def main():
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("DIAGNÓSTICO ESPECÍFICO: Usuario moyano@moyano.com")
        print("=" * 80)
        
        # 1. Buscar el usuario moyano
        moyano = db.query(Usuario).filter(
            Usuario.email == 'moyano@moyano.com'
        ).options(joinedload(Usuario.roles)).first()
        
        if not moyano:
            print("❌ Usuario moyano@moyano.com no encontrado")
            return
        
        print(f"✅ Usuario encontrado:")
        print(f"  - ID: {moyano.id}")
        print(f"  - Email: {moyano.email}")
        print(f"  - Empresa ID: {moyano.empresa_id}")
        print(f"  - Roles: {[rol.nombre for rol in moyano.roles]}")
        
        # 2. Buscar la empresa "Moyano"
        empresa_moyano = db.query(Empresa).filter(
            Empresa.razon_social.ilike('%moyano%')
        ).first()
        
        if empresa_moyano:
            print(f"\n✅ Empresa 'Moyano' encontrada:")
            print(f"  - ID: {empresa_moyano.id}")
            print(f"  - Razón Social: {empresa_moyano.razon_social}")
            print(f"  - NIT: {empresa_moyano.nit}")
            print(f"  - Owner ID: {empresa_moyano.owner_id}")
            print(f"  - Padre ID: {empresa_moyano.padre_id}")
        
        # 3. Buscar TODAS las empresas que debería ver moyano
        print(f"\n🔍 ANÁLISIS DETALLADO DE ACCESO PARA MOYANO:")
        print("-" * 60)
        
        # 3.1 Empresas donde es owner
        empresas_owner = db.query(Empresa).filter(
            Empresa.owner_id == moyano.id
        ).all()
        
        print(f"📊 Empresas donde Moyano es owner: {len(empresas_owner)}")
        for emp in empresas_owner:
            print(f"  - {emp.razon_social} (ID: {emp.id})")
        
        # 3.2 Su empresa principal
        if moyano.empresa_id:
            emp_principal = db.query(Empresa).filter(
                Empresa.id == moyano.empresa_id
            ).first()
            if emp_principal:
                print(f"📊 Su empresa principal: {emp_principal.razon_social} (ID: {emp_principal.id})")
        
        # 3.3 Empresas asignadas via usuario_empresas
        relaciones = db.execute(
            usuario_empresas.select().where(
                usuario_empresas.c.usuario_id == moyano.id
            )
        ).fetchall()
        
        print(f"📊 Relaciones en usuario_empresas: {len(relaciones)}")
        for rel in relaciones:
            empresa = db.query(Empresa).filter(Empresa.id == rel.empresa_id).first()
            if empresa:
                print(f"  - {empresa.razon_social} (ID: {empresa.id}, is_owner: {rel.is_owner})")
        
        # 3.4 Empresas hijas (si es holding)
        if moyano.empresa_id:
            empresas_hijas = db.query(Empresa).filter(
                Empresa.padre_id == moyano.empresa_id
            ).all()
            print(f"📊 Empresas hijas: {len(empresas_hijas)}")
            for emp in empresas_hijas:
                print(f"  - {emp.razon_social} (ID: {emp.id})")
        
        # 4. Probar la función actual
        print(f"\n🧪 RESULTADO DE get_empresas_para_usuario:")
        print("-" * 60)
        
        empresas_visibles = get_empresas_para_usuario(db, moyano)
        print(f"✅ Empresas que puede ver actualmente: {len(empresas_visibles)}")
        for emp in empresas_visibles:
            print(f"  - {emp.razon_social} (ID: {emp.id})")
        
        # 5. Buscar empresas que DEBERÍA poder crear
        print(f"\n🔍 EMPRESAS QUE MOYANO PODRÍA HABER CREADO:")
        print("-" * 60)
        
        # Buscar empresas creadas recientemente que no tienen owner
        empresas_sin_owner = db.query(Empresa).filter(
            Empresa.owner_id.is_(None)
        ).order_by(Empresa.created_at.desc()).limit(10).all()
        
        print(f"📊 Últimas 10 empresas sin owner_id:")
        for emp in empresas_sin_owner:
            print(f"  - {emp.razon_social} (ID: {emp.id}, NIT: {emp.nit})")
            print(f"    Creada: {emp.created_at}")
        
        # 6. Verificar si hay empresas que deberían estar asignadas a moyano
        print(f"\n🔍 POSIBLES EMPRESAS PERDIDAS:")
        print("-" * 60)
        
        # Buscar empresas que podrían ser de moyano por nombre o contexto
        posibles_empresas = db.query(Empresa).filter(
            Empresa.owner_id.is_(None),
            Empresa.razon_social.ilike('%moyano%')
        ).all()
        
        if posibles_empresas:
            print(f"⚠️  Empresas con 'moyano' en el nombre sin owner:")
            for emp in posibles_empresas:
                print(f"  - {emp.razon_social} (ID: {emp.id})")
        else:
            print("✅ No hay empresas con 'moyano' en el nombre sin owner")
        
        # 7. Recomendaciones específicas
        print(f"\n💡 RECOMENDACIONES PARA MOYANO:")
        print("-" * 60)
        
        if len(empresas_owner) == 0:
            print("❌ PROBLEMA: Moyano no es owner de ninguna empresa")
            print("   Solución: Verificar si hay empresas que debería poseer")
        
        if len(relaciones) == 0:
            print("❌ PROBLEMA: Moyano no tiene relaciones en usuario_empresas")
            print("   Solución: Crear relaciones para empresas que debería ver")
        
        if len(empresas_visibles) <= 1:
            print("⚠️  ADVERTENCIA: Moyano solo ve 1 empresa o menos")
            print("   Verificar si debería ver más empresas")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"❌ Error durante el diagnóstico: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    main()