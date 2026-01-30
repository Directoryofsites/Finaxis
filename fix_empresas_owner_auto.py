#!/usr/bin/env python3
"""
Script automático para corregir el problema de owner_id en empresas creadas por contadores
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from app.core.database import engine
from app.models.usuario import Usuario, usuario_empresas
from app.models.empresa import Empresa
from app.models.permiso import Rol

def main():
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("CORRECCIÓN AUTOMÁTICA: Asignación de owner_id para empresas de contadores")
        print("=" * 80)
        
        correcciones_realizadas = 0
        
        # 1. Caso específico: moyano@moyano.com
        print("\n1. CORRIGIENDO CASO ESPECÍFICO: moyano@moyano.com")
        print("-" * 60)
        
        moyano = db.query(Usuario).filter(
            Usuario.email == 'moyano@moyano.com'
        ).first()
        
        if moyano and moyano.empresa_id:
            empresa_moyano = db.query(Empresa).filter(
                Empresa.id == moyano.empresa_id
            ).first()
            
            if empresa_moyano and empresa_moyano.owner_id is None:
                print(f"🔧 Corrigiendo:")
                print(f"  Usuario: {moyano.email} (ID: {moyano.id})")
                print(f"  Empresa: {empresa_moyano.razon_social} (ID: {empresa_moyano.id})")
                
                # 1. Asignar owner_id
                empresa_moyano.owner_id = moyano.id
                db.add(empresa_moyano)
                print(f"  ✅ Asignado owner_id = {moyano.id}")
                
                # 2. Crear relación en usuario_empresas si no existe
                relacion_existente = db.execute(
                    usuario_empresas.select().where(
                        usuario_empresas.c.usuario_id == moyano.id,
                        usuario_empresas.c.empresa_id == empresa_moyano.id
                    )
                ).fetchone()
                
                if not relacion_existente:
                    stmt = usuario_empresas.insert().values(
                        usuario_id=moyano.id,
                        empresa_id=empresa_moyano.id,
                        is_owner=True
                    )
                    db.execute(stmt)
                    print(f"  ✅ Creada relación en usuario_empresas")
                else:
                    print(f"  ℹ️  Relación ya existía")
                
                correcciones_realizadas += 1
            else:
                print("✅ Caso de moyano ya está correcto")
        
        # 2. Buscar y corregir otros casos similares
        print(f"\n2. BUSCANDO Y CORRIGIENDO OTROS CASOS:")
        print("-" * 60)
        
        # Usuarios contadores que tienen empresa_id pero la empresa no tiene owner_id
        contadores = db.query(Usuario).join(Usuario.roles).filter(
            Rol.nombre == 'contador',
            Usuario.empresa_id.isnot(None)
        ).all()
        
        for contador in contadores:
            if contador.email == 'moyano@moyano.com':
                continue  # Ya procesamos a moyano
                
            empresa = db.query(Empresa).filter(
                Empresa.id == contador.empresa_id
            ).first()
            
            if empresa and empresa.owner_id is None:
                print(f"🔧 Corrigiendo:")
                print(f"  Usuario: {contador.email} (ID: {contador.id})")
                print(f"  Empresa: {empresa.razon_social} (ID: {empresa.id})")
                
                # Asignar owner_id
                empresa.owner_id = contador.id
                db.add(empresa)
                print(f"  ✅ Asignado owner_id = {contador.id}")
                
                # Crear relación en usuario_empresas
                relacion_existente = db.execute(
                    usuario_empresas.select().where(
                        usuario_empresas.c.usuario_id == contador.id,
                        usuario_empresas.c.empresa_id == empresa.id
                    )
                ).fetchone()
                
                if not relacion_existente:
                    stmt = usuario_empresas.insert().values(
                        usuario_id=contador.id,
                        empresa_id=empresa.id,
                        is_owner=True
                    )
                    db.execute(stmt)
                    print(f"  ✅ Creada relación en usuario_empresas")
                
                correcciones_realizadas += 1
        
        # 3. Commit todos los cambios
        if correcciones_realizadas > 0:
            db.commit()
            print(f"\n✅ CORRECCIONES COMPLETADAS: {correcciones_realizadas} casos corregidos")
        else:
            print(f"\n✅ NO SE NECESITARON CORRECCIONES")
        
        # 4. Verificar resultado final para moyano
        print(f"\n3. VERIFICACIÓN FINAL PARA MOYANO:")
        print("-" * 60)
        
        if moyano:
            from app.services.empresa import get_empresas_para_usuario
            
            # Refrescar objetos
            db.refresh(moyano)
            
            print(f"🧪 Probando get_empresas_para_usuario para {moyano.email}:")
            empresas_visibles = get_empresas_para_usuario(db, moyano)
            print(f"  ✅ Empresas visibles: {len(empresas_visibles)}")
            
            for emp in empresas_visibles:
                print(f"    - {emp.razon_social} (ID: {emp.id})")
                
                # Verificar razones de visibilidad
                razones = []
                if emp.owner_id == moyano.id:
                    razones.append("ES OWNER")
                if moyano.empresa_id == emp.id:
                    razones.append("ES SU EMPRESA PRINCIPAL")
                
                rel_exists = db.execute(
                    usuario_empresas.select().where(
                        usuario_empresas.c.usuario_id == moyano.id,
                        usuario_empresas.c.empresa_id == emp.id
                    )
                ).fetchone()
                
                if rel_exists:
                    razones.append("RELACIÓN M2M")
                
                print(f"      Razones: {', '.join(razones)}")
        
        print(f"\n" + "=" * 80)
        print("CORRECCIÓN AUTOMÁTICA COMPLETADA")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error durante la corrección: {str(e)}")
        db.rollback()
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    main()