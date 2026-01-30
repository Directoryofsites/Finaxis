#!/usr/bin/env python3
"""
Script de diagnóstico para investigar el problema de visualización de empresas
para usuarios con rol contador.
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
        print("DIAGNÓSTICO: Problema de visualización de empresas para contadores")
        print("=" * 80)
        
        # 1. Buscar usuarios con rol contador
        print("\n1. USUARIOS CON ROL CONTADOR:")
        print("-" * 50)
        
        contadores = db.query(Usuario).join(Usuario.roles).filter(
            Rol.nombre == 'contador'
        ).options(joinedload(Usuario.roles)).all()
        
        if not contadores:
            print("❌ No se encontraron usuarios con rol 'contador'")
            return
        
        print(f"✅ Encontrados {len(contadores)} usuarios con rol contador:")
        for contador in contadores:
            print(f"  - ID: {contador.id}, Email: {contador.email}, Empresa ID: {contador.empresa_id}")
        
        # 2. Buscar empresas donde estos contadores son owner
        print("\n2. EMPRESAS DONDE CONTADORES SON OWNER:")
        print("-" * 50)
        
        contador_ids = [c.id for c in contadores]
        empresas_owned = db.query(Empresa).filter(
            Empresa.owner_id.in_(contador_ids)
        ).all()
        
        print(f"✅ Encontradas {len(empresas_owned)} empresas con contadores como owner:")
        for empresa in empresas_owned:
            owner = next((c for c in contadores if c.id == empresa.owner_id), None)
            owner_email = owner.email if owner else "DESCONOCIDO"
            print(f"  - ID: {empresa.id}, Razón Social: {empresa.razon_social}")
            print(f"    Owner ID: {empresa.owner_id} ({owner_email})")
            print(f"    NIT: {empresa.nit}")
        
        # 3. Verificar tabla usuario_empresas para contadores
        print("\n3. RELACIONES EN TABLA usuario_empresas:")
        print("-" * 50)
        
        relaciones = db.execute(
            usuario_empresas.select().where(
                usuario_empresas.c.usuario_id.in_(contador_ids)
            )
        ).fetchall()
        
        print(f"✅ Encontradas {len(relaciones)} relaciones en usuario_empresas:")
        for rel in relaciones:
            usuario = next((c for c in contadores if c.id == rel.usuario_id), None)
            empresa = db.query(Empresa).filter(Empresa.id == rel.empresa_id).first()
            
            usuario_email = usuario.email if usuario else "DESCONOCIDO"
            empresa_nombre = empresa.razon_social if empresa else "DESCONOCIDA"
            
            print(f"  - Usuario: {rel.usuario_id} ({usuario_email})")
            print(f"    Empresa: {rel.empresa_id} ({empresa_nombre})")
            print(f"    Is Owner: {rel.is_owner}")
        
        # 4. Probar la función get_empresas_para_usuario para cada contador
        print("\n4. PRUEBA DE get_empresas_para_usuario:")
        print("-" * 50)
        
        for contador in contadores:
            print(f"\n🔍 Probando para usuario: {contador.email} (ID: {contador.id})")
            
            try:
                empresas_visibles = get_empresas_para_usuario(db, contador)
                print(f"  ✅ Empresas visibles: {len(empresas_visibles)}")
                
                for empresa in empresas_visibles:
                    print(f"    - {empresa.razon_social} (ID: {empresa.id})")
                    
                    # Verificar por qué esta empresa es visible
                    razones = []
                    if empresa.owner_id == contador.id:
                        razones.append("ES OWNER")
                    if contador.empresa_id == empresa.id:
                        razones.append("ES SU EMPRESA PRINCIPAL")
                    if empresa.padre_id == contador.empresa_id:
                        razones.append("ES EMPRESA HIJA")
                    
                    # Verificar si está en usuario_empresas
                    rel_exists = db.execute(
                        usuario_empresas.select().where(
                            usuario_empresas.c.usuario_id == contador.id,
                            usuario_empresas.c.empresa_id == empresa.id
                        )
                    ).fetchone()
                    
                    if rel_exists:
                        razones.append("RELACIÓN M2M")
                    
                    print(f"      Razones: {', '.join(razones) if razones else 'DESCONOCIDA'}")
                    
            except Exception as e:
                print(f"  ❌ Error al obtener empresas: {str(e)}")
        
        # 5. Buscar empresas huérfanas (sin owner o con owner inexistente)
        print("\n5. EMPRESAS HUÉRFANAS O PROBLEMÁTICAS:")
        print("-" * 50)
        
        empresas_sin_owner = db.query(Empresa).filter(
            Empresa.owner_id.is_(None)
        ).all()
        
        print(f"📊 Empresas sin owner_id: {len(empresas_sin_owner)}")
        for empresa in empresas_sin_owner:
            print(f"  - {empresa.razon_social} (ID: {empresa.id}, NIT: {empresa.nit})")
        
        # Empresas con owner_id que no existe
        empresas_owner_invalido = db.query(Empresa).filter(
            Empresa.owner_id.isnot(None),
            ~Empresa.owner_id.in_(
                db.query(Usuario.id).subquery()
            )
        ).all()
        
        print(f"📊 Empresas con owner_id inválido: {len(empresas_owner_invalido)}")
        for empresa in empresas_owner_invalido:
            print(f"  - {empresa.razon_social} (ID: {empresa.id}, Owner ID inválido: {empresa.owner_id})")
        
        # 6. Resumen y recomendaciones
        print("\n6. RESUMEN Y DIAGNÓSTICO:")
        print("-" * 50)
        
        total_empresas = db.query(Empresa).count()
        print(f"📊 Total de empresas en sistema: {total_empresas}")
        print(f"📊 Empresas con contadores como owner: {len(empresas_owned)}")
        print(f"📊 Relaciones usuario_empresas para contadores: {len(relaciones)}")
        
        # Identificar problemas
        problemas = []
        
        if len(empresas_owned) == 0:
            problemas.append("❌ CRÍTICO: No hay empresas con contadores como owner")
        
        if len(relaciones) < len(empresas_owned):
            problemas.append("⚠️  ADVERTENCIA: Faltan relaciones en usuario_empresas")
        
        for contador in contadores:
            empresas_visibles = get_empresas_para_usuario(db, contador)
            empresas_deberia_ver = db.query(Empresa).filter(
                Empresa.owner_id == contador.id
            ).count()
            
            if len(empresas_visibles) < empresas_deberia_ver:
                problemas.append(f"❌ PROBLEMA: {contador.email} ve {len(empresas_visibles)} empresas pero debería ver {empresas_deberia_ver}")
        
        if problemas:
            print("\n🚨 PROBLEMAS IDENTIFICADOS:")
            for problema in problemas:
                print(f"  {problema}")
        else:
            print("\n✅ No se identificaron problemas obvios")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"❌ Error durante el diagnóstico: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    main()