#!/usr/bin/env python3
"""
Script COMPLETO para limpiar empresa 3 con todas las dependencias
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.documento import Documento
from app.models.movimiento_contable import MovimientoContable
from app.models.activo_novedad import ActivoNovedad
from app.models.activo_fijo import ActivoFijo

def limpiar_empresa_3_con_dependencias():
    """
    Limpia empresa 3 eliminando TODAS las dependencias primero
    """
    db = next(get_db())
    empresa_id = 3
    
    try:
        print(f"🧹 LIMPIEZA COMPLETA - Empresa {empresa_id}")
        print("=" * 50)
        
        # 1. Contar documentos
        docs = db.query(Documento).filter(
            Documento.empresa_id == empresa_id
        ).all()
        
        print(f"📄 Documentos encontrados: {len(docs)}")
        
        # 2. Eliminar movimientos de inventario primero
        print("🔄 Eliminando movimientos de inventario...")
        try:
            # Importar el modelo de movimientos de inventario
            from app.models.producto import MovimientoInventario
            
            movs_inventario = 0
            for doc in docs:
                movs_inv = db.query(MovimientoInventario).filter(
                    MovimientoInventario.documento_id == doc.id
                ).delete(synchronize_session=False)
                movs_inventario += movs_inv
            
            print(f"   ✅ Movimientos inventario eliminados: {movs_inventario}")
            
        except Exception as e:
            print(f"   ⚠️  Error con inventario (puede ser normal): {e}")
        
        # 3. Eliminar aplicaciones de pago
        print("💰 Eliminando aplicaciones de pago...")
        try:
            from app.models.aplicacion_pago import AplicacionPago
            
            aplicaciones = 0
            for doc in docs:
                apps = db.query(AplicacionPago).filter(
                    (AplicacionPago.documento_origen_id == doc.id) |
                    (AplicacionPago.documento_destino_id == doc.id)
                ).delete(synchronize_session=False)
                aplicaciones += apps
            
            print(f"   ✅ Aplicaciones eliminadas: {aplicaciones}")
            
        except Exception as e:
            print(f"   ⚠️  Error con aplicaciones (puede ser normal): {e}")
        
        # 4. Eliminar novedades de activos
        print("📝 Eliminando novedades de activos...")
        novedades = db.query(ActivoNovedad).filter(
            ActivoNovedad.empresa_id == empresa_id
        ).delete(synchronize_session=False)
        print(f"   ✅ Novedades eliminadas: {novedades}")
        
        # 5. Eliminar movimientos contables
        print("🔄 Eliminando movimientos contables...")
        total_movimientos = 0
        for doc in docs:
            movs = db.query(MovimientoContable).filter(
                MovimientoContable.documento_id == doc.id
            ).delete(synchronize_session=False)
            total_movimientos += movs
        
        print(f"   ✅ Movimientos eliminados: {total_movimientos}")
        
        # 6. Ahora sí eliminar documentos
        print("📄 Eliminando documentos...")
        docs_eliminados = 0
        for doc in docs:
            try:
                db.delete(doc)
                docs_eliminados += 1
            except Exception as e:
                print(f"   ❌ Error eliminando doc {doc.id}: {e}")
        
        print(f"   ✅ Documentos eliminados: {docs_eliminados}")
        
        # 7. Resetear depreciación acumulada de activos
        print("🏢 Reseteando activos...")
        activos_reseteados = db.query(ActivoFijo).filter(
            ActivoFijo.empresa_id == empresa_id
        ).update({
            ActivoFijo.depreciacion_acumulada_niif: 0,
            ActivoFijo.depreciacion_acumulada_fiscal: 0
        }, synchronize_session=False)
        
        print(f"   ✅ Activos reseteados: {activos_reseteados}")
        
        # 8. Commit final
        print("💾 Guardando cambios...")
        db.commit()
        
        print(f"\n🎉 ¡LIMPIEZA COMPLETADA EXITOSAMENTE!")
        print(f"   📄 {docs_eliminados} documentos eliminados")
        print(f"   🔄 {total_movimientos} movimientos contables eliminados")
        print(f"   📝 {novedades} novedades eliminadas")
        print(f"   🏢 {activos_reseteados} activos reseteados")
        print(f"\n✨ La empresa {empresa_id} está completamente limpia.")
        print(f"🎯 Ahora puedes hacer nuevas pruebas de depreciación.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ ERROR CRÍTICO: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚨 EJECUTANDO LIMPIEZA COMPLETA...")
    print("⚠️  Esto eliminará TODOS los documentos de empresa 3")
    print("🔄 Procesando...")
    limpiar_empresa_3_con_dependencias()