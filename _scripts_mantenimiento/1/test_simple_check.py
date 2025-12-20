#!/usr/bin/env python3
"""
Prueba simple para verificar el estado del módulo de Conciliación Bancaria
"""

import sys
import os

def check_database_connection():
    """Verifica la conexión a la base de datos"""
    try:
        from app.core.database import get_db
        from sqlalchemy.orm import Session
        
        # Obtener una sesión de base de datos
        db_gen = get_db()
        db = next(db_gen)
        
        # Intentar una consulta simple
        from sqlalchemy import text
        result = db.execute(text("SELECT 1")).fetchone()
        db.close()
        
        if result:
            print("✅ Conexión a base de datos: OK")
            return True
        else:
            print("❌ Conexión a base de datos: FALLO")
            return False
            
    except Exception as e:
        print(f"❌ Error de conexión a base de datos: {str(e)}")
        return False

def check_models():
    """Verifica que los modelos se puedan importar"""
    try:
        from app.models.conciliacion_bancaria import (
            ImportConfig, ImportSession, BankMovement, 
            Reconciliation, AccountingConfig
        )
        print("✅ Modelos de conciliación bancaria: OK")
        return True
    except Exception as e:
        print(f"❌ Error importando modelos: {str(e)}")
        return False

def check_services():
    """Verifica que los servicios se puedan importar"""
    try:
        from app.services.conciliacion_bancaria import (
            ImportEngine, MatchingEngine, AuditService, SecurityService
        )
        print("✅ Servicios de conciliación bancaria: OK")
        return True
    except Exception as e:
        print(f"❌ Error importando servicios: {str(e)}")
        return False

def check_schemas():
    """Verifica que los esquemas se puedan importar"""
    try:
        from app.schemas.conciliacion_bancaria import (
            FileValidationResult, ImportSessionCreate, BankMovementCreate
        )
        print("✅ Esquemas de validación: OK")
        return True
    except Exception as e:
        print(f"❌ Error importando esquemas: {str(e)}")
        return False

def check_api_routes():
    """Verifica que las rutas de API se puedan importar"""
    try:
        from app.api.conciliacion_bancaria import routes
        print("✅ Rutas de API: OK")
        return True
    except Exception as e:
        print(f"❌ Error importando rutas de API: {str(e)}")
        return False

def check_files():
    """Verifica que los archivos principales existan"""
    files_to_check = [
        "app/models/conciliacion_bancaria.py",
        "app/services/conciliacion_bancaria.py", 
        "app/api/conciliacion_bancaria/routes.py",
        "app/schemas/conciliacion_bancaria.py",
        "frontend/app/conciliacion-bancaria/page.js"
    ]
    
    all_exist = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path}: Existe")
        else:
            print(f"❌ {file_path}: NO EXISTE")
            all_exist = False
    
    return all_exist

def main():
    """Función principal"""
    print("="*60)
    print("  VERIFICACIÓN RÁPIDA - MÓDULO CONCILIACIÓN BANCARIA")
    print("="*60)
    
    checks = [
        ("Archivos principales", check_files),
        ("Modelos de base de datos", check_models),
        ("Servicios de backend", check_services),
        ("Esquemas de validación", check_schemas),
        ("Rutas de API", check_api_routes),
        ("Conexión a base de datos", check_database_connection)
    ]
    
    results = []
    
    for name, check_func in checks:
        print(f"\n🔍 Verificando: {name}")
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Error en {name}: {str(e)}")
            results.append(False)
    
    print("\n" + "="*60)
    print("  RESUMEN")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Verificaciones pasadas: {passed}/{total}")
    print(f"📊 Porcentaje de éxito: {(passed/total*100):.1f}%")
    
    if passed == total:
        print("\n🎉 ¡Excelente! Todos los componentes están funcionando correctamente.")
        print("   El módulo de Conciliación Bancaria está listo.")
    elif passed >= total * 0.8:
        print("\n⚠️  La mayoría de componentes funcionan, pero hay algunos problemas menores.")
    else:
        print("\n🚨 Hay problemas significativos que requieren atención.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    print(f"\n{'='*60}")
    sys.exit(0 if success else 1)