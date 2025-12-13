#!/usr/bin/env python3
"""
Script para verificar documentos en TODAS las empresas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.documento import Documento
from app.models.empresa import Empresa
from app.models.movimiento_contable import MovimientoContable

def verificar_todas_empresas():
    """
    Verifica documentos en todas las empresas
    """
    db = next(get_db())
    
    try:
        print("🔍 Verificando TODAS las empresas")
        print("=" * 60)
        
        # Obtener todas las empresas
        empresas = db.query(Empresa).all()
        print(f"🏢 Total empresas: {len(empresas)}")
        
        for empresa in empresas:
            print(f"\n📊 Empresa {empresa.id}: {empresa.razon_social}")
            print("-" * 40)
            
            # Documentos de esta empresa
            docs = db.query(Documento).filter(
                Documento.empresa_id == empresa.id
            ).order_by(Documento.fecha.desc()).all()
            
            print(f"   📄 Total documentos: {len(docs)}")
            
            if docs:
                print("   📋 Últimos documentos:")
                for doc in docs[:10]:  # Mostrar solo los primeros 10
                    tipo_nombre = doc.tipo_documento.codigo if doc.tipo_documento else 'N/A'
                    observaciones = (doc.observaciones or 'Sin obs')[:30]
                    print(f"      - {tipo_nombre}-{doc.numero} | {doc.fecha} | {observaciones}...")
                
                if len(docs) > 10:
                    print(f"      ... y {len(docs) - 10} más")
        
        # Buscar documentos con palabras clave
        print(f"\n🔍 Buscando documentos con palabras clave...")
        
        palabras_clave = ['depreciación', 'automática', 'activo', 'ACTIVO']
        
        for palabra in palabras_clave:
            docs_palabra = db.query(Documento).filter(
                Documento.observaciones.ilike(f'%{palabra}%')
            ).all()
            
            if docs_palabra:
                print(f"   🔑 '{palabra}': {len(docs_palabra)} documentos")
                for doc in docs_palabra[:5]:
                    empresa_id = doc.empresa_id
                    tipo_nombre = doc.tipo_documento.codigo if doc.tipo_documento else 'N/A'
                    print(f"      - Empresa {empresa_id}: {tipo_nombre}-{doc.numero} | {doc.observaciones}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        db.close()

def eliminar_todos_documentos_empresa(empresa_id: int):
    """
    Elimina TODOS los documentos de una empresa específica
    """
    db = next(get_db())
    
    try:
        print(f"🗑️  ELIMINANDO TODOS los documentos de empresa {empresa_id}")
        
        # Obtener todos los documentos
        docs = db.query(Documento).filter(
            Documento.empresa_id == empresa_id
        ).all()
        
        print(f"📄 Documentos a eliminar: {len(docs)}")
        
        if not docs:
            print("✅ No hay documentos que eliminar.")
            return
        
        respuesta = input(f"\n⚠️  ¿ELIMINAR TODOS los {len(docs)} documentos de empresa {empresa_id}? (escriba 'SI ELIMINAR' para confirmar): ")
        if respuesta != 'SI ELIMINAR':
            print("❌ Eliminación cancelada.")
            return
        
        eliminados = 0
        for doc in docs:
            try:
                # Eliminar movimientos primero
                movs_eliminados = db.query(MovimientoContable).filter(
                    MovimientoContable.documento_id == doc.id
                ).delete(synchronize_session=False)
                
                # Eliminar documento
                db.delete(doc)
                eliminados += 1
                
                if eliminados % 10 == 0:
                    print(f"   Eliminados {eliminados}/{len(docs)}...")
                
            except Exception as e:
                print(f"❌ Error eliminando documento {doc.id}: {e}")
        
        db.commit()
        print(f"✅ Eliminados {eliminados} documentos exitosamente.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error durante eliminación: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "verificar":
            verificar_todas_empresas()
        elif sys.argv[1] == "eliminar" and len(sys.argv) > 2:
            empresa_id = int(sys.argv[2])
            eliminar_todos_documentos_empresa(empresa_id)
        else:
            print("❌ Uso: python verificar_todas_empresas.py verificar")
            print("❌ Uso: python verificar_todas_empresas.py eliminar <empresa_id>")
    else:
        verificar_todas_empresas()