#!/usr/bin/env python3
"""
Script para verificar el estado de los documentos de activos fijos
y diagnosticar problemas con la generación de documentos contables
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.documento import Documento
from app.models.movimiento_contable import MovimientoContable
from app.models.tipo_documento import TipoDocumento
from app.models.activo_novedad import ActivoNovedad
from app.models.activo_fijo import ActivoFijo

def main():
    # Conectar a la base de datos
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    print("🔍 DIAGNÓSTICO DE DOCUMENTOS DE ACTIVOS FIJOS")
    print("=" * 60)
    
    try:
        # 1. Verificar documentos de depreciación
        print("\n1. 📄 DOCUMENTOS DE DEPRECIACIÓN:")
        documentos = db.query(Documento).filter(
            Documento.empresa_id == 3,  # Empresa "Verduras la 20"
            Documento.observaciones.ilike('%depreciación%')
        ).all()
        
        print(f"   Total documentos encontrados: {len(documentos)}")
        
        for doc in documentos:
            print(f"\n   📋 Documento ID: {doc.id}")
            print(f"      Número: {doc.numero}")
            print(f"      Fecha: {doc.fecha}")
            print(f"      Estado: {doc.estado}")
            print(f"      Observaciones: {doc.observaciones}")
            
            # Verificar tipo de documento
            if doc.tipo_documento:
                print(f"      Tipo: {doc.tipo_documento.codigo} - {doc.tipo_documento.nombre}")
            else:
                print(f"      ❌ PROBLEMA: Sin tipo de documento asignado")
            
            # Verificar movimientos contables
            movimientos = db.query(MovimientoContable).filter(
                MovimientoContable.documento_id == doc.id
            ).all()
            
            print(f"      Movimientos contables: {len(movimientos)}")
            
            if not movimientos:
                print(f"      ❌ PROBLEMA: No tiene movimientos contables")
            else:
                total_debito = sum(float(m.debito or 0) for m in movimientos)
                total_credito = sum(float(m.credito or 0) for m in movimientos)
                print(f"         Total débito: ${total_debito:,.0f}")
                print(f"         Total crédito: ${total_credito:,.0f}")
                print(f"         Balance: {'✅ OK' if abs(total_debito - total_credito) < 0.01 else '❌ DESBALANCEADO'}")
                
                # Mostrar detalle de movimientos
                for mov in movimientos:
                    cuenta_info = f"{mov.cuenta.codigo} - {mov.cuenta.nombre}" if mov.cuenta else "Sin cuenta"
                    print(f"         - {cuenta_info}: D${mov.debito or 0:,.0f} C${mov.credito or 0:,.0f}")
        
        # 2. Verificar novedades de depreciación
        print(f"\n2. 📝 NOVEDADES DE DEPRECIACIÓN:")
        novedades = db.query(ActivoNovedad).filter(
            ActivoNovedad.empresa_id == 3,
            ActivoNovedad.tipo == 'DEPRECIACION'
        ).all()
        
        print(f"   Total novedades: {len(novedades)}")
        
        for novedad in novedades:
            print(f"\n   📌 Novedad ID: {novedad.id}")
            print(f"      Activo: {novedad.activo.codigo} - {novedad.activo.nombre}")
            print(f"      Fecha: {novedad.fecha}")
            print(f"      Valor: ${novedad.valor:,.0f}")
            print(f"      Documento asociado: {novedad.documento_contable_id}")
            
            if novedad.documento_contable_id:
                doc_asociado = db.query(Documento).filter(Documento.id == novedad.documento_contable_id).first()
                if doc_asociado:
                    print(f"         ✅ Documento existe: {doc_asociado.numero}")
                else:
                    print(f"         ❌ PROBLEMA: Documento no existe")
            else:
                print(f"         ❌ PROBLEMA: Sin documento asociado")
        
        # 3. Verificar tipos de documento disponibles
        print(f"\n3. 📋 TIPOS DE DOCUMENTO DISPONIBLES:")
        tipos = db.query(TipoDocumento).filter(TipoDocumento.empresa_id == 3).all()
        
        for tipo in tipos:
            print(f"   - ID: {tipo.id} | {tipo.codigo} - {tipo.nombre} | Consecutivo: {tipo.consecutivo_actual}")
        
        # 4. Verificar activos fijos
        print(f"\n4. 🏢 ACTIVOS FIJOS:")
        activos = db.query(ActivoFijo).filter(ActivoFijo.empresa_id == 3).all()
        
        print(f"   Total activos: {len(activos)}")
        
        for activo in activos:
            print(f"\n   🏗️ Activo: {activo.codigo} - {activo.nombre}")
            print(f"      Costo: ${activo.costo_adquisicion:,.0f}")
            print(f"      Dep. Acumulada: ${activo.depreciacion_acumulada_niif:,.0f}")
            print(f"      Estado: {activo.estado}")
            
            if activo.categoria:
                print(f"      Categoría: {activo.categoria.nombre}")
                print(f"      Método depreciación: {activo.categoria.metodo_depreciacion}")
                
                # Verificar configuración contable
                config_ok = (
                    activo.categoria.cuenta_gasto_depreciacion_id and 
                    activo.categoria.cuenta_depreciacion_acumulada_id
                )
                print(f"      Config contable: {'✅ OK' if config_ok else '❌ INCOMPLETA'}")
                
                if not config_ok:
                    print(f"         Cuenta gasto: {activo.categoria.cuenta_gasto_depreciacion_id}")
                    print(f"         Cuenta acumulada: {activo.categoria.cuenta_depreciacion_acumulada_id}")
            else:
                print(f"      ❌ PROBLEMA: Sin categoría asignada")
        
        print(f"\n" + "=" * 60)
        print("🎯 RESUMEN DE PROBLEMAS DETECTADOS:")
        
        # Contar problemas
        docs_sin_tipo = sum(1 for doc in documentos if not doc.tipo_documento)
        docs_sin_movimientos = sum(1 for doc in documentos if not db.query(MovimientoContable).filter(MovimientoContable.documento_id == doc.id).count())
        novedades_sin_doc = sum(1 for nov in novedades if not nov.documento_contable_id)
        activos_sin_categoria = sum(1 for act in activos if not act.categoria)
        
        if docs_sin_tipo:
            print(f"❌ {docs_sin_tipo} documentos sin tipo asignado")
        if docs_sin_movimientos:
            print(f"❌ {docs_sin_movimientos} documentos sin movimientos contables")
        if novedades_sin_doc:
            print(f"❌ {novedades_sin_doc} novedades sin documento asociado")
        if activos_sin_categoria:
            print(f"❌ {activos_sin_categoria} activos sin categoría")
        
        if not any([docs_sin_tipo, docs_sin_movimientos, novedades_sin_doc, activos_sin_categoria]):
            print("✅ No se detectaron problemas críticos")
        
    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    main()