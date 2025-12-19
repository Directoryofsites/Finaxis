#!/usr/bin/env python3
"""
Validación completa del sistema - Módulo de Conciliación Bancaria
Tarea 15: Final checkpoint - Complete system validation
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

class SystemValidator:
    """Validador completo del sistema de conciliación bancaria"""
    
    def __init__(self):
        self.validation_results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'unknown',
            'validations': {},
            'summary': {},
            'recommendations': []
        }
    
    def validate_file_structure(self) -> Dict[str, Any]:
        """Validar estructura de archivos del módulo"""
        
        required_files = {
            'models': 'app/models/conciliacion_bancaria.py',
            'services': 'app/services/conciliacion_bancaria.py',
            'api_routes': 'app/api/conciliacion_bancaria/routes.py',
            'schemas': 'app/schemas/conciliacion_bancaria.py',
            'frontend_page': 'frontend/app/conciliacion-bancaria/page.js',
            'cache_system': 'app/core/cache.py',
            'monitoring_system': 'app/core/monitoring.py',
            'file_processor': 'app/core/file_processor.py'
        }
        
        frontend_components = [
            'frontend/app/conciliacion-bancaria/components/ReconciliationDashboard.js',
            'frontend/app/conciliacion-bancaria/components/FileImportInterface.js',
            'frontend/app/conciliacion-bancaria/components/ManualReconciliationInterface.js',
            'frontend/app/conciliacion-bancaria/components/AutomaticAdjustments.js',
            'frontend/app/conciliacion-bancaria/components/ReconciliationReports.js',
            'frontend/app/conciliacion-bancaria/components/ImportConfigManager.js',
            'frontend/app/conciliacion-bancaria/components/AccountingConfiguration.js'
        ]
        
        results = {
            'core_files': {},
            'frontend_components': {},
            'missing_files': [],
            'status': 'success'
        }
        
        # Validar archivos principales
        for component, file_path in required_files.items():
            exists = os.path.exists(file_path)
            results['core_files'][component] = {
                'path': file_path,
                'exists': exists,
                'size_kb': round(os.path.getsize(file_path) / 1024, 2) if exists else 0
            }
            
            if not exists:
                results['missing_files'].append(file_path)
                results['status'] = 'error'
        
        # Validar componentes de frontend
        for component_path in frontend_components:
            exists = os.path.exists(component_path)
            component_name = os.path.basename(component_path)
            results['frontend_components'][component_name] = {
                'path': component_path,
                'exists': exists,
                'size_kb': round(os.path.getsize(component_path) / 1024, 2) if exists else 0
            }
            
            if not exists:
                results['missing_files'].append(component_path)
                results['status'] = 'warning'
        
        return results
    
    def validate_integration_points(self) -> Dict[str, Any]:
        """Validar puntos de integración con el sistema existente"""
        
        integration_checks = {
            'main_py_registration': {
                'file': 'app/main.py',
                'pattern': 'conciliacion_bancaria_router',
                'description': 'Módulo registrado en main.py'
            },
            'menu_integration': {
                'file': 'frontend/lib/menuData.js',
                'pattern': 'CONCILIACION_BANCARIA_MODULE',
                'description': 'Módulo integrado en menú principal'
            },
            'permissions_defined': {
                'file': 'seed_permissions.py',
                'pattern': 'conciliacion_bancaria:',
                'description': 'Permisos definidos en seeder'
            },
            'authentication_import': {
                'file': 'app/api/conciliacion_bancaria/routes.py',
                'pattern': 'has_permission',
                'description': 'Sistema de permisos integrado'
            }
        }
        
        results = {
            'integrations': {},
            'status': 'success'
        }
        
        for check_name, check_config in integration_checks.items():
            file_path = check_config['file']
            pattern = check_config['pattern']
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    pattern_found = pattern in content
                    
                    results['integrations'][check_name] = {
                        'description': check_config['description'],
                        'file': file_path,
                        'pattern': pattern,
                        'found': pattern_found,
                        'status': 'success' if pattern_found else 'error'
                    }
                    
                    if not pattern_found:
                        results['status'] = 'error'
            else:
                results['integrations'][check_name] = {
                    'description': check_config['description'],
                    'file': file_path,
                    'found': False,
                    'status': 'error',
                    'error': 'File not found'
                }
                results['status'] = 'error'
        
        return results
    
    def validate_api_endpoints(self) -> Dict[str, Any]:
        """Validar endpoints de API implementados"""
        
        expected_endpoints = {
            'configuration': [
                'POST /import-configs',
                'GET /import-configs',
                'PUT /import-configs/{id}',
                'DELETE /import-configs/{id}'
            ],
            'import': [
                'POST /import',
                'POST /import/{session_id}/confirm-duplicates',
                'GET /import-sessions'
            ],
            'reconciliation': [
                'POST /reconcile/auto',
                'POST /reconcile/manual',
                'POST /reconcile/reverse/{id}',
                'GET /reconciliations'
            ],
            'adjustments': [
                'GET /adjustments/preview/{id}',
                'POST /adjustments/apply',
                'GET /adjustments/detect/{id}'
            ],
            'reports': [
                'GET /reports/generate',
                'GET /reports/export'
            ],
            'monitoring': [
                'GET /monitoring/performance',
                'GET /monitoring/health',
                'GET /monitoring/cache-stats'
            ]
        }
        
        results = {
            'endpoint_categories': {},
            'total_endpoints': 0,
            'status': 'success'
        }
        
        routes_file = 'app/api/conciliacion_bancaria/routes.py'
        
        if os.path.exists(routes_file):
            with open(routes_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                for category, endpoints in expected_endpoints.items():
                    category_results = {
                        'expected': len(endpoints),
                        'found': 0,
                        'endpoints': {}
                    }
                    
                    for endpoint in endpoints:
                        method, path = endpoint.split(' ', 1)
                        # Buscar patrón del endpoint en el archivo
                        endpoint_pattern = f'@router.{method.lower()}("{path.replace("{id}", "{")}'
                        found = endpoint_pattern.replace('{', '').replace('}', '') in content.replace('{', '').replace('}', '')
                        
                        category_results['endpoints'][endpoint] = {
                            'found': found,
                            'pattern': endpoint_pattern
                        }
                        
                        if found:
                            category_results['found'] += 1
                    
                    results['endpoint_categories'][category] = category_results
                    results['total_endpoints'] += category_results['found']
        else:
            results['status'] = 'error'
            results['error'] = 'Routes file not found'
        
        return results
    
    def validate_database_models(self) -> Dict[str, Any]:
        """Validar modelos de base de datos"""
        
        expected_models = [
            'ImportConfig',
            'ImportSession', 
            'BankMovement',
            'Reconciliation',
            'ReconciliationMovement',
            'AccountingConfig',
            'ReconciliationAudit'
        ]
        
        results = {
            'models': {},
            'total_models': 0,
            'status': 'success'
        }
        
        models_file = 'app/models/conciliacion_bancaria.py'
        
        if os.path.exists(models_file):
            with open(models_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                for model_name in expected_models:
                    model_pattern = f'class {model_name}(Base):'
                    found = model_pattern in content
                    
                    results['models'][model_name] = {
                        'found': found,
                        'pattern': model_pattern
                    }
                    
                    if found:
                        results['total_models'] += 1
                    else:
                        results['status'] = 'warning'
        else:
            results['status'] = 'error'
            results['error'] = 'Models file not found'
        
        return results
    
    def validate_frontend_components(self) -> Dict[str, Any]:
        """Validar componentes de frontend"""
        
        main_page = 'frontend/app/conciliacion-bancaria/page.js'
        
        results = {
            'main_page': {},
            'component_imports': {},
            'status': 'success'
        }
        
        if os.path.exists(main_page):
            with open(main_page, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Verificar imports principales
                expected_imports = [
                    'ImportConfigManager',
                    'FileImportInterface',
                    'ManualReconciliationInterface',
                    'ReconciliationDashboard',
                    'ReconciliationReports',
                    'AutomaticAdjustments'
                ]
                
                for component in expected_imports:
                    import_found = f'import {component}' in content or f'from ./{component}' in content
                    usage_found = f'<{component}' in content
                    
                    results['component_imports'][component] = {
                        'imported': import_found,
                        'used': usage_found,
                        'status': 'success' if (import_found and usage_found) else 'warning'
                    }
                    
                    if not (import_found and usage_found):
                        results['status'] = 'warning'
                
                # Verificar estructura de tabs
                tabs_found = 'TabsContent' in content and 'TabsTrigger' in content
                results['main_page']['tabs_structure'] = tabs_found
                results['main_page']['file_size_kb'] = round(len(content) / 1024, 2)
        else:
            results['status'] = 'error'
            results['error'] = 'Main page file not found'
        
        return results
    
    def validate_performance_optimizations(self) -> Dict[str, Any]:
        """Validar optimizaciones de rendimiento implementadas"""
        
        optimization_files = {
            'cache_system': 'app/core/cache.py',
            'monitoring_system': 'app/core/monitoring.py',
            'file_processor': 'app/core/file_processor.py',
            'database_optimization': 'optimize_database.py'
        }
        
        results = {
            'optimization_files': {},
            'cache_integration': False,
            'monitoring_integration': False,
            'status': 'success'
        }
        
        # Verificar archivos de optimización
        for opt_name, file_path in optimization_files.items():
            exists = os.path.exists(file_path)
            results['optimization_files'][opt_name] = {
                'path': file_path,
                'exists': exists,
                'size_kb': round(os.path.getsize(file_path) / 1024, 2) if exists else 0
            }
            
            if not exists:
                results['status'] = 'warning'
        
        # Verificar integración de cache en servicios
        services_file = 'app/services/conciliacion_bancaria.py'
        if os.path.exists(services_file):
            with open(services_file, 'r', encoding='utf-8') as f:
                content = f.read()
                results['cache_integration'] = '@cached' in content
                results['monitoring_integration'] = '@monitor_performance' in content
        
        return results
    
    def validate_security_implementation(self) -> Dict[str, Any]:
        """Validar implementación de seguridad"""
        
        results = {
            'permission_usage': {},
            'authentication_integration': False,
            'multi_tenant_support': False,
            'status': 'success'
        }
        
        routes_file = 'app/api/conciliacion_bancaria/routes.py'
        
        if os.path.exists(routes_file):
            with open(routes_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Verificar uso de permisos
                permission_patterns = [
                    'conciliacion_bancaria:ver',
                    'conciliacion_bancaria:configurar',
                    'conciliacion_bancaria:importar',
                    'conciliacion_bancaria:conciliar',
                    'conciliacion_bancaria:ajustar',
                    'conciliacion_bancaria:reportes',
                    'conciliacion_bancaria:auditoria'
                ]
                
                for permission in permission_patterns:
                    found = permission in content
                    results['permission_usage'][permission] = found
                    
                    if not found:
                        results['status'] = 'warning'
                
                # Verificar integración de autenticación
                results['authentication_integration'] = 'has_permission' in content
                results['multi_tenant_support'] = 'current_user.empresa_id' in content
        
        return results
    
    def generate_final_report(self) -> Dict[str, Any]:
        """Generar reporte final de validación"""
        
        print("🔍 Iniciando validación completa del sistema...")
        print("="*70)
        
        # Ejecutar todas las validaciones
        validations = {
            'file_structure': self.validate_file_structure(),
            'integration_points': self.validate_integration_points(),
            'api_endpoints': self.validate_api_endpoints(),
            'database_models': self.validate_database_models(),
            'frontend_components': self.validate_frontend_components(),
            'performance_optimizations': self.validate_performance_optimizations(),
            'security_implementation': self.validate_security_implementation()
        }
        
        # Calcular estado general
        status_counts = {'success': 0, 'warning': 0, 'error': 0}
        
        for validation_name, validation_result in validations.items():
            status = validation_result.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
            
            print(f"\n📋 {validation_name.replace('_', ' ').title()}:")
            
            if status == 'success':
                print(f"   ✅ Estado: {status.upper()}")
            elif status == 'warning':
                print(f"   ⚠️  Estado: {status.upper()}")
            else:
                print(f"   ❌ Estado: {status.upper()}")
            
            # Mostrar detalles específicos
            if validation_name == 'file_structure':
                missing = len(validation_result.get('missing_files', []))
                total_core = len(validation_result.get('core_files', {}))
                total_frontend = len(validation_result.get('frontend_components', {}))
                print(f"   📁 Archivos principales: {total_core}")
                print(f"   🎨 Componentes frontend: {total_frontend}")
                if missing > 0:
                    print(f"   ⚠️  Archivos faltantes: {missing}")
            
            elif validation_name == 'api_endpoints':
                total = validation_result.get('total_endpoints', 0)
                print(f"   🌐 Endpoints implementados: {total}")
            
            elif validation_name == 'database_models':
                total = validation_result.get('total_models', 0)
                print(f"   🗄️  Modelos de BD: {total}")
        
        # Determinar estado general
        if status_counts['error'] > 0:
            overall_status = 'critical'
        elif status_counts['warning'] > 0:
            overall_status = 'warning'
        else:
            overall_status = 'success'
        
        # Generar recomendaciones
        recommendations = self._generate_recommendations(validations, overall_status)
        
        # Crear resumen
        summary = {
            'total_validations': len(validations),
            'successful_validations': status_counts['success'],
            'warnings': status_counts['warning'],
            'errors': status_counts['error'],
            'overall_status': overall_status,
            'completion_percentage': (status_counts['success'] / len(validations)) * 100
        }
        
        self.validation_results.update({
            'overall_status': overall_status,
            'validations': validations,
            'summary': summary,
            'recommendations': recommendations
        })
        
        return self.validation_results
    
    def _generate_recommendations(self, validations: Dict[str, Any], overall_status: str) -> List[str]:
        """Generar recomendaciones basadas en los resultados"""
        
        recommendations = []
        
        # Recomendaciones basadas en archivos faltantes
        file_validation = validations.get('file_structure', {})
        missing_files = file_validation.get('missing_files', [])
        
        if missing_files:
            recommendations.append(f"Verificar y crear {len(missing_files)} archivos faltantes")
        
        # Recomendaciones de integración
        integration_validation = validations.get('integration_points', {})
        if integration_validation.get('status') != 'success':
            recommendations.append("Completar puntos de integración pendientes")
        
        # Recomendaciones de seguridad
        security_validation = validations.get('security_implementation', {})
        if security_validation.get('status') != 'success':
            recommendations.append("Revisar implementación de permisos y seguridad")
        
        # Recomendaciones generales
        if overall_status == 'success':
            recommendations.extend([
                "✅ Sistema listo para producción",
                "Ejecutar pruebas finales en entorno de staging",
                "Preparar documentación de despliegue",
                "Configurar monitoreo en producción"
            ])
        elif overall_status == 'warning':
            recommendations.extend([
                "⚠️ Resolver advertencias antes de producción",
                "Completar componentes opcionales",
                "Verificar rendimiento con datos reales"
            ])
        else:
            recommendations.extend([
                "❌ Resolver errores críticos antes de continuar",
                "Revisar integración con sistema existente",
                "Completar archivos y configuraciones faltantes"
            ])
        
        return recommendations

def main():
    """Función principal de validación"""
    
    validator = SystemValidator()
    
    try:
        # Generar reporte completo
        report = validator.generate_final_report()
        
        # Mostrar resumen final
        print("\n" + "="*70)
        print("📊 RESUMEN FINAL DE VALIDACIÓN")
        print("="*70)
        
        summary = report['summary']
        overall_status = report['overall_status']
        
        print(f"🎯 Estado General: {overall_status.upper()}")
        print(f"📈 Porcentaje de Completitud: {summary['completion_percentage']:.1f}%")
        print(f"✅ Validaciones Exitosas: {summary['successful_validations']}/{summary['total_validations']}")
        
        if summary['warnings'] > 0:
            print(f"⚠️  Advertencias: {summary['warnings']}")
        
        if summary['errors'] > 0:
            print(f"❌ Errores: {summary['errors']}")
        
        # Mostrar recomendaciones
        print(f"\n💡 RECOMENDACIONES:")
        for i, recommendation in enumerate(report['recommendations'], 1):
            print(f"   {i}. {recommendation}")
        
        # Guardar reporte en archivo
        report_file = f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Reporte completo guardado en: {report_file}")
        
        # Determinar código de salida
        if overall_status == 'success':
            print("\n🎉 ¡VALIDACIÓN COMPLETADA EXITOSAMENTE!")
            print("   El módulo de Conciliación Bancaria está listo para producción.")
            return True
        elif overall_status == 'warning':
            print("\n⚠️  VALIDACIÓN COMPLETADA CON ADVERTENCIAS")
            print("   Revisar recomendaciones antes de desplegar a producción.")
            return True
        else:
            print("\n❌ VALIDACIÓN FALLÓ")
            print("   Resolver errores críticos antes de continuar.")
            return False
    
    except Exception as e:
        print(f"\n💥 ERROR DURANTE LA VALIDACIÓN: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)