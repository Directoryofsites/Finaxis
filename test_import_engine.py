#!/usr/bin/env python3
"""
Script de prueba para el motor de importación de conciliación bancaria
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.services.conciliacion_bancaria import ImportEngine, ConfigurationManager
from app.models.conciliacion_bancaria import ImportConfig

def test_import_engine():
    """Prueba básica del motor de importación"""
    try:
        # Crear engine y sesión
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        print("✅ Conexión a base de datos establecida")
        
        # Crear instancia del motor de importación
        import_engine = ImportEngine(db)
        print("✅ ImportEngine creado exitosamente")
        
        # Crear instancia del gestor de configuración
        config_manager = ConfigurationManager(db)
        print("✅ ConfigurationManager creado exitosamente")
        
        # Probar consulta básica
        configs = db.query(ImportConfig).all()
        print(f"✅ Consulta de configuraciones exitosa. Encontradas: {len(configs)}")
        
        # Crear configuración de prueba
        test_config = ImportConfig(
            bank_id=1,  # Asumiendo que existe un tercero con ID 1
            empresa_id=1,  # Asumiendo que existe una empresa con ID 1
            name="Configuración de Prueba",
            file_format="CSV",
            delimiter=",",
            date_format="%Y-%m-%d",
            field_mapping={
                "date": 0,
                "amount": 1,
                "description": 2,
                "reference": 3
            },
            header_rows=1,
            created_by=1  # Asumiendo que existe un usuario con ID 1
        )
        
        # Validar configuración
        validation_result = config_manager.validate_config(test_config)
        if validation_result.is_valid:
            print("✅ Configuración de prueba válida")
        else:
            print(f"⚠️ Configuración de prueba inválida: {validation_result.errors}")
        
        print("\n🎉 Todas las pruebas básicas pasaron exitosamente!")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error en las pruebas: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Prueba del Motor de Importación - Conciliación Bancaria ===\n")
    success = test_import_engine()
    if success:
        print("\n✅ Todas las pruebas completadas exitosamente")
    else:
        print("\n❌ Algunas pruebas fallaron")
        sys.exit(1)