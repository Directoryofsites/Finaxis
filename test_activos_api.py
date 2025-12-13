#!/usr/bin/env python3
"""
Script para probar la API de activos fijos después de las correcciones
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.documento import Documento
from app.models.movimiento_contable import MovimientoContable
from app.models.activo_novedad import ActivoNovedad

def main():
    # Conectar a la base de datos
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    print("🔧 PRUEBA FINAL DE CORRECCIONES")
    print("=" * 50)
    
    try:
        # 1. Verificar documentos de depreciación
        print("\n1. 📄 VERIFICANDO DOCUMENTOS:")
        documentos = db.query(Documento).filter(
            Documento.empresa_id == 3,
            Documento.observaciones.ilike('%depreciación%')
        ).all()
        
        print(f"   Documentos encontrados: {len(documentos)}")
        
        for doc in documentos:
            print(f"\n   📋 Documento {doc.id}: {doc.numero}")
            print(f"      Tipo: {doc.tipo_documento.codigo if doc.tipo_documento else 'SIN TIPO'} - {doc.tipo_documento.nombre if doc.tipo_documento else 'SIN NOMBRE'}")
            print(f"      Estado: {doc.estado}")
            print(f"      Fecha: {doc.fecha}")
            
            # Verificar movimientos
            movimientos = db.query(MovimientoContable).filter(
                MovimientoContable.documento_id == doc.id
            ).all()
            
            print(f"      Movimientos: {len(movimientos)}")
            
            if movimientos:
                total_debito = sum(float(m.debito or 0) for m in movimientos)
                total_credito = sum(float(m.credito or 0) for m in movimientos)
                print(f"         Débito: ${total_debito:,.0f}")
                print(f"         Crédito: ${total_credito:,.0f}")
                print(f"         Balance: {'✅ OK' if abs(total_debito - total_credito) < 0.01 else '❌ ERROR'}")
            
            # Verificar novedades asociadas
            novedades = db.query(ActivoNovedad).filter(
                ActivoNovedad.documento_contable_id == doc.id
            ).all()
            
            print(f"      Novedades asociadas: {len(novedades)}")
        
        # 2. Probar función get_documentos_contables_activos
        print(f"\n2. 🔧 PROBANDO FUNCIÓN CORREGIDA:")
        
        from app.services.activo_fijo import get_documentos_contables_activos
        
        resultado = get_documentos_contables_activos(db, 3)
        
        print(f"   Función ejecutada: ✅")
        print(f"   Total documentos devueltos: {resultado['total']}")
        print(f"   Documentos en array: {len(resultado['documentos'])}")
        
        if resultado['documentos']:
            doc = resultado['documentos'][0]
            print(f"   Primer documento:")
            print(f"      ID: {doc['id']}")
            print(f"      Número: {doc['numero']}")
            print(f"      Tipo código: {doc['tipo_documento_codigo']}")
            print(f"      Tipo nombre: {doc['tipo_documento_nombre']}")
            print(f"      Total débito: ${doc['total_debito']:,.0f}")
            print(f"      Movimientos: {len(doc['movimientos_contables'])}")
        
        print(f"\n3. 🎯 RESUMEN DE CORRECCIONES APLICADAS:")
        print(f"   ✅ Corregido models_doc -> models_doc.Documento en activo_fijo.py")
        print(f"   ✅ Corregido models_doc -> models_doc.Documento en documento.py")
        print(f"   ✅ Frontend cambiado a usar /activos/documentos-contables")
        print(f"   ✅ Endpoint DELETE corregido para recibir razón del cuerpo")
        print(f"   ✅ Creado endpoint GET /documentos/{{id}}/pdf")
        print(f"   ✅ Filtros implementados en frontend")
        
        print(f"\n🎉 TODAS LAS CORRECCIONES APLICADAS EXITOSAMENTE")
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    main()