#!/usr/bin/env python3
"""
Script para corregir el problema de owner_id en empresas creadas por contadores
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
        print("CORRECCIÓN: Asignación de owner_id para empresas de contadores")
        print("=" * 80)
        
        # 1. Identificar casos problemáticos
        print("\n1. IDENTIFICANDO PROBLEMAS:")
        print("-" * 50)
        
        # Caso específico: moyano@moyano.com y empresa Moyano
        moyano = db.query(Usuario).filter(
            Usuario.email == 'moyano@moyano.com'
        ).first()
        
        if moyano:
            empresa_moyano = db.query(Empresa).filter(
                Empresa.id == moyano.empresa_id
            ).first()
            
            if empresa_moyano and empresa_moyano.owner_id is None:
                print(f"🔍 PROBLEMA IDENTIFICADO:")
                print(f"  Usuario: {moyano.email} (ID: {moyano.id})")
                print(f"  Empresa: {empresa_moyano.razon_social} (ID: {empresa_moyano.id})")
                print(f"  Problema: owner_id es None, debería ser {moyano.id}")
                
                # Confirmar corrección
                respuesta = input("\n¿Corregir este problema? (s/n): ").lower().strip()
                
                if respuesta == 's':
                    print("\n🔧 APLICANDO CORRECCIÓN:")
                    
                    # 1. Asignar owner_id
                    empresa_moyano.owner_id = moyano.id
                    db.add(empresa_moyano)
                    print(f"  ✅ Asignado owner_id = {moyano.id} a empresa {empresa_moyano.razon_social}")
                    
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
                        print(f"  ✅ Creada relación en usuario_empresas (is_owner=True)")
                    else:
                        print(f"  ℹ️  Relación en usuario_empresas ya existe")
                    
                    # Commit cambios
                    db.commit()
                    print(f"  ✅ Cambios guardados exitosamente")
                    
                    # Verificar corrección
                    print(f"\n🧪 VERIFICANDO CORRECCIÓN:")
                    from app.services.empresa import get_empresas_para_usuario
                    
                    # Refrescar objetos
                    db.refresh(moyano)
                    db.refresh(empresa_moyano)
                    
                    empresas_visibles = get_empresas_para_usuario(db, moyano)
                    print(f"  ✅ Empresas visibles para {moyano.email}: {len(empresas_visibles)}")
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
                    
                else:
                    print("❌ Corrección cancelada por el usuario")
        
        # 2. Buscar otros casos similares
        print(f"\n2. BUSCANDO OTROS CASOS SIMILARES:")
        print("-" * 50)
        
        # Usuarios contadores que tienen empresa_id pero la empresa no tiene owner_id
        contadores = db.query(Usuario).join(Usuario.roles).filter(
            Rol.nombre == 'contador',
            Usuario.empresa_id.isnot(None)
        ).all()
        
        casos_adicionales = []
        for contador in contadores:
            if contador.id == (moyano.id if moyano else -1):
                continue  # Ya procesamos a moyano
                
            empresa = db.query(Empresa).filter(
                Empresa.id == contador.empresa_id
            ).first()
            
            if empresa and empresa.owner_id is None:
                casos_adicionales.append((contador, empresa))
        
        if casos_adicionales:
            print(f"🔍 Encontrados {len(casos_adicionales)} casos adicionales:")
            for contador, empresa in casos_adicionales:
                print(f"  - Usuario: {contador.email} (ID: {contador.id})")
                print(f"    Empresa: {empresa.razon_social} (ID: {empresa.id})")
            
            respuesta = input(f"\n¿Corregir estos {len(casos_adicionales)} casos? (s/n): ").lower().strip()
            
            if respuesta == 's':
                for contador, empresa in casos_adicionales:
                    print(f"\n🔧 Corrigiendo: {contador.email} -> {empresa.razon_social}")
                    
                    # Asignar owner_id
                    empresa.owner_id = contador.id
                    db.add(empresa)
                    
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
                        print(f"  ✅ Corregido: {empresa.razon_social}")
                
                db.commit()
                print(f"  ✅ Todos los casos corregidos")
        else:
            print("✅ No se encontraron casos adicionales")
        
        print(f"\n" + "=" * 80)
        print("CORRECCIÓN COMPLETADA")
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