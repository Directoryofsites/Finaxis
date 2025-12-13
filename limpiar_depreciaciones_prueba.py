#!/usr/bin/env python3
"""
Script para limpiar depreciaciones de prueba en Kiro
Permite hacer nuevos ensayos de depreciación eliminando datos previos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.activo_fijo import ActivoFijo
from app.models.activo_novedad import ActivoNovedad, TipoNovedadActivo
from app.models.documento import Documento
from app.models.movimiento_contable import MovimientoContable

def limpiar_depreciaciones_empresa(empresa_id: int = 1):
    """
    Limpia todas las depreciaciones de una empresa para permitir nuevas pruebas
    """
    db = next(get_db())
    
    try:
        print(f"🧹 Iniciando limpieza de depreciaciones para empresa {empresa_id}...")
        
        # 1. Contar datos antes de limpiar
        docs_antes = db.query(Documento).filter(
            Documento.empresa_id == empresa_id,
            Documento.observaciones.ilike('%depreciación%')
        ).count()
        
        novedades_antes = db.query(ActivoNovedad).filter(
            ActivoNovedad.empresa_id == empresa_id,
            ActivoNovedad.tipo == TipoNovedadActivo.DEPRECIACION
        ).count()
        
        activos_con_dep = db.query(ActivoFijo).filter(
            ActivoFijo.empresa_id == empresa_id,
            ActivoFijo.depreciacion_acumulada_niif > 0
        ).count()
        
        print(f"📊 Estado actual:")
        print(f"   - Documentos de depreciación: {docs_antes}")
        print(f"   - Novedades de depreciación: {novedades_antes}")
        print(f"   - Activos con depreciación acumulada: {activos_con_dep}")
        
        if docs_antes == 0 and novedades_antes == 0 and activos_con_dep == 0:
            print("✅ No hay depreciaciones que limpiar. Base de datos ya está limpia.")
            return
        
        # 2. Confirmar limpieza
        respuesta = input("\n⚠️  ¿Continuar con la limpieza? (s/N): ").lower().strip()
        if respuesta != 's':
            print("❌ Limpieza cancelada por el usuario.")
            return
        
        # 3. Buscar documentos de depreciación
        documentos_depreciacion = db.query(Documento).filter(
            Documento.empresa_id == empresa_id,
            Documento.observaciones.ilike('%depreciación%')
        ).all()
        
        documentos_eliminados = []
        
        # 4. Eliminar documentos y movimientos
        for doc in documentos_depreciacion:
            # Eliminar movimientos contables
            movimientos_eliminados = db.query(MovimientoContable).filter(
                MovimientoContable.documento_id == doc.id
            ).delete(synchronize_session=False)
            
            doc_nombre = f"{doc.tipo_documento.codigo if doc.tipo_documento else 'N/A'}-{doc.numero}"
            documentos_eliminados.append(doc_nombre)
            
            print(f"   🗑️  Eliminando documento: {doc_nombre} ({movimientos_eliminados} movimientos)")
            
            # Eliminar documento
            db.delete(doc)
        
        # 5. Eliminar novedades de depreciación
        novedades_eliminadas = db.query(ActivoNovedad).filter(
            ActivoNovedad.empresa_id == empresa_id,
            ActivoNovedad.tipo == TipoNovedadActivo.DEPRECIACION
        ).delete(synchronize_session=False)
        
        print(f"   🗑️  Eliminadas {novedades_eliminadas} novedades de depreciación")
        
        # 6. Resetear depreciación acumulada
        activos_reseteados = db.query(ActivoFijo).filter(
            ActivoFijo.empresa_id == empresa_id
        ).update({
            ActivoFijo.depreciacion_acumulada_niif: 0,
            ActivoFijo.depreciacion_acumulada_fiscal: 0
        }, synchronize_session=False)
        
        print(f"   🔄 Reseteados {activos_reseteados} activos (depreciación acumulada = 0)")
        
        # 7. Confirmar cambios
        db.commit()
        
        print(f"\n✅ ¡Limpieza completada exitosamente!")
        print(f"   - {len(documentos_eliminados)} documentos eliminados")
        print(f"   - {novedades_eliminadas} novedades eliminadas") 
        print(f"   - {activos_reseteados} activos reseteados")
        print(f"\n🎯 Ya puedes ejecutar nuevas depreciaciones de prueba.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error durante la limpieza: {str(e)}")
        raise
    finally:
        db.close()

def mostrar_estado_depreciaciones(empresa_id: int = 1):
    """
    Muestra el estado actual de las depreciaciones
    """
    db = next(get_db())
    
    try:
        print(f"📊 Estado de depreciaciones - Empresa {empresa_id}")
        print("=" * 50)
        
        # Documentos de depreciación
        docs = db.query(Documento).filter(
            Documento.empresa_id == empresa_id,
            Documento.observaciones.ilike('%depreciación%')
        ).all()
        
        print(f"📄 Documentos de depreciación: {len(docs)}")
        for doc in docs:
            tipo_nombre = doc.tipo_documento.codigo if doc.tipo_documento else 'N/A'
            print(f"   - {tipo_nombre}-{doc.numero} | {doc.fecha} | {doc.observaciones}")
        
        # Novedades de depreciación
        novedades = db.query(ActivoNovedad).filter(
            ActivoNovedad.empresa_id == empresa_id,
            ActivoNovedad.tipo == TipoNovedadActivo.DEPRECIACION
        ).count()
        
        print(f"\n📝 Novedades de depreciación: {novedades}")
        
        # Activos con depreciación
        activos_con_dep = db.query(ActivoFijo).filter(
            ActivoFijo.empresa_id == empresa_id,
            ActivoFijo.depreciacion_acumulada_niif > 0
        ).all()
        
        print(f"\n🏢 Activos con depreciación acumulada: {len(activos_con_dep)}")
        for activo in activos_con_dep:
            print(f"   - {activo.codigo}: ${activo.depreciacion_acumulada_niif:,.0f}")
        
    except Exception as e:
        print(f"❌ Error consultando estado: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 Herramienta de limpieza de depreciaciones - Kiro")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "estado":
            mostrar_estado_depreciaciones()
        elif sys.argv[1] == "limpiar":
            limpiar_depreciaciones_empresa()
        else:
            print("❌ Comando no reconocido. Usa: 'estado' o 'limpiar'")
    else:
        print("Comandos disponibles:")
        print("  python limpiar_depreciaciones_prueba.py estado   - Ver estado actual")
        print("  python limpiar_depreciaciones_prueba.py limpiar  - Limpiar depreciaciones")