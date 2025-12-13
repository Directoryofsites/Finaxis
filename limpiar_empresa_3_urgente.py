#!/usr/bin/env python3
"""
Script URGENTE para limpiar documentos de empresa 3
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

def limpiar_empresa_3_completo():
    """
    Limpia COMPLETAMENTE la empresa 3
    """
    db = next(get_db())
    empresa_id = 3
    
    try:
        print(f"🧹 LIMPIEZA URGENTE - Empresa {empresa_id}")
        print("=" * 50)
        
        # 1. Contar documentos
        docs = db.query(Documento).filter(
            Documento.empresa_id == empresa_id
        ).all()
        
        print(f"📄 Documentos a eliminar: {len(docs)}")
        
        # 2. Eliminar movimientos contables
        total_movimientos = 0
        for doc in docs:
            movs = db.query(MovimientoContable).filter(
                MovimientoContable.documento_id == doc.id
            ).delete(synchronize_session=False)
            total_movimientos += movs
        
        print(f"🔄 Movimientos eliminados: {total_movimientos}")
        
        # 3. Eliminar documentos
        docs_eliminados = db.query(Documento).filter(
            Documento.empresa_id == empresa_id
        ).delete(synchronize_session=False)
        
        print(f"📄 Documentos eliminados: {docs_eliminados}")
        
        # 4. Eliminar novedades de activos
        novedades = db.query(ActivoNovedad).filter(
            ActivoNovedad.empresa_id == empresa_id
        ).delete(synchronize_session=False)
        
        print(f"📝 Novedades eliminadas: {novedades}")
        
        # 5. Resetear depreciación acumulada de activos
        activos_reseteados = db.query(ActivoFijo).filter(
            ActivoFijo.empresa_id == empresa_id
        ).update({
            ActivoFijo.depreciacion_acumulada_niif: 0,
            ActivoFijo.depreciacion_acumulada_fiscal: 0
        }, synchronize_session=False)
        
        print(f"🏢 Activos reseteados: {activos_reseteados}")
        
        # 6. Commit
        db.commit()
        
        print(f"\n✅ ¡LIMPIEZA COMPLETADA!")
        print(f"   - {docs_eliminados} documentos eliminados")
        print(f"   - {total_movimientos} movimientos eliminados")
        print(f"   - {novedades} novedades eliminadas")
        print(f"   - {activos_reseteados} activos reseteados")
        print(f"\n🎯 La empresa {empresa_id} está completamente limpia.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ ERROR: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    try:
        print("🚨 EJECUTANDO LIMPIEZA URGENTE...")
        limpiar_empresa_3_completo()
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()