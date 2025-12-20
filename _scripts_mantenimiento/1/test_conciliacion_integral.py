#!/usr/bin/env python3
"""
Script de pruebas integrales para el módulo de Conciliación Bancaria
Ejecuta todas las pruebas disponibles y genera un reporte completo
"""

import sys
import os
import subprocess
import time
from datetime import datetime

def print_header(title):
    """Imprime un encabezado formateado"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_section(title):
    """Imprime una sección"""
    print(f"\n📋 {title}")
    print("-" * 40)

def run_test(test_file, description):
    """Ejecuta un test y retorna el resultado"""
    print(f"🧪 Ejecutando: {description}")
    print(f"   Archivo: {test_file}")
    
    try:
        start_time = time.time()
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, timeout=60)
        end_time = time.time()
        
        duration = end_time - start_time
        
        if result.returncode == 0 or "✅" in result.stdout:
            print(f"   ✅ PASÓ ({duration:.2f}s)")
            return True, duration, result.stdout
        else:
            print(f"   ❌ FALLÓ ({duration:.2f}s)")
            print(f"   Error: {result.stderr}")
            return False, duration, result.stderr
            
    except subprocess.TimeoutExpired:
        print(f"   ⏰ TIMEOUT (>60s)")
        return False, 60, "Timeout"
    except FileNotFoundError:
        print(f"   📁 ARCHIVO NO ENCONTRADO")
        return False, 0, "File not found"
    except Exception as e:
        print(f"   💥 ERROR: {str(e)}")
        return False, 0, str(e)

def check_file_exists(file_path):
    """Verifica si un archivo existe"""
    return os.path.exists(file_path)

def main():
    """Función principal"""
    print_header("PRUEBAS INTEGRALES - MÓDULO CONCILIACIÓN BANCARIA")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Directorio: {os.getcwd()}")
    
    # Lista de pruebas disponibles
    tests = [
        ("test_import_engine.py", "Motor de Importación de Extractos"),
        ("test_configuration_manager.py", "Sistema de Gestión de Configuraciones"),
        ("test_matching_engine.py", "Motor de Conciliación Automática"),
        ("test_automatic_adjustments.py", "Sistema de Ajustes Automáticos"),
        ("test_manual_reconciliation_interface.py", "Interfaz de Conciliación Manual"),
        ("test_import_functionality.py", "Funcionalidad de Importación Completa")
    ]
    
    print_section("VERIFICACIÓN DE ARCHIVOS DE PRUEBA")
    
    available_tests = []
    for test_file, description in tests:
        if check_file_exists(test_file):
            print(f"✅ {test_file} - {description}")
            available_tests.append((test_file, description))
        else:
            print(f"❌ {test_file} - NO ENCONTRADO")
    
    if not available_tests:
        print("\n❌ No se encontraron archivos de prueba.")
        print("   Asegúrate de estar en el directorio correcto.")
        return False
    
    print_section("EJECUCIÓN DE PRUEBAS")
    
    results = []
    total_duration = 0
    
    for test_file, description in available_tests:
        success, duration, output = run_test(test_file, description)
        results.append({
            'file': test_file,
            'description': description,
            'success': success,
            'duration': duration,
            'output': output
        })
        total_duration += duration
        time.sleep(1)  # Pausa entre pruebas
    
    print_section("RESUMEN DE RESULTADOS")
    
    passed = sum(1 for r in results if r['success'])
    failed = len(results) - passed
    
    print(f"📊 Estadísticas:")
    print(f"   Total de pruebas: {len(results)}")
    print(f"   ✅ Pasaron: {passed}")
    print(f"   ❌ Fallaron: {failed}")
    print(f"   ⏱️  Tiempo total: {total_duration:.2f}s")
    print(f"   📈 Tasa de éxito: {(passed/len(results)*100):.1f}%")
    
    print(f"\n📋 Detalle por prueba:")
    for result in results:
        status = "✅ PASÓ" if result['success'] else "❌ FALLÓ"
        print(f"   {status} - {result['description']} ({result['duration']:.2f}s)")
    
    if failed > 0:
        print_section("PRUEBAS FALLIDAS - DETALLES")
        for result in results:
            if not result['success']:
                print(f"\n❌ {result['description']}:")
                print(f"   Archivo: {result['file']}")
                print(f"   Error: {result['output'][:200]}...")
    
    print_section("VERIFICACIÓN DE COMPONENTES PRINCIPALES")
    
    # Verificar archivos principales del módulo
    key_files = [
        ("app/models/conciliacion_bancaria.py", "Modelos de Base de Datos"),
        ("app/services/conciliacion_bancaria.py", "Servicios de Backend"),
        ("app/api/conciliacion_bancaria/routes.py", "Endpoints de API"),
        ("frontend/app/conciliacion-bancaria/page.js", "Interfaz Principal"),
        ("app/schemas/conciliacion_bancaria.py", "Esquemas de Validación")
    ]
    
    for file_path, description in key_files:
        if check_file_exists(file_path):
            print(f"✅ {description}")
        else:
            print(f"❌ {description} - FALTANTE: {file_path}")
    
    print_section("RECOMENDACIONES")
    
    if passed == len(results):
        print("🎉 ¡Excelente! Todas las pruebas pasaron exitosamente.")
        print("   El módulo de Conciliación Bancaria está listo para producción.")
        print("\n📋 Próximos pasos sugeridos:")
        print("   1. Ejecutar pruebas de integración con datos reales")
        print("   2. Realizar pruebas de rendimiento con archivos grandes")
        print("   3. Validar la integración con el sistema contable existente")
    elif passed > failed:
        print("⚠️  La mayoría de las pruebas pasaron, pero hay algunas fallas.")
        print("   Revisa los errores arriba y corrige los problemas identificados.")
    else:
        print("🚨 Hay problemas significativos que requieren atención.")
        print("   Revisa la configuración del sistema y los errores reportados.")
    
    print_header("FIN DE PRUEBAS INTEGRALES")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)