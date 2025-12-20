"""
Script de prueba para el sistema de gestión de configuraciones
Módulo de Conciliación Bancaria
"""

import sys
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.conciliacion_bancaria import ConfigurationManager
from app.models.conciliacion_bancaria import ImportConfig

def test_configuration_manager():
    """Prueba el ConfigurationManager"""
    print("=== Prueba del Sistema de Gestión de Configuraciones ===\n")
    
    db: Session = SessionLocal()
    
    try:
        # 1. Crear ConfigurationManager
        print("✓ Creando ConfigurationManager...")
        config_manager = ConfigurationManager(db)
        print("✅ ConfigurationManager creado exitosamente\n")
        
        # 2. Obtener configuraciones existentes
        print("✓ Consultando configuraciones existentes...")
        configs = config_manager.get_configurations(empresa_id=1)
        print(f"✅ Configuraciones encontradas: {len(configs)}\n")
        
        # 3. Crear una configuración de prueba
        print("✓ Creando configuración de prueba...")
        test_config_data = {
            'name': 'Banco Test - CSV',
            'bank_id': 1,  # Usar ID de banco en lugar de nombre
            'file_format': 'CSV',
            'delimiter': ',',
            'date_format': '%Y-%m-%d',
            'field_mapping': {
                'date': 0,
                'amount': 1,
                'description': 2,
                'reference': 3
            },
            'header_rows': 1
        }
        
        try:
            new_config = config_manager.create_configuration(
                test_config_data, 
                empresa_id=1, 
                user_id=1
            )
            print(f"✅ Configuración creada con ID: {new_config.id}\n")
            
            # 4. Validar configuración
            print("✓ Validando configuración...")
            validation_result = config_manager.validate_configuration(new_config)
            if validation_result['is_valid']:
                print("✅ Configuración válida\n")
            else:
                print(f"❌ Configuración inválida: {validation_result['errors']}\n")
            
            # 5. Actualizar configuración
            print("✓ Actualizando configuración...")
            update_data = {
                'name': 'Banco Test - CSV (Actualizado)'
            }
            updated_config = config_manager.update_configuration(
                new_config.id,
                update_data,
                empresa_id=1,
                user_id=1
            )
            print(f"✅ Configuración actualizada: {updated_config.name}\n")
            
            # 6. Duplicar configuración
            print("✓ Duplicando configuración...")
            duplicated_config = config_manager.duplicate_configuration(
                new_config.id,
                'Banco Test - CSV (Copia)',
                empresa_id=1,
                user_id=1
            )
            print(f"✅ Configuración duplicada con ID: {duplicated_config.id}\n")
            
            # 7. Buscar por banco
            print("✓ Buscando configuraciones por banco...")
            bank_configs = config_manager.get_configurations_by_bank(1, empresa_id=1)
            print(f"✅ Configuraciones encontradas para banco ID 1: {len(bank_configs)}\n")
            
            # 8. Eliminar configuraciones de prueba
            print("✓ Eliminando configuraciones de prueba...")
            config_manager.delete_configuration(new_config.id, empresa_id=1, user_id=1)
            config_manager.delete_configuration(duplicated_config.id, empresa_id=1, user_id=1)
            print("✅ Configuraciones eliminadas exitosamente\n")
            
        except ValueError as e:
            print(f"❌ Error de validación: {str(e)}\n")
            return False
        
        # 9. Probar validación con campos faltantes
        print("✓ Probando validación con campos faltantes...")
        invalid_config_data = {
            'name': 'Config Inválida',
            'bank_id': 1,
            'file_format': 'CSV',
            'delimiter': ',',
            'date_format': '%Y-%m-%d',
            'field_mapping': {
                'date': 0
                # Faltan 'amount' y 'description'
            },
            'header_rows': 1
        }
        
        try:
            invalid_config = config_manager.create_configuration(
                invalid_config_data,
                empresa_id=1,
                user_id=1
            )
            print("❌ ERROR: Debería haber rechazado la configuración inválida\n")
            return False
        except ValueError as e:
            print(f"✅ Validación correcta: {str(e)}\n")
        
        print("🎉 Todas las pruebas del ConfigurationManager pasaron exitosamente!\n")
        return True
        
    except Exception as e:
        print(f"❌ Error en las pruebas: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    try:
        success = test_configuration_manager()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error fatal: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
